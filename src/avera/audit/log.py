"""Append-only, hash-chained audit log.

Design contract:
- Every record contains ``prev_hash`` — the digest of the preceding record.
- The first record's ``prev_hash`` is the digest of the empty string (genesis sentinel).
- Records are written to an append-only JSONL file; each line is one JSON object.
- ``verify_chain()`` walks every record and re-derives hashes — any inconsistent
  record or broken link raises ``ChainIntegrityError``.
- The log is thread-safe via a per-instance ``threading.Lock``.

Tamper-evidence is **keyed**. Without a secret key the chain uses plain
SHA-256, which only detects accidental edits or partial tampering: anyone who
can rewrite the file can forge a record and re-stitch every hash, and the chain
still verifies clean. It is *not* immutable against a privileged attacker. Pass
a key (argument or ``AVERA_AUDIT_KEY``) to switch the digest to HMAC-SHA256, so
records cannot be forged or the chain re-stitched without the secret. Use
``keyed`` / ``tamper_evidence`` to inspect which guarantee is in force, and the
``expected_count`` / ``expected_last_hash`` anchors of ``verify_chain`` to catch
truncation or rollback from an external record.

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
import hmac
import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:  # POSIX advisory locking for cross-process safety; degrades gracefully if absent.
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


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

    def __init__(self, path: str | Path, *, key: bytes | str | None = None) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        # Optional HMAC key for keyed tamper-evidence. Without a key the chain is
        # tamper-evident only against accidental edits / adjacent tampering (a
        # privileged attacker can re-stitch it). With a key held outside the file
        # (passed here or via AVERA_AUDIT_KEY), records cannot be forged or the
        # chain re-stitched without the secret.
        if key is None:
            env_key = os.environ.get("AVERA_AUDIT_KEY")
            key = env_key if env_key else None
        self._key: bytes | None = key.encode() if isinstance(key, str) else key
        self._warned_keyless = False

    @property
    def keyed(self) -> bool:
        """Whether the chain is protected by a secret HMAC key.

        ``False`` means plain SHA-256: tamper-evident only against accidental or
        partial edits, *not* against a privileged attacker who can re-stitch the
        whole file. See the module docstring.
        """
        return self._key is not None

    @property
    def tamper_evidence(self) -> str:
        """Human-readable guarantee level: ``keyed-hmac`` or ``change-detection-only``."""
        return "keyed-hmac" if self.keyed else "change-detection-only"

    def _digest(self, raw: str) -> str:
        """Keyed (HMAC-SHA256) digest when a key is set, else plain SHA-256."""
        if self._key:
            return hmac.new(self._key, raw.encode(), hashlib.sha256).hexdigest()
        return hashlib.sha256(raw.encode()).hexdigest()

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
            self._path.parent.mkdir(parents=True, exist_ok=True)
            # Hold a cross-process exclusive lock across read-prev + write so two
            # processes (or instances) cannot race the prev_hash/seq computation.
            with self._path.open("a+", encoding="utf-8") as fh:
                if fcntl is not None:
                    try:
                        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                    except OSError:
                        pass
                try:
                    fh.seek(0)
                    existing = [l for l in fh.read().splitlines() if l.strip()]
                    seq = len(existing)
                    prev_hash = _GENESIS_HASH
                    if existing:
                        prev_hash = str(json.loads(existing[-1]).get("self_hash", _GENESIS_HASH))

                    timestamp = datetime.now(timezone.utc).isoformat()
                    pre: dict[str, Any] = {
                        "seq": seq,
                        "timestamp_utc": timestamp,
                        "event": event,
                        "project": project,
                        "prev_hash": prev_hash,
                        "payload": payload,
                    }
                    self_hash = self._digest(_canonical(pre))
                    full: dict[str, Any] = {**pre, "self_hash": self_hash}
                    line = json.dumps(full, ensure_ascii=False, separators=(",", ":"))
                    fh.write(line + "\n")
                    fh.flush()
                finally:
                    if fcntl is not None:
                        try:
                            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                        except OSError:
                            pass

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

    def verify_chain(
        self,
        *,
        expected_count: int | None = None,
        expected_last_hash: str | None = None,
    ) -> int:
        """Verify the full hash chain.

        Parameters
        ----------
        expected_count, expected_last_hash:
            Optional external anchor. A plain hash chain cannot detect truncation
            on its own (a prefix is a valid chain). If a caller persists the record
            count and/or last ``self_hash`` in a separate trust store, pass them here
            and truncation/rollback is detected.

        Returns
        -------
        int
            Number of records verified.

        Raises
        ------
        ChainIntegrityError
            If any record's ``prev_hash`` does not match the preceding record's
            ``self_hash``, if a ``self_hash`` is inconsistent, or if the external
            anchor (count / last hash) does not match.
        """
        if not self.keyed and not self._warned_keyless:
            self._warned_keyless = True
            logger.warning(
                "Audit chain at %s is verified without a key: this detects accidental "
                "or partial edits only, not a deliberate re-stitch by someone who can "
                "rewrite the file. Set AVERA_AUDIT_KEY for forgery-resistant "
                "(HMAC) tamper-evidence.",
                self._path,
            )

        if not self._path.exists():
            if expected_count:
                raise ChainIntegrityError(
                    f"audit log missing but {expected_count} records expected (truncation)"
                )
            return 0

        lines = [l.strip() for l in self._path.read_text(encoding="utf-8").splitlines() if l.strip()]
        prev_self_hash: str = _GENESIS_HASH   # prev_hash expected by the first record

        for i, line in enumerate(lines):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ChainIntegrityError(f"Record {i}: JSON parse error — {exc}") from exc

            # 1. Verify self_hash (recompute from a FIXED schema, not whatever keys
            #    the line happens to contain — otherwise injected/renamed top-level
            #    fields could be smuggled in by recomputing self_hash over them).
            stored_self = obj.get("self_hash")
            pre = {
                "seq": obj.get("seq"),
                "timestamp_utc": obj.get("timestamp_utc"),
                "event": obj.get("event"),
                "project": obj.get("project"),
                "prev_hash": obj.get("prev_hash"),
                "payload": obj.get("payload"),
            }
            recomputed = self._digest(_canonical(pre))
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

        # External anchor checks (truncation / rollback) — opt-in.
        if expected_count is not None and len(lines) < expected_count:
            raise ChainIntegrityError(
                f"truncation: {len(lines)} records present, {expected_count} expected"
            )
        if expected_last_hash is not None:
            actual_last = prev_self_hash if lines else _GENESIS_HASH
            if actual_last != expected_last_hash:
                raise ChainIntegrityError(
                    f"head mismatch: last self_hash {str(actual_last)[:12]}… "
                    f"!= expected {str(expected_last_hash)[:12]}…"
                )

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
