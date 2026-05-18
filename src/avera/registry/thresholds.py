"""Governed safety threshold registry.

Separates threshold governance from test fixture data.  Every threshold
entry is versioned, owner-attributed, and carries a ``valid_from`` date so
auditors can answer "what threshold was in force on date X for requirement Y?"

Design contract:
- Thresholds are immutable once registered; changing a threshold requires a
  new entry with a newer ``valid_from`` date — the old entry is preserved.
- The registry is persisted as a single JSON file and is safe to commit to VCS.
- ``resolve()`` returns the entry that was active on a given ISO-8601 date.
- ``verify_no_gaps()`` ensures every requirement in a CSV set has a threshold.

Usage::

    from avera.registry import ThresholdRegistry, ThresholdEntry

    reg = ThresholdRegistry.load(Path("threshold-registry.json"))

    reg.register(
        ThresholdEntry(
            req_id="BMS-REQ-001",
            metric="max_cell_temp_c",
            operator="<=",
            value=75.0,
            safety_level="asil-d",
            source_standard="ISO 26262",
            owner="thermal-team@acme.com",
            valid_from="2026-01-01",
            rationale="HW limit from cell datasheet rev 4.",
        )
    )
    reg.save(Path("threshold-registry.json"))

    entry = reg.resolve("BMS-REQ-001", on_date="2026-05-17")
    print(entry.value)   # 75.0
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ThresholdConflictError(ValueError):
    """Raised when a duplicate or conflicting threshold entry is registered."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ThresholdEntry:
    """One versioned safety threshold record.

    Attributes
    ----------
    req_id:
        Requirement identifier (e.g. "BMS-REQ-001").
    metric:
        Measurable quantity name (e.g. "max_cell_temp_c").
    operator:
        Comparison operator: ``"<="`` | ``">="`` | ``"<"`` | ``">"`` | ``"=="``
    value:
        Numeric threshold value.
    safety_level:
        Safety integrity label (e.g. "asil-d", "dal-a", "sil4", "class-c").
    source_standard:
        Governing standard (e.g. "ISO 26262", "DO-178C", "EN-50128", "IEC-62304").
    owner:
        Team or person responsible for this threshold.
    valid_from:
        ISO-8601 date string from which this entry is in force ("YYYY-MM-DD").
    rationale:
        Free-text justification for the threshold value.
    """

    req_id: str
    metric: str
    operator: str
    value: float
    safety_level: str
    source_standard: str
    owner: str
    valid_from: str          # "YYYY-MM-DD"
    rationale: str = ""

    def is_violated_by(self, measured: float) -> bool:
        """Return True if ``measured`` violates this threshold."""
        ops = {
            "<=": measured <= self.value,
            ">=": measured >= self.value,
            "<":  measured <  self.value,
            ">":  measured >  self.value,
            "==": measured == self.value,
        }
        # Threshold is the allowed ceiling/floor — violation means the measured
        # value does NOT satisfy the requirement.
        return not ops.get(self.operator, True)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ThresholdEntry":
        return cls(
            req_id=str(d["req_id"]),
            metric=str(d["metric"]),
            operator=str(d["operator"]),
            value=float(d["value"]),
            safety_level=str(d["safety_level"]),
            source_standard=str(d["source_standard"]),
            owner=str(d["owner"]),
            valid_from=str(d["valid_from"]),
            rationale=str(d.get("rationale", "")),
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ThresholdRegistry:
    """Versioned, append-only registry of safety thresholds.

    Parameters
    ----------
    entries:
        Initial list of entries.  Usually constructed via :meth:`load`.
    """

    _SCHEMA = "avera.threshold_registry.v1.0"

    def __init__(self, entries: list[ThresholdEntry] | None = None) -> None:
        self._entries: list[ThresholdEntry] = list(entries or [])

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> "ThresholdRegistry":
        """Load registry from a JSON file.  Returns empty registry if absent."""
        p = Path(path)
        if not p.exists():
            return cls()
        raw = json.loads(p.read_text(encoding="utf-8"))
        entries = [ThresholdEntry.from_dict(e) for e in raw.get("entries", [])]
        return cls(entries)

    def save(self, path: str | Path) -> None:
        """Persist registry to a JSON file (atomic write via temp → rename)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self._SCHEMA,
            "entry_count": len(self._entries),
            "entries": [e.to_dict() for e in self._entries],
        }
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def register(self, entry: ThresholdEntry) -> None:
        """Add a new threshold entry.

        Raises
        ------
        ThresholdConflictError
            If an entry with the same ``req_id`` and ``valid_from`` already exists.
        """
        for existing in self._entries:
            if existing.req_id == entry.req_id and existing.valid_from == entry.valid_from:
                raise ThresholdConflictError(
                    f"Threshold for req_id={entry.req_id!r} with "
                    f"valid_from={entry.valid_from!r} already registered."
                )
        self._entries.append(entry)

    def register_many(self, entries: list[ThresholdEntry]) -> None:
        """Register multiple entries, stopping on the first conflict."""
        for e in entries:
            self.register(e)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def resolve(self, req_id: str, on_date: str | None = None) -> ThresholdEntry | None:
        """Return the active threshold for ``req_id`` on ``on_date``.

        If ``on_date`` is None the most recent entry is returned.
        Returns None if no entry exists for this req_id.
        """
        candidates = [e for e in self._entries if e.req_id == req_id]
        if not candidates:
            return None
        if on_date is None:
            return max(candidates, key=lambda e: e.valid_from)
        active = [e for e in candidates if e.valid_from <= on_date]
        if not active:
            return None
        return max(active, key=lambda e: e.valid_from)

    def history(self, req_id: str) -> list[ThresholdEntry]:
        """Return all historical entries for a requirement, oldest first."""
        return sorted(
            [e for e in self._entries if e.req_id == req_id],
            key=lambda e: e.valid_from,
        )

    def all_req_ids(self) -> list[str]:
        """Return sorted unique requirement IDs in this registry."""
        return sorted({e.req_id for e in self._entries})

    def entries_by_standard(self, standard: str) -> list[ThresholdEntry]:
        """Filter entries by source_standard (case-insensitive substring match)."""
        std = standard.lower()
        return [e for e in self._entries if std in e.source_standard.lower()]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def verify_no_gaps(self, req_ids: list[str], on_date: str | None = None) -> list[str]:
        """Return req_ids that have NO active threshold on ``on_date``.

        Useful to surface uncovered requirements before analysis.
        """
        return [rid for rid in req_ids if self.resolve(rid, on_date) is None]

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"ThresholdRegistry(entries={len(self._entries)})"
