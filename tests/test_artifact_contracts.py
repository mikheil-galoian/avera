from __future__ import annotations

import importlib
from copy import deepcopy
from typing import Any

import pytest


VALIDATOR_MODULE_CANDIDATES = (
    "avera.contracts.validator",
    "avera.validation.validator",
    "avera.validation.contracts",
    "avera.contracts",
)

REQUIRED_FIELDS = {
    "report": (
        "schema_version",
        "verdict",
        "risk",
        "confidence",
        "confidence_score",
        "affected_requirements",
        "affected_components",
        "affected_files",
        "introduced_failures",
        "preexisting_failures",
        "threshold_evidence",
        "evidence_summary",
        "recommended_next_checks",
        "comparison_summary",
        "rules_triggered",
        "confidence_factors",
        "risk_drivers",
    ),
    "graph": ("schema_version", "nodes", "edges", "summary"),
    "decision": (
        "schema_version",
        "action",
        "status",
        "category",
        "priority",
        "release_recommendation",
        "owner",
        "owner_routing",
        "actions",
        "corrective_actions",
        "verification_playbook",
        "escalation",
        "context",
        "verdict",
        "risk",
        "confidence",
        "confidence_score",
        "gate_status",
        "rationale",
    ),
    "trend": (
        "schema_version",
        "summary",
        "verdict_history",
        "risk_history",
        "components",
        "requirements",
        "tests",
        "test_stability_buckets",
    ),
    "workspace_pack": (
        "schema_version",
        "workspace",
        "summary",
        "artifacts",
        "report",
        "graph",
        "memory_slice",
        "traceability",
        "decision",
        "trend",
        "manifest",
    ),
}


