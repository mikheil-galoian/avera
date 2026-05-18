import csv
import json
from pathlib import Path

import pytest


FIXTURE_DIR = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "adas-pedestrian-detection-regression"
)


def load_json(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_adas_fixture_files_exist() -> None:
    expected_files = {
        "requirements.csv",
        "component_map.json",
        "baseline_results.json",
        "current_results.json",
        "change_description.txt",
        "signal_trace.csv",
    }

    assert FIXTURE_DIR.is_dir()
    assert expected_files == {path.name for path in FIXTURE_DIR.iterdir() if path.is_file()}


def test_requirements_capture_pedestrian_recall_and_braking_latency_limits() -> None:
    with (FIXTURE_DIR / "requirements.csv").open(encoding="utf-8", newline="") as requirements_file:
        requirements = {row["id"]: row for row in csv.DictReader(requirements_file)}

    assert requirements["ADAS-REQ-204"] == {
        "id": "ADAS-REQ-204",
        "component": "ADAS Pedestrian Detection",
        "requirement": "Pedestrian recall in urban daylight regression suite must not fall below 0.95",
        "metric": "pedestrian_recall",
        "operator": ">=",
        "threshold": "0.95",
        "safety_level": "high",
        "next_checks": "ADAS-HIL-VRU-12",
    }
    assert requirements["ADAS-REQ-219"]["metric"] == "brake_trigger_latency_ms"
    assert requirements["ADAS-REQ-219"]["threshold"] == "120.0"


def test_component_map_connects_changed_file_to_adas_requirements_and_test() -> None:
    component_map = load_json("component_map.json")

    classifier = component_map["src/adas/perception/pedestrian_classifier.cpp"]

    assert classifier["component"] == "ADAS Pedestrian Detection"
    assert classifier["requirements"] == ["ADAS-REQ-204", "ADAS-REQ-219"]
    assert classifier["tests"] == ["ADAS-SIL-VRU-REGRESSION-03"]


def test_current_result_is_a_high_risk_adas_regression_against_baseline() -> None:
    baseline = load_json("baseline_results.json")
    current = load_json("current_results.json")

    baseline_test = baseline["tests"][0]
    current_test = current["tests"][0]

    assert baseline["stage"] == "baseline"
    assert current["stage"] == "current"
    assert baseline_test["status"] == "passed"
    assert current_test["status"] == "failed"
    assert baseline_test["metrics"]["pedestrian_recall"] == 0.972
    assert current_test["metrics"]["pedestrian_recall"] == 0.903
    assert baseline_test["metrics"]["brake_trigger_latency_ms"] == 104.0
    assert current_test["metrics"]["brake_trigger_latency_ms"] == 146.0
    assert baseline_test["metrics"]["pedestrian_recall"] >= 0.95
    assert current_test["metrics"]["pedestrian_recall"] < 0.95
    assert baseline_test["metrics"]["brake_trigger_latency_ms"] <= 120.0
    assert current_test["metrics"]["brake_trigger_latency_ms"] > 120.0
    assert current["changedFiles"] == ["src/adas/perception/pedestrian_classifier.cpp"]


def test_signal_trace_shows_worsening_recall_and_braking_latency() -> None:
    with (FIXTURE_DIR / "signal_trace.csv").open(encoding="utf-8", newline="") as signal_file:
        rows = list(csv.DictReader(signal_file))

    recall_values = [
        float(row["value"])
        for row in rows
        if row["signal"] == "pedestrian_recall"
    ]
    latency_values = [
        float(row["value"])
        for row in rows
        if row["signal"] == "brake_trigger_latency_ms"
    ]

    assert recall_values == [0.972, 0.948, 0.921, 0.903]
    assert latency_values == [104.0, 118.0, 132.0, 146.0]


def test_future_analyzer_reports_high_confidence_adas_regression() -> None:
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
