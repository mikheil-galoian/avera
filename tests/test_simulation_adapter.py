from __future__ import annotations

from pathlib import Path

from avera.adapters import adapt_simulation_csv


def test_adapt_simulation_csv_groups_metric_rows_into_one_test(tmp_path: Path) -> None:
    csv_path = tmp_path / "simulation.csv"
    csv_path.write_text(
        """test_id,component,status,metric,value,unit,scenario,evidence
ADAS-SIL-VRU-REGRESSION-03,ADAS Pedestrian Detection,failed,pedestrian_recall,0.903,ratio,ADAS-VRU-URBAN-CROSSING,recall below threshold
ADAS-SIL-VRU-REGRESSION-03,ADAS Pedestrian Detection,failed,brake_trigger_latency_ms,146.0,ms,ADAS-VRU-URBAN-CROSSING,latency above threshold
""",
        encoding="utf-8",
    )

    payload = adapt_simulation_csv(csv_path, run_id="adas-sim", stage="current")

    assert payload["runId"] == "adas-sim"
    assert payload["stage"] == "current"
    assert payload["metadata"]["adapter"] == "simulation_csv.v0"
    assert len(payload["tests"]) == 1
    test = payload["tests"][0]
    assert test["status"] == "failed"
    assert test["metrics"]["pedestrian_recall"] == 0.903
    assert test["metrics"]["brake_trigger_latency_ms"] == 146.0
    assert "recall below threshold" in test["evidence"]
    assert "latency above threshold" in test["evidence"]


def test_adapt_simulation_csv_requires_expected_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(
        """test_id,component,status,metric
ADAS-SIL-VRU-REGRESSION-03,ADAS Pedestrian Detection,failed,pedestrian_recall
""",
        encoding="utf-8",
    )

    try:
        adapt_simulation_csv(csv_path, run_id="adas-sim", stage="current")
    except ValueError as exc:
        assert "missing required columns" in str(exc)
    else:
        raise AssertionError("Expected simulation adapter to reject missing columns")
