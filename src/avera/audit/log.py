"""Immutable audit log with SHA-256 hash chaining.

Design contract:
- Every record contains ``prev_hash`` — the SHA-256 digest of the preceding record.
- The first record's ``prev_hash`` is the SHA-256 of the empty string (genesis sentinel).
- Records are written to an append-only JSONL file; each line is one JSON object.
- ``verify_chain()`` walks every record and re-derives hashes — any tampering or
  insertion breaks the chain and raises ``ChainIntegrityError``.
- The log is thread-safe via a per-instance ``threading.Lock``.

Usage::

    from pathlib import Path
    from avera.audit import AuditLog

    log = AuditLog(Path("avera-audit.jsonl"))
    log.append(event="analysis_started", project="bms-fast-charge", run_id="r-001")
    log.append(event="verdict_issued",   project="bms-fast-charge", run_id="r-001",
               verdict="confirmed_regression", risk="high")
    log.append(event="baseline_promoted", project="bms-fast-charge", promoted_by="eng@acme.com")

    records = log.read_all()
    log.verify_chain()          # raises ChainIntegrityError if tampered
    stats  = log.calibration_stats("bms-fast-charge")
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


# ---------------------------------------------------------------------------
# Sentinel hash — SHA-256("") — genesis prev_hash for the first record.
# ---------------------------------------------------------------------------
_GENESIS_HASH: str = hashlib.sha256(b"").hexdigest()


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ChainIntegrityError(RuntimeError):
    """Raised when ``verify_chain()`` detects a broken or tampered chain."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditRecord:
    """One immutable audit record as returned by ``read_all()``."""

    seq: int                        # 0-based position in the file
    timestamp_utc: str              # ISO-8601 UTC timestamp
    event: str                      # e.g. "analysis_started", "verdict_issued"
    project: str                    # project / fixture name
    prev_hash: str                  # SHA-256 of raw JSON of the previous line
    self_hash: str                  # SHA-256 of this record's own raw JSON (excl. self_hash)
    payload: dict[str, Any]         # arbitrary event-specific fields

    # Convenience accessors
    @property
    def run_id(self) -> str:
        return str(self.payload.get("run_id", ""))

    @property
    def verdict(self) -> str:
        return str(self.payload.get("verdict", ""))

    @property
    def risk(self) -> str:
        return str(self.payload.get("risk", ""))

    @property
    def human_confirmed(self) -> bool | None:
        v = self.payload.get("human_confirmed")
        return bool(v) if v is not None else None


# ---------------------------------------------------------------------------
# Core log class
# ---------------------------------------------------------------------------

