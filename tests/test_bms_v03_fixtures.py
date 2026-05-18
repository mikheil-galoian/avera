import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"

SCENARIOS = {
    "bms-worsened-preexisting": {
        "verdict": "worsened_preexisting_failure",
        "risk": "high",
        "confidence": "high",
    },
    "bms-environment-failure": {
        "verdict": "environment_failure",
        "risk": "unknown",
        "confidence": "low",
    },
    "bms-coverage-gap": {
        "verdict": "requirements_coverage_gap",
        "risk": "medium",
        "confidence": "low",
    },
}

EXPECTED_FILES = {
    "requirements.csv",
    "component_map.json",
    "baseline_results.json",
    "current_results.json",
    "change_description.txt",
}


def load_json(scenario: str, name: str) -> dict:
    return json.loads((FIXTURES_DIR / scenario / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_v03_fixture_files_exist(scenario: str) -> None:
    fixture_dir = FIXTURES_DIR / scenario

    assert fixture_dir.is_dir()
    assert EXPECTED_FILES == {path.name for path in fixture_dir.iterdir() if path.is_file()}


def test_worsened_preexisting_fixture_gets_materially_worse() -> None:
    baseline = load_json("bms-worsened-preexisting", "baseline_results.json")
    current = load_json("bms-worsened-preexisting", "current_results.json")

    baseline_test = baseline["tests"][0]
    current_test = current["tests"][0]

    assert baseline_test["status"] == "failed"
    assert current_test["status"] == "failed"
    assert baseline_test["metrics"]["max_cell_temp_c"] > 50.0
    assert current_test["metrics"]["max_cell_temp_c"] > baseline_test["metrics"]["max_cell_temp_c"]
    assert current_test["metrics"]["cooling_response_ms"] > baseline_test["metrics"]["cooling_response_ms"]


def test_environment_failure_fixture_has_no_current_requirement_metrics() -> None:
    baseline = load_json("bms-environment-failure", "baseline_results.json")
    current = load_json("bms-environment-failure", "current_results.json")

    assert baseline["tests"][0]["status"] == "passed"
    assert current["environment"]["status"] == "failed"
    assert current["environment"]["failureType"] == "hil_bench_unavailable"
    assert current["tests"][0]["status"] == "error"
    assert current["tests"][0]["metrics"] == {}


def test_coverage_gap_fixture_changed_requirement_is_not_executed() -> None:
    component_map = load_json("bms-coverage-gap", "component_map.json")
    baseline = load_json("bms-coverage-gap", "baseline_results.json")
    current = load_json("bms-coverage-gap", "current_results.json")

    mapped_tests = set(component_map["src/bms/soc_estimator.c"]["tests"])
    executed_tests = {test["id"] for test in baseline["tests"] + current["tests"]}

    assert current["changedFiles"] == ["src/bms/soc_estimator.c"]
    assert mapped_tests == {"BMS-SIL-SOC-DRIFT-03"}
    assert mapped_tests.isdisjoint(executed_tests)


@pytest.mark.parametrize(("scenario", "expected"), SCENARIOS.items())
def test_future_analyzer_reports_expected_v03_outcomes(scenario: str, expected: dict) -> None:
    avera_core = pytest.importorskip("avera.core", reason="AVERA core is not implemented yet")
    fixture_dir = FIXTURES_DIR / scenario

    report = avera_core.analyze(
        baseline_path=fixture_dir / "baseline_results.json",
        current_path=fixture_dir / "current_results.json",
        requirements_path=fixture_dir / "requirements.csv",
        component_map_path=fixture_dir / "component_map.json",
        change_description_path=fixture_dir / "change_description.txt",
    )

    assert report["verdict"] == expected["verdict"]
    assert report["risk"] == expected["risk"]
    assert report["confidence"] == expected["confidence"]
