from __future__ import annotations

import sys
import types
from pathlib import Path

# Make avera_demo importable from the demo/ subdirectory
_demo_dir = Path(__file__).resolve().parents[1] / "demo"
if str(_demo_dir) not in sys.path:
    sys.path.insert(0, str(_demo_dir))

from avera_demo.artifacts import build_profile, artifact_catalog, list_scenarios_for_track, scenario_paths

streamlit_stub = types.SimpleNamespace()
sys.modules.setdefault("streamlit", streamlit_stub)

from avera_demo.views import build_decision_review, build_traceability_counts, normalize_bucket


def test_known_demo_scenario_exposes_review_surface_metadata() -> None:
    scenario = scenario_paths("adas-pedestrian-detection-regression")

    profile = build_profile(scenario)
    artifacts = artifact_catalog(scenario)
    artifact_labels = {artifact.label for artifact in artifacts}

    assert profile.domain == "ADAS"
    assert profile.title == "Pedestrian detection regression"
    assert "pedestrian recall" in profile.summary.lower()
    assert "cross-domain proof" in profile.use_case.lower()
    assert "brake_trigger_latency_ms" in profile.primary_signal
    assert "static ADAS showcase asset" in profile.fallback_note

    assert {"Assessment Report", "Traceability Index", "Decision", "Workspace Pack"} <= artifact_labels


def test_adapted_simulation_scenario_exposes_raw_source_artifacts() -> None:
    scenario = scenario_paths("adas-simulation-adapted")

    profile = build_profile(scenario)
    artifacts = artifact_catalog(scenario)
    artifact_labels = {artifact.label for artifact in artifacts}

    assert profile.domain == "ADAS"
    assert "adapted simulation" in profile.title.lower()
    assert "external simulation evidence" in profile.use_case.lower()
    assert "Baseline Simulation CSV" in artifact_labels
    assert "Current Simulation CSV" in artifact_labels


def test_adapted_requirements_scenario_exposes_raw_requirements_export() -> None:
    scenario = scenario_paths("bms-requirements-adapted")

    profile = build_profile(scenario)
    artifacts = artifact_catalog(scenario)
    artifact_labels = {artifact.label for artifact in artifacts}

    assert profile.domain == "BMS"
    assert "adapted requirements" in profile.title.lower()
    assert "richer requirements exports" in profile.use_case.lower()
    assert "Requirements Export Variant" in artifact_labels


def test_adapted_log_scenario_exposes_raw_verification_logs() -> None:
    scenario = scenario_paths("bms-log-adapted")

    profile = build_profile(scenario)
    artifacts = artifact_catalog(scenario)
    artifact_labels = {artifact.label for artifact in artifacts}

    assert profile.domain == "BMS"
    assert "verification log" in profile.title.lower()
    assert "richer verification logs" in profile.use_case.lower()
    assert "Baseline Verification Log CSV" in artifact_labels
    assert "Current Verification Log CSV" in artifact_labels


def test_adapted_track_groups_only_adapted_scenarios() -> None:
    adapted = list_scenarios_for_track("adapted")
    standard = list_scenarios_for_track("standard")

    assert "adas-simulation-adapted" in adapted
    assert "bms-requirements-adapted" in adapted
    assert "bms-log-adapted" in adapted
    assert "bms-fast-charge" not in adapted
    assert "bms-fast-charge" in standard


def test_traceability_review_bucket_preserves_labels_for_navigation() -> None:
    payload = [
        {
            "component": "BMS Thermal Control",
            "requirements": ["BMS-REQ-101"],
            "tests": ["TC-BMS-FAST-01"],
            "failures": [{"id": "FAIL-1"}],
        },
        {
            "id": "REQ-FALLBACK",
            "requirements": ["REQ-FALLBACK"],
            "tests": [],
            "failures": [],
        },
        {
            "name": "Named fallback",
            "requirements": [],
            "tests": ["TC-NAMED-01"],
            "failures": [],
        },
    ]

    rows = normalize_bucket(payload, "component")

    assert [row["label"] for row in rows] == [
        "BMS Thermal Control",
        "REQ-FALLBACK",
        "Named fallback",
    ]
    assert rows[0]["payload"]["requirements"] == ["BMS-REQ-101"]
    assert rows[0]["payload"]["tests"] == ["TC-BMS-FAST-01"]


def test_decision_review_builder_exposes_readable_sections() -> None:
    summary_rows, rationale, corrective_actions, verification_playbook, escalation = build_decision_review(
        {
            "action": "block",
            "category": "confirmed_regression",
            "priority": "high",
            "owner": "validation",
            "release_recommendation": "hold release",
            "rationale": ["Regression confirmed against baseline"],
            "corrective_actions": ["Re-run focused thermal validation"],
            "verification_playbook": ["Run BMS fast-charge fixture"],
            "escalation": "Escalate to release gate owner",
        }
    )

    assert summary_rows[0] == {"field": "Action", "value": "block"}
    assert summary_rows[-1] == {"field": "Release Recommendation", "value": "hold release"}
    assert rationale == ["Regression confirmed against baseline"]
    assert corrective_actions == ["Re-run focused thermal validation"]
    assert verification_playbook == ["Run BMS fast-charge fixture"]
    assert escalation == "Escalate to release gate owner"


def test_traceability_counts_builder_summarizes_review_scope() -> None:
    counts = build_traceability_counts(
        {
            "components": [{"component": "BMS Thermal Control"}, {"component": "Charge Arbitration"}],
            "requirements": [{"requirement": "REQ-BMS-002"}],
            "tests": [{"test": "TC-FAST-01"}, {"id": "TC-FAST-02"}],
        }
    )

    assert counts == {"components": 2, "requirements": 1, "tests": 2}