class AuditLog:
    """Append-only, hash-chained audit log backed by a JSONL file.

    Parameters
    ----------
    path:
        Path to the ``.jsonl`` file.  Created on first append if absent.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def append(self, *, event: str, project: str, **payload: Any) -> AuditRecord:
        """Append one immutable record and return it.

        Parameters
        ----------
        event:
            Short label for the event type.
        project:
            Project / fixture name this event belongs to.
        **payload:
            Arbitrary additional fields stored in ``payload``.
        """
        with self._lock:
            prev_raw, prev_hash = self._last_raw_and_hash()
            seq = self._count_records()          # exact position before this write
            timestamp = datetime.now(timezone.utc).isoformat()

            # Build the «pre-hash» object — everything except self_hash.
            pre: dict[str, Any] = {
                "seq": seq,
                "timestamp_utc": timestamp,
                "event": event,
                "project": project,
                "prev_hash": prev_hash,
                "payload": payload,
            }
            pre_raw = _canonical(pre)
            self_hash = hashlib.sha256(pre_raw.encode()).hexdigest()

            full: dict[str, Any] = {**pre, "self_hash": self_hash}
            line = json.dumps(full, ensure_ascii=False, separators=(",", ":"))

            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

            return AuditRecord(
                seq=pre["seq"],
                timestamp_utc=timestamp,
                event=event,
                project=project,
                prev_hash=prev_hash,
                self_hash=self_hash,
                payload=dict(payload),
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read_all(self) -> list[AuditRecord]:
        """Return all records in append order (oldest first)."""
        return list(self._iter_records())

    def read_project(self, project: str) -> list[AuditRecord]:
        """Return all records for a specific project."""
        return [r for r in self._iter_records() if r.project == project]

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_chain(self) -> int:
        """Verify the full hash chain.

        Returns
        -------
        int
            Number of records verified.

        Raises
        ------
        ChainIntegrityError
            If any record's ``prev_hash`` does not match the hash of the
            preceding raw line, or if ``self_hash`` is inconsistent.
        """
        if not self._path.exists():
            return 0

        lines = [l.strip() for l in self._path.read_text(encoding="utf-8").splitlines() if l.strip()]
        prev_self_hash: str = _GENESIS_HASH   # prev_hash expected by the first record

        for i, line in enumerate(lines):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ChainIntegrityError(f"Record {i}: JSON parse error — {exc}") from exc

            # 1. Verify self_hash (recompute from pre-hash fields)
            stored_self = obj.pop("self_hash", None)
            recomputed = hashlib.sha256(_canonical(obj).encode()).hexdigest()
            if stored_self != recomputed:
                raise ChainIntegrityError(
                    f"Record {i} ({obj.get('event', '?')}): "
                    f"self_hash mismatch — stored {str(stored_self)[:12]}… "
                    f"recomputed {recomputed[:12]}…"
                )

            # 2. Verify prev_hash link (must equal self_hash of previous record)
            actual_prev = obj.get("prev_hash", "")
            if actual_prev != prev_self_hash:
                raise ChainIntegrityError(
                    f"Record {i} ({obj.get('event', '?')}): "
                    f"prev_hash mismatch — expected {prev_self_hash[:12]}… "
                    f"got {str(actual_prev)[:12]}…"
                )

            prev_self_hash = stored_self  # type: ignore[assignment]

        return len(lines)

    # ------------------------------------------------------------------
    # Calibration helpers
    # ------------------------------------------------------------------

    def calibration_stats(self, project: str | None = None) -> dict[str, Any]:
        """Return calibration statistics from ``human_confirmed`` feedback records.

        Returns a dict with::

            {
                "total_verdicts": int,
                "confirmed": int,       # human agreed with engine
                "overruled": int,       # human disagreed
                "accuracy": float,      # confirmed / (confirmed + overruled)
                "pending_feedback": int # verdicts without any feedback yet
            }
        """
        records = self.read_project(project) if project else self.read_all()

        verdicts: dict[str, str] = {}    # run_id → verdict
        feedback: dict[str, bool] = {}   # run_id → human_confirmed

        for r in records:
            if r.event == "verdict_issued" and r.run_id:
                verdicts[r.run_id] = r.verdict
            if r.event == "human_feedback" and r.run_id and r.human_confirmed is not None:
                feedback[r.run_id] = r.human_confirmed

        confirmed  = sum(1 for rid, ok in feedback.items() if ok)
        overruled  = sum(1 for rid, ok in feedback.items() if not ok)
        total_fb   = confirmed + overruled
        pending    = len([rid for rid in verdicts if rid not in feedback])

        return {
            "total_verdicts": len(verdicts),
            "confirmed": confirmed,
            "overruled": overruled,
            "accuracy": round(confirmed / total_fb, 4) if total_fb else None,
            "pending_feedback": pending,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_records(self) -> Iterator[AuditRecord]:
        if not self._path.exists():
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            yield AuditRecord(
                seq=int(obj.get("seq", 0)),
                timestamp_utc=str(obj.get("timestamp_utc", "")),
                event=str(obj.get("event", "")),
                project=str(obj.get("project", "")),
                prev_hash=str(obj.get("prev_hash", "")),
                self_hash=str(obj.get("self_hash", "")),
                payload=dict(obj.get("payload", {})),
            )

    def _last_raw_and_hash(self) -> tuple[str | None, str]:
        """Return (raw_last_line, prev_hash) for the next record to be appended."""
        if not self._path.exists():
            return None, _GENESIS_HASH
        lines = [l.strip() for l in self._path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not lines:
            return None, _GENESIS_HASH
        last = lines[-1]
        obj = json.loads(last)
        return last, str(obj.get("self_hash", hashlib.sha256(last.encode()).hexdigest()))

    @staticmethod
    def _current_length(prev_raw: str | None) -> int:
        """Cheap seq counter — not stored; re-derived on each append."""
        # We don't re-read the file; instead track via prev_raw presence.
        # Full seq is set during write by counting existing records once.
        return 0  # placeholder — overwritten in append()

    def _count_records(self) -> int:
        if not self._path.exists():
            return 0
        return sum(1 for l in self._path.read_text(encoding="utf-8").splitlines() if l.strip())


def _canonical(obj: dict[str, Any]) -> str:
    """Deterministic JSON serialisation for hashing (sorted keys, no spaces)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
