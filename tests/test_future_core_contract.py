from pathlib import Path

import pytest


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bms-fast-charge"


def test_future_analyzer_reports_high_confidence_bms_regression() -> None:
    avera_core = pytest.importorskip("avera.core", reason="AVERA core is not implemented yet")

    report = avera_core.analyze(
        baseline_path=FIXTURE_DIR / "baseline_results.json",
        current_path=FIXTURE_DIR / "current_results.json",
        requirements_path=FIXTURE_DIR / "requirements.csv",
        component_map_path=FIXTURE_DIR / "component_map.json",
        change_description_path=FIXTURE_DIR / "change_description.txt",
    )

    assert report["verdict"] == "confirmed_regression"
    assert report["risk"] == "high"
    assert report["confidence"] == "high"
    assert report["affected_component"] == "BMS Thermal Control"
    assert report["affected_requirements"] == ["BMS-REQ-112", "BMS-REQ-118"]
    assert report["changed_files"] == ["src/bms/thermal_manager.c"]
    assert report["recommendations"] == ["BMS-HIL-FASTCHARGE-07"]
    assert report["evidence"]["max_cell_temp_c"] == {
        "baseline": 47.1,
        "current": 52.8,
        "operator": "<=",
        "threshold": 50.0,
    }