VALID_PAYLOADS = {
    "report": {
        "schema_version": "avera.report.v0.1",
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "confidence_score": 0.94,
        "affected_requirements": [{"id": "BMS-REQ-118"}],
        "affected_components": ["BMS Thermal Control"],
        "affected_files": ["src/bms/thermal_manager.c"],
        "introduced_failures": [{"test_id": "TC-FAST-01"}],
        "preexisting_failures": [],
        "threshold_evidence": [
            {
                "test_id": "TC-FAST-01",
                "requirement_id": "BMS-REQ-118",
                "metric": "max_cell_temp_c",
                "operator": "<=",
                "threshold": 50.0,
                "baseline_passed": True,
                "current_passed": False,
            }
        ],
        "evidence_summary": ["max_cell_temp_c exceeded threshold"],
        "recommended_next_checks": ["rerun thermal HIL"],
        "comparison_summary": {"baseline": 47.1, "current": 52.8},
        "rules_triggered": ["temperature_over_threshold"],
        "confidence_factors": ["direct_threshold_breach"],
        "risk_drivers": ["thermal_limit_exceeded"],
    },
    "graph": {
        "schema_version": "avera.evidence_graph.v0.1",
        "nodes": [{"id": "n1", "type": "test"}],
        "edges": [{"source": "n1", "target": "n2"}],
        "summary": {"node_count": 1, "edge_count": 1},
    },
    "decision": {
        "schema_version": "avera.decision.v0.2",
        "action": "block",
        "status": "block",
        "category": "containment_required",
        "priority": "immediate",
        "release_recommendation": "do_not_release",
        "owner": "validation_and_component_owner",
        "owner_routing": {
            "primary_owner": "validation_and_component_owner",
            "supporting_owners": ["release_manager", "requirements_owner"],
            "focus_component": "BMS Thermal Control",
        },
        "actions": [
            "freeze_release_candidate",
            "reproduce_failure_on_target_test_path",
        ],
        "corrective_actions": ["fix thermal control regression"],
        "verification_playbook": ["rerun thermal HIL"],
        "escalation": {"level": "program_blocker"},
        "context": {
            "component_count": 1,
            "requirement_count": 1,
            "test_count": 1,
            "top_components": ["BMS Thermal Control"],
        },
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "confidence_score": 0.94,
        "gate_status": "block",
        "rationale": ["verdict:confirmed_regression", "risk:high"],
    },
    "trend": {
        "schema_version": "avera.trend_index.v0.1",
        "summary": {
            "component_count": 1,
            "requirement_count": 1,
            "test_count": 1,
            "memory_record_count": 2,
            "memory_analysis_records": 1,
            "memory_gate_records": 1,
        },
        "verdict_history": [
            {
                "timestamp_utc": "2026-04-28T00:05:00Z",
                "record_type": "gate",
                "verdict": "confirmed_regression",
                "risk": "high",
            }
        ],
        "risk_history": [
            {
                "timestamp_utc": "2026-04-28T00:05:00Z",
                "record_type": "gate",
                "verdict": "confirmed_regression",
                "risk": "high",
            }
        ],
        "components": [
            {
                "component": "BMS Thermal Control",
                "history_count": 1,
                "verdict_counts": {"confirmed_regression": 1},
                "risk_counts": {"high": 1},
                "latest_timestamp_utc": "2026-04-28T00:00:00Z",
            }
        ],
        "requirements": [
            {
                "requirement": "BMS-REQ-118",
                "history_count": 1,
                "verdict_counts": {"confirmed_regression": 1},
                "risk_counts": {"high": 1},
                "latest_timestamp_utc": "2026-04-28T00:00:00Z",
            }
        ],
        "tests": [
            {
                "test": "TC-FAST-01",
                "components": ["BMS Thermal Control"],
                "requirements": ["BMS-REQ-118"],
                "status_counts": {"fail": 1},
                "stability_bucket": "regressed",
            }
        ],
        "test_stability_buckets": {
            "stable": [],
            "regressed": ["TC-FAST-01"],
            "unstable": [],
        },
    },
    "workspace_pack": {
        "schema_version": "avera.workspace_pack.v0.1",
        "workspace": {"path": "fixtures/bms-fast-charge", "name": "bms-fast-charge"},
        "summary": {
            "verdict": "confirmed_regression",
            "risk": "high",
            "confidence": "high",
            "confidence_score": 0.94,
            "component_count": 1,
            "requirement_count": 1,
            "introduced_failure_count": 1,
            "preexisting_failure_count": 0,
            "memory_slice_count": 1,
            "missing_artifacts": [],
        },
        "artifacts": {
            "report_json": {"path": "reports/avera-report.json", "exists": True},
            "report_markdown": {"path": "reports/avera-report.md", "exists": True},
            "graph_json": {"path": "reports/avera-evidence-graph.json", "exists": True},
            "memory_jsonl": {"path": "reports/avera-memory.jsonl", "exists": True},
            "traceability_json": {"path": "reports/avera-traceability-index.json", "exists": True},
            "decision_json": {"path": "reports/avera-decision.json", "exists": True},
            "trend_json": {"path": "reports/avera-trend-index.json", "exists": True},
        },
        "report": {
            "schema_version": "avera.assessment.v0.2",
            "json_path": "reports/avera-report.json",
            "markdown_path": "reports/avera-report.md",
            "verdict": "confirmed_regression",
            "risk": "high",
        },
        "graph": {
            "schema_version": "evidence_graph.v0.3",
            "path": "reports/avera-evidence-graph.json",
            "summary": {"node_count": 1, "edge_count": 1},
        },
        "memory_slice": [
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-28T00:00:00Z",
                "report_path": "reports/avera-report.json",
                "verdict": "confirmed_regression",
                "risk": "high",
            }
        ],
        "traceability": {
            "schema_version": "avera.traceability_index.v0.1",
            "path": "reports/avera-traceability-index.json",
            "summary": {"component_count": 1},
        },
        "decision": {
            "schema_version": "avera.decision.v0.2",
            "path": "reports/avera-decision.json",
            "action": "block",
            "category": "containment_required",
            "owner": "validation_and_component_owner",
        },
        "trend": {
            "schema_version": "avera.trend_index.v0.1",
            "path": "reports/avera-trend-index.json",
            "summary": {"component_count": 1},
        },
        "manifest": {
            "schema_version": "avera.workspace_pack.v0.1",
            "exported_at_utc": "2026-04-28T00:00:00Z",
            "workspace_path": "fixtures/bms-fast-charge",
            "source_artifacts": {
                "report_json": "reports/avera-report.json",
                "report_markdown": "reports/avera-report.md",
                "graph_json": "reports/avera-evidence-graph.json",
                "memory_jsonl": "reports/avera-memory.jsonl",
                "traceability_json": "reports/avera-traceability-index.json",
                "decision_json": "reports/avera-decision.json",
                "trend_json": "reports/avera-trend-index.json",
            },
            "artifact_count": 7,
            "missing_artifacts": [],
        },
    },
}

def test_validate_artifact_accepts_known_top_level_contracts() -> None:
    validate_artifact = _require_validator("validate_artifact")

    for artifact_name, payload in VALID_PAYLOADS.items():
        if artifact_name == "workspace_pack":
            continue

        assert set(payload) == set(REQUIRED_FIELDS[artifact_name])
        result = validate_artifact(artifact_name, deepcopy(payload))
        assert _is_ok(result), _describe_failure(result)


