"""Adapt simple simulation-result CSV artifacts into AVERA verification results."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = ("test_id", "component", "status", "metric", "value")


def adapt_simulation_csv(
    path: str | Path,
    *,
    run_id: str,
    stage: str,
) -> dict[str, Any]:
    """Convert a simulation-results CSV into an AVERA verification-run JSON."""

    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_COLUMNS if column not in fields]
        if missing:
            raise ValueError(
                f"Simulation CSV missing required columns: {', '.join(missing)}"
            )

        tests: dict[str, dict[str, Any]] = {}
        row_count = 0
        for row in reader:
            row_count += 1
            _merge_row(tests, row, row_count)

    return {
        "runId": run_id,
        "stage": stage,
        "tests": list(tests.values()),
        "metadata": {
            "adapter": "simulation_csv.v0",
            "source_format": "simulation_csv",
            "source_path": str(source),
            "row_count": row_count,
            "test_count": len(tests),
        },
    }


def _merge_row(tests: dict[str, dict[str, Any]], row: dict[str, str], row_number: int) -> None:
    test_id = (row.get("test_id") or "").strip()
    component = (row.get("component") or "").strip()
    status = (row.get("status") or "").strip()
    metric = (row.get("metric") or "").strip()
    raw_value = (row.get("value") or "").strip()

    if not test_id:
        raise ValueError(f"Simulation CSV row {row_number} missing test_id")
    if not component:
        raise ValueError(f"Simulation CSV row {row_number} missing component")
    if not status:
        raise ValueError(f"Simulation CSV row {row_number} missing status")
    if not metric:
        raise ValueError(f"Simulation CSV row {row_number} missing metric")

    entry = tests.setdefault(
        test_id,
        {
            "id": test_id,
            "component": component,
            "status": status,
            "metrics": {},
            "evidence": "",
            "metadata": {
                "adapter": "simulation_csv.v0",
                "source_rows": [],
            },
        },
    )

    if entry["component"] != component:
        raise ValueError(
            f"Simulation CSV row {row_number} changes component for {test_id}: "
            f"{entry['component']} -> {component}"
        )
    if entry["status"] != status:
        entry["status"] = _combine_status(str(entry["status"]), status)

    entry["metrics"][metric] = _coerce_value(raw_value)

    evidence = (row.get("evidence") or "").strip()
    if evidence:
        if entry["evidence"]:
            entry["evidence"] = f"{entry['evidence']}\n{evidence}"
        else:
            entry["evidence"] = evidence

    unit = (row.get("unit") or "").strip()
    scenario = (row.get("scenario") or "").strip()
    metadata = entry["metadata"]
    if unit:
        metadata.setdefault("metric_units", {})[metric] = unit
    if scenario:
        metadata.setdefault("scenarios", []).append(scenario)
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
class SimulationCsvAdapter(_VA):
    """VerificationAdapter wrapper for :func:`adapt_simulation_csv`."""

    name = "simulation_csv"
    version = "1.0.0"
    source_format = "simulation_csv"
    file_extensions = (".csv",)

    def adapt(self, path: Path, *, run_id: str, stage: str) -> dict:
        return adapt_simulation_csv(path, run_id=run_id, stage=stage)

    def can_handle(self, path: Path) -> bool:
        if path.suffix.lower() != ".csv":
            return False
        try:
            header = path.read_text(encoding="utf-8-sig", errors="replace").split("\n")[0]
            return "test_id" in header and "metric" in header and "value" in header
        except OSError:
            return False

    @property
    def metadata(self) -> dict:
        return {"adapter": "simulation_csv.1_0_0", "adapter_name": "simulation_csv",
                "adapter_version": "1.0.0", "source_format": "simulation_csv"}

    def __repr__(self) -> str:
        return "SimulationCsvAdapter(name='simulation_csv', version='1.0.0')"
