"""Adapt richer verification log CSV artifacts into AVERA verification results."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = ("test_id", "component", "status", "message")


def adapt_log_csv(
    path: str | Path,
    *,
    run_id: str,
    stage: str,
) -> dict[str, Any]:
    """Convert a richer verification log CSV into an AVERA verification-run JSON."""

    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fields]
        if missing:
            raise ValueError(f"Verification log CSV missing required columns: {', '.join(missing)}")

        tests: dict[str, dict[str, Any]] = {}
        row_count = 0
        for row in reader:
            row_count += 1
            _merge_row(tests, row, row_count)

    if not tests:
        raise ValueError(f"Verification log CSV has no rows: {source}")

    return {
        "runId": run_id,
        "stage": stage,
        "tests": list(tests.values()),
        "metadata": {
            "adapter": "log_csv.v0",
            "source_format": "verification_log_csv",
            "source_path": str(source),
            "row_count": row_count,
            "test_count": len(tests),
        },
    }


def _merge_row(tests: dict[str, dict[str, Any]], row: dict[str, str], row_number: int) -> None:
    test_id = (row.get("test_id") or "").strip()
    component = (row.get("component") or "").strip()
    status = (row.get("status") or "").strip()
    message = (row.get("message") or "").strip()

    if not test_id:
        raise ValueError(f"Verification log CSV row {row_number} missing test_id")
    if not component:
        raise ValueError(f"Verification log CSV row {row_number} missing component")
    if not status:
        raise ValueError(f"Verification log CSV row {row_number} missing status")
    if not message:
        raise ValueError(f"Verification log CSV row {row_number} missing message")

    entry = tests.setdefault(
        test_id,
        {
            "id": test_id,
            "component": component,
            "status": status,
            "metrics": {},
            "evidence": "",
            "metadata": {
                "adapter": "log_csv.v0",
                "source_rows": [],
            },
        },
    )

    if entry["component"] != component:
        raise ValueError(
            f"Verification log CSV row {row_number} changes component for {test_id}: "
            f"{entry['component']} -> {component}"
        )
    if entry["status"] != status:
        entry["status"] = _combine_status(str(entry["status"]), status)

    metric = (row.get("metric") or "").strip()
    value = (row.get("value") or "").strip()
    if metric and value:
        entry["metrics"][metric] = _coerce_value(value)

    if entry["evidence"]:
        entry["evidence"] = f"{entry['evidence']}\n{message}"
    else:
        entry["evidence"] = message

    metadata = entry["metadata"]
    timestamp = (row.get("timestamp_utc") or "").strip()
    environment = (row.get("environment") or "").strip()
    unit = (row.get("unit") or "").strip()
    if timestamp:
        metadata.setdefault("timestamps_utc", []).append(timestamp)
    if environment:
        metadata.setdefault("environments", []).append(environment)
    if unit and metric:
        metadata.setdefault("metric_units", {})[metric] = unit
    metadata["source_rows"].append(row_number)


def _coerce_value(raw_value: str) -> Any:
    lowered = raw_value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if any(char in raw_value for char in (".", "e", "E")):
            return float(raw_value)
        return int(raw_value)
    except ValueError:
        return raw_value


def _combine_status(existing: str, incoming: str) -> str:
    order = {
        "error": 4,
        "failed": 3,
        "inconclusive": 2,
        "skipped": 1,
        "passed": 0,
    }
    current = order.get(existing, 0)
    candidate = order.get(incoming, 0)
    return existing if current >= candidate else incoming


# ---------------------------------------------------------------------------
# SDK-compatible class wrapper
# ---------------------------------------------------------------------------

from avera.adapters.interface import VerificationAdapter as _VA
class LogCsvAdapter(_VA):
    """VerificationAdapter wrapper for :func:`adapt_log_csv`."""

    name = "log_csv"
    version = "1.0.0"
    source_format = "verification_log_csv"
    file_extensions = (".csv",)

    def adapt(self, path: Path, *, run_id: str, stage: str) -> dict:
        return adapt_log_csv(path, run_id=run_id, stage=stage)

    def can_handle(self, path: Path) -> bool:
        if path.suffix.lower() != ".csv":
            return False
        try:
            header = path.read_text(encoding="utf-8-sig", errors="replace").split("\n")[0]
            return "test_id" in header and "message" in header
        except OSError:
            return False

    @property
    def metadata(self) -> dict:
        return {"adapter": "log_csv.1_0_0", "adapter_name": "log_csv",
                "adapter_version": "1.0.0", "source_format": "verification_log_csv"}

    def __repr__(self) -> str:
        return "LogCsvAdapter(name='log_csv', version='1.0.0')"