@pytest.mark.parametrize(
    ("artifact_name", "missing_field"),
    [
        ("report", "schema_version"),
        ("graph", "edges"),
        ("decision", "rationale"),
        ("trend", "test_stability_buckets"),
    ],
)
def test_validate_artifact_rejects_missing_required_fields(
    artifact_name: str,
    missing_field: str,
) -> None:
    validate_artifact = _require_validator("validate_artifact")

    payload = deepcopy(VALID_PAYLOADS[artifact_name])
    payload.pop(missing_field)

    result = validate_artifact(artifact_name, payload)

    assert not _is_ok(result)
    assert missing_field in _joined_messages(result)


def test_validate_artifact_rejects_unknown_artifact_name() -> None:
    validate_artifact = _require_validator("validate_artifact")

    result = validate_artifact("telemetry_snapshot", {"schema_version": "avera.telemetry.v0.1"})

    assert not _is_ok(result)
    messages = _joined_messages(result).lower()
    assert any(token in messages for token in ("unknown", "unsupported", "unrecognized", "artifact"))


def test_validate_artifact_warns_on_unsupported_schema_version() -> None:
    # Audit regression (#19): a known artifact carrying a schema_version that is
    # not in the central registry must be flagged, not pass silently.
    validate_artifact = _require_validator("validate_artifact")

    payload = deepcopy(VALID_PAYLOADS["decision"])
    payload["schema_version"] = "avera.decision.v9.9"  # not a registered version
    result = validate_artifact("decision", payload)

    warnings_text = " ".join(getattr(result, "warnings", []) or [])
    assert "v9.9" in warnings_text or "supported version" in warnings_text


def test_validate_artifact_accepts_registered_schema_version() -> None:
    validate_artifact = _require_validator("validate_artifact")
    payload = deepcopy(VALID_PAYLOADS["decision"])  # uses the registered version
    result = validate_artifact("decision", payload)
    warnings_text = " ".join(getattr(result, "warnings", []) or [])
    assert "supported version" not in warnings_text


def test_validate_bundle_accepts_complete_workspace_pack_contract() -> None:
    validate_bundle = _maybe_validator("validate_bundle")
    if validate_bundle is None:
        pytest.skip("validate_bundle is not exposed by the artifact validator module")

    assert set(VALID_PAYLOADS["workspace_pack"]) == set(REQUIRED_FIELDS["workspace_pack"])
    result = validate_bundle(deepcopy(VALID_PAYLOADS["workspace_pack"]))

    assert _is_ok(result), _describe_failure(result)


def test_validate_bundle_rejects_missing_workspace_pack_fields() -> None:
    validate_bundle = _maybe_validator("validate_bundle")
    if validate_bundle is None:
        pytest.skip("validate_bundle is not exposed by the artifact validator module")

    payload = deepcopy(VALID_PAYLOADS["workspace_pack"])
    payload.pop("manifest")

    result = validate_bundle(payload)

    assert not _is_ok(result)
    assert "manifest" in _joined_messages(result)


def _import_validator_module() -> Any | None:
    for module_name in VALIDATOR_MODULE_CANDIDATES:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
    return None


def _require_validator(function_name: str):
    function = _maybe_validator(function_name)
    if function is None:
        pytest.skip(f"{function_name} is not exposed by the artifact validator module")
    return function


def _maybe_validator(function_name: str):
    validator = _import_validator_module()
    if validator is None:
        return None
    function = getattr(validator, function_name, None)
    return function if callable(function) else None


def _is_ok(result: Any) -> bool:
    if isinstance(result, bool):
        return result

    if isinstance(result, dict):
        for key in ("ok", "valid", "success"):
            if key in result:
                return bool(result[key])
        if "errors" in result:
            return not bool(result["errors"])

    for attr in ("ok", "valid", "success"):
        if hasattr(result, attr):
            return bool(getattr(result, attr))

    if isinstance(result, tuple) and result:
        if isinstance(result[0], bool):
            return result[0]

    raise AssertionError(f"Could not determine validation status from {result!r}")


def _joined_messages(result: Any) -> str:
    messages: list[str] = []

    if isinstance(result, dict):
        for key in ("errors", "warnings", "messages"):
            values = result.get(key)
            if isinstance(values, list):
                messages.extend(str(item) for item in values)
    else:
        for attr in ("errors", "warnings", "messages"):
            if hasattr(result, attr):
                values = getattr(result, attr)
                if isinstance(values, list):
                    messages.extend(str(item) for item in values)

    if not messages:
        return repr(result)
    return "\n".join(messages)


def _describe_failure(result: Any) -> str:
    if _is_ok(result):
        return ""
    return _joined_messages(result)
