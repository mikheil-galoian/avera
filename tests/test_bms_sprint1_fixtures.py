import json
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"

SCENARIOS = {
    "bms-successful-change": {
        "verdict": "successful_change",
        "risk": "low",
        "confidence": "high",
    },
    "bms-preexisting-failure": {
        "verdict": "preexisting_failure",
        "risk": "medium",
        "confidence": "high",
    },
    "bms-insufficient-evidence": {
        "verdict": "insufficient_evidence",
        "risk": "unknown",
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
def test_sprint1_fixture_files_exist(scenario: str) -> None:
    fixture_dir = FIXTURES_DIR / scenario

    assert fixture_dir.is_dir()
    assert EXPECTED_FILES == {path.name for path in fixture_dir.iterdir() if path.is_file()}


def test_successful_change_fixture_stays_within_requirements() -> None:
    baseline = load_json("bms-successful-change", "baseline_results.json")
    current = load_json("bms-successful-change", "current_results.json")

    assert baseline["tests"][0]["status"] == "passed"
    assert current["tests"][0]["status"] == "passed"
    assert current["tests"][0]["metrics"]["max_cell_temp_c"] <= 50.0
    assert current["tests"][0]["metrics"]["cooling_response_ms"] <= 500.0
    assert current["tests"][0]["metrics"]["max_cell_temp_c"] < baseline["tests"][0]["metrics"]["max_cell_temp_c"]


def test_preexisting_failure_fixture_fails_before_current_change() -> None:
    baseline = load_json("bms-preexisting-failure", "baseline_results.json")
    current = load_json("bms-preexisting-failure", "current_results.json")

    assert baseline["tests"][0]["status"] == "failed"
    assert current["tests"][0]["status"] == "failed"
    assert baseline["tests"][0]["metrics"]["max_cell_temp_c"] > 50.0
    assert current["tests"][0]["metrics"]["max_cell_temp_c"] > 50.0


def test_insufficient_evidence_fixture_missing_current_required_metric() -> None:
    baseline = load_json("bms-insufficient-evidence", "baseline_results.json")
    current = load_json("bms-insufficient-evidence", "current_results.json")

    assert baseline["tests"][0]["status"] == "passed"
    assert current["tests"][0]["status"] == "inconclusive"
    assert "max_cell_temp_c" in baseline["tests"][0]["metrics"]
    assert "max_cell_temp_c" not in current["tests"][0]["metrics"]


@pytest.mark.parametrize(("scenario", "expected"), SCENARIOS.items())
def test_future_analyzer_reports_expected_sprint1_outcomes(scenario: str, expected: dict) -> None:
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
