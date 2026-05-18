"""Load simple signal trace CSV artifacts."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("timestamp_ms", "scenario_id", "test_id", "signal", "value", "unit")


@dataclass(frozen=True)
class SignalTracePoint:
    timestamp_ms: float
    scenario_id: str
    test_id: str
    signal: str
    value: float
    unit: str


def load_signal_trace(path: str | Path) -> list[SignalTracePoint]:
    """Load `signal_trace.csv` into ordered trace points."""

    trace_path = Path(path)
    with trace_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = [field for field in REQUIRED_FIELDS if field not in fields]
        if missing:
            raise ValueError(f"Signal trace missing fields {missing}: {trace_path}")
        return [_point(row, trace_path, index) for index, row in enumerate(reader, start=2)]


def summarize_signal_trace(
    points: Iterable[SignalTracePoint | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize trace values per `(test_id, signal)` pair.

    The `last` value is the last value observed in input order. `load_signal_trace`
    preserves CSV order, so callers can control "last" by ordering the source trace.
    """

    summaries: dict[tuple[str, str], dict[str, Any]] = {}
    for index, point in enumerate(points):
        source = f"signal_trace_point[{index}]"
        test_id = _text(_field(point, "test_id"), "test_id", source)
        signal = _text(_field(point, "signal"), "signal", source)
        value = _float(_field(point, "value"), "value", source)
        unit = _text(_field(point, "unit"), "unit", source)

        key = (test_id, signal)
        summary = summaries.get(key)
        if summary is None:
            summaries[key] = {
                "test_id": test_id,
                "signal": signal,
                "min": value,
                "max": value,
                "last": value,
                "unit": unit,
                "count": 1,
            }
            continue

        if summary["unit"] != unit:
            raise ValueError(
                f"Mixed units for signal summary {test_id}/{signal}: "
                f"{summary['unit']} != {unit}"
            )
        summary["min"] = min(summary["min"], value)
        summary["max"] = max(summary["max"], value)
        summary["last"] = value
        summary["count"] += 1

    return [summaries[key] for key in sorted(summaries)]


def _point(row: dict[str, Any], path: Path, row_number: int) -> SignalTracePoint:
    source = f"{path}:{row_number}"
    return SignalTracePoint(
        timestamp_ms=_float(row.get("timestamp_ms"), "timestamp_ms", source),
        scenario_id=_text(row.get("scenario_id"), "scenario_id", source),
        test_id=_text(row.get("test_id"), "test_id", source),
        signal=_text(row.get("signal"), "signal", source),
        value=_float(row.get("value"), "value", source),
        unit=_text(row.get("unit"), "unit", source),
    )


def _field(point: SignalTracePoint | Mapping[str, Any], field: str) -> Any:
    if isinstance(point, Mapping):
        return point.get(field)
    return getattr(point, field, None)


def _text(value: Any, field: str, source: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Missing {field}: {source}")
    return text


def _float(value: Any, field: str, source: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric {field}: {source}") from exc
