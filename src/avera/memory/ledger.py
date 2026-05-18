"""Append-only local memory ledger for AVERA runs."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "avera.memory_record.v0.1"


@dataclass(frozen=True)
class MemoryRecord:
    schema_version: str
    record_type: str
    timestamp_utc: str
    project_path: str | None = None
    report_path: str | None = None
    evidence_graph_path: str | None = None
    output_dir: str | None = None
    verdict: str | None = None
    risk: str | None = None
    confidence: str | None = None
    confidence_score: float | None = None
    gate_status: str | None = None
    gate_exit_code: int | None = None
    affected_components: list[str] = field(default_factory=list)
    affected_requirements: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


def append_analysis_record(
    memory_path: str | Path,
    *,
    project: str | Path,
    out: str | Path,
    report_path: str | Path,
    graph_path: str | Path,
    report: dict[str, Any],
) -> MemoryRecord:
    """Append an analysis result to local engineering memory."""

    record = MemoryRecord(
        schema_version=SCHEMA_VERSION,
        record_type="analysis",
        timestamp_utc=_now(),
        project_path=str(project),
        output_dir=str(out),
        report_path=str(report_path),
        evidence_graph_path=str(graph_path),
        verdict=_text(report.get("verdict")),
        risk=_text(report.get("risk")),
        confidence=_text(report.get("confidence")),
        confidence_score=_number(report.get("confidence_score")),
        affected_components=_string_list(report.get("affected_components")),
        affected_requirements=_requirement_ids(report.get("affected_requirements")),
        summary=dict(report.get("comparison_summary") or {}),
    )
    _append_record(Path(memory_path), record)
    return record


def append_gate_record(
    memory_path: str | Path,
    *,
    report_path: str | Path,
    decision: Any,
) -> MemoryRecord:
    """Append a gate decision to local engineering memory."""

    summary = dict(getattr(decision, "report_summary", {}) or {})
    record = MemoryRecord(
        schema_version=SCHEMA_VERSION,
        record_type="gate",
        timestamp_utc=_now(),
        report_path=str(report_path),
        verdict=_text(summary.get("verdict")),
        risk=_text(summary.get("risk")),
        confidence=_text(summary.get("confidence")),
        confidence_score=_number(summary.get("confidence_score")),
        gate_status=_text(getattr(decision, "status", None)),
        gate_exit_code=getattr(decision, "exit_code", None),
        reasons=_string_list(getattr(decision, "reasons", [])),
        summary=summary,
    )
    _append_record(Path(memory_path), record)
    return record


def load_memory_records(memory_path: str | Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    """Load local memory records from newest to oldest."""

    path = Path(memory_path)
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)

    records.reverse()
    return records[:limit] if limit is not None else records


def summarize_memory(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return compact counters for memory records."""

    by_type = Counter(str(item.get("record_type") or "unknown") for item in records)
    by_verdict = Counter(str(item.get("verdict") or "unknown") for item in records)
    by_risk = Counter(str(item.get("risk") or "unknown") for item in records)
    by_gate = Counter(str(item.get("gate_status") or "none") for item in records)
    return {
        "total_records": len(records),
        "by_type": dict(sorted(by_type.items())),
        "by_verdict": dict(sorted(by_verdict.items())),
        "by_risk": dict(sorted(by_risk.items())),
        "by_gate_status": dict(sorted(by_gate.items())),
    }


def _append_record(path: Path, record: MemoryRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    else:
        values = value if isinstance(value, list | tuple | set) else [value]
    return sorted({str(item).strip() for item in values if str(item).strip()})


def _requirement_ids(value: Any) -> list[str]:
    ids: list[str] = []
    for item in value or []:
        if isinstance(item, dict):
            req_id = item.get("id")
        else:
            req_id = item
        if req_id:
            ids.append(str(req_id).strip())
    return sorted({item for item in ids if item})
