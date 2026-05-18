import csv
import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "bms-fast-charge"


def load_json(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_bms_fast_charge_fixture_files_exist() -> None:
    expected_files = {
        "requirements.csv",
        "component_map.json",
        "baseline_results.json",
        "current_results.json",
        "change_description.txt",
        "signal_trace.csv",
    }

    assert expected_files == {path.name for path in FIXTURE_DIR.iterdir() if path.is_file()}


def test_requirements_capture_temperature_and_cooling_limits() -> None:
    with (FIXTURE_DIR / "requirements.csv").open(encoding="utf-8", newline="") as requirements_file:
        requirements = {row["id"]: row for row in csv.DictReader(requirements_file)}

    assert requirements["BMS-REQ-112"] == {
        "id": "BMS-REQ-112",
        "component": "BMS Thermal Control",
        "requirement": "Maximum cell temperature during fast charging must not exceed 50 C",
        "metric": "max_cell_temp_c",
        "operator": "<=",
        "threshold": "50.0",
        "safety_level": "high",
        "next_checks": "BMS-HIL-FASTCHARGE-07",
    }
    assert requirements["BMS-REQ-118"]["metric"] == "cooling_response_ms"
    assert requirements["BMS-REQ-118"]["threshold"] == "500.0"


def test_component_map_connects_changed_file_to_requirements_and_test() -> None:
    component_map = load_json("component_map.json")

    thermal_manager = component_map["src/bms/thermal_manager.c"]

    assert thermal_manager["component"] == "BMS Thermal Control"
    assert thermal_manager["requirements"] == ["BMS-REQ-112", "BMS-REQ-118"]
    assert thermal_manager["tests"] == ["BMS-SIL-FASTCHARGE-01"]


def test_current_result_is_regression_against_baseline_thresholds() -> None:
    baseline = load_json("baseline_results.json")
    current = load_json("current_results.json")

    baseline_test = baseline["tests"][0]
    current_test = current["tests"][0]

    assert baseline["stage"] == "baseline"
    assert current["stage"] == "current"
    assert baseline_test["status"] == "passed"
    assert current_test["status"] == "failed"
    assert baseline_test["metrics"]["max_cell_temp_c"] == 47.1
    assert current_test["metrics"]["max_cell_temp_c"] == 52.8
    assert baseline_test["metrics"]["max_cell_temp_c"] <= 50.0
    assert current_test["metrics"]["max_cell_temp_c"] > 50.0
    assert current["changedFiles"] == ["src/bms/thermal_manager.c"]
