import csv
import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
FIXTURE_DIR = FIXTURES_DIR / "bms-mixed-results"

EXPECTED_OUTCOME = {
    "verdict": "confirmed_regression",
    "risk": "high",
    "confidence": "high",
}


def load_json(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_bms_mixed_results_fixture_files_exist() -> None:
    expected_files = {
        "requirements.csv",
        "component_map.json",
        "baseline_results.json",
        "current_results.json",
        "change_description.txt",
    }

    assert expected_files == {path.name for path in FIXTURE_DIR.iterdir() if path.is_file()}


def test_expected_outcomes_registers_mixed_results_as_confirmed_regression() -> None:
    expected_outcomes = json.loads((FIXTURES_DIR / "expected_outcomes.json").read_text(encoding="utf-8"))

    assert expected_outcomes["bms-mixed-results"] == EXPECTED_OUTCOME


def test_requirements_cover_regression_preexisting_failure_and_unchanged_pass() -> None:
    with (FIXTURE_DIR / "requirements.csv").open(encoding="utf-8", newline="") as requirements_file:
        requirements = {row["id"]: row for row in csv.DictReader(requirements_file)}

    assert requirements["BMS-REQ-112"]["safety_level"] == "high"
    assert requirements["BMS-REQ-205"]["metric"] == "cell_delta_mv"
    assert requirements["BMS-REQ-301"]["metric"] == "contactor_close_ms"


def test_component_map_limits_changed_file_to_introduced_regression_test() -> None:
    component_map = load_json("component_map.json")

    changed_mapping = component_map["src/bms/thermal_manager.c"]

    assert changed_mapping["requirements"] == ["BMS-REQ-112", "BMS-REQ-118"]
    assert changed_mapping["tests"] == ["BMS-SIL-FASTCHARGE-01"]


def test_mixed_results_include_introduced_preexisting_and_unchanged_outcomes() -> None:
    baseline = load_json("baseline_results.json")
    current = load_json("current_results.json")

    baseline_by_id = {test["id"]: test for test in baseline["tests"]}
    current_by_id = {test["id"]: test for test in current["tests"]}

    introduced = "BMS-SIL-FASTCHARGE-01"
    preexisting = "BMS-SIL-BALANCE-02"
    unchanged_pass = "BMS-SIL-CONTACTOR-01"

    assert current["changedFiles"] == ["src/bms/thermal_manager.c"]

    assert baseline_by_id[introduced]["status"] == "passed"
    assert current_by_id[introduced]["status"] == "failed"
    assert baseline_by_id[introduced]["metrics"]["max_cell_temp_c"] <= 50.0
    assert current_by_id[introduced]["metrics"]["max_cell_temp_c"] > 50.0

    assert baseline_by_id[preexisting]["status"] == "failed"
    assert current_by_id[preexisting]["status"] == "failed"
    assert baseline_by_id[preexisting]["metrics"]["cell_delta_mv"] > 35.0
    assert current_by_id[preexisting]["metrics"]["cell_delta_mv"] > 35.0

    assert baseline_by_id[unchanged_pass]["status"] == "passed"
    assert current_by_id[unchanged_pass]["status"] == "passed"
    assert baseline_by_id[unchanged_pass]["metrics"]["contactor_close_ms"] <= 120.0
    assert current_by_id[unchanged_pass]["metrics"]["contactor_close_ms"] <= 120.0


def test_future_analyzer_reports_expected_mixed_results_outcome() -> None:
    avera_core = pytest.importorskip("avera.core", reason="AVERA core is not implemented yet")

    report = avera_core.analyze(
        baseline_path=FIXTURE_DIR / "baseline_results.json",
        current_path=FIXTURE_DIR / "current_results.json",
        requirements_path=FIXTURE_DIR / "requirements.csv",
        component_map_path=FIXTURE_DIR / "component_map.json",
        change_description_path=FIXTURE_DIR / "change_description.txt",
    )

    assert report["verdict"] == EXPECTED_OUTCOME["verdict"]
    assert report["risk"] == EXPECTED_OUTCOME["risk"]
    assert report["confidence"] == EXPECTED_OUTCOME["confidence"]
