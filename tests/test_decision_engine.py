from __future__ import annotations

import inspect
from typing import Any

import pytest


decisions_engine = pytest.importorskip(
    "avera.decisions.engine",
    reason="decision engine module is not implemented yet",
)


def test_evaluate_decision_maps_core_verdicts_to_expected_actions() -> None:
    scenarios = [
        (
            "confirmed_regression",
            {
                "verdict": "confirmed_regression",
                "risk": "high",
                "confidence": "high",
                "confidence_score": 0.94,
                "affected_components": ["BMS Thermal Control"],
            },
            {
                "status": "block",
                "gate_exit_code": 1,
                "reason_hint": "blocking verdict",
            },
            {
                "components": {
                    "BMS Thermal Control": {
                        "requirements": ["BMS-REQ-118"],
                        "tests": ["TC-FAST-01"],
                    }
                },
                "tests": {
                    "TC-FAST-01": {
                        "status": "fail",
                        "requirement_id": "BMS-REQ-118",
                    }
                },
            },
            "block",
            {
                "primary_owner": "validation_and_component_owner",
                "supporting_owners": ["release_manager", "requirements_owner"],
                "focus_component": "BMS Thermal Control",
                "escalation_level": "program_blocker",
                "corrective_actions": True,
            },
        ),
        (
            "successful_change",
            {
                "verdict": "successful_change",
                "risk": "low",
                "confidence": "high",
                "confidence_score": 0.91,
                "affected_components": ["BMS Power"],
            },
            {
                "status": "pass",
                "gate_exit_code": 0,
                "reason_hint": "report satisfies gate policy",
            },
            {
                "components": {
                    "BMS Power": {
                        "requirements": ["BMS-REQ-112"],
                        "tests": ["TC-BOOT-02"],
                    }
                },
                "tests": {
                    "TC-BOOT-02": {
                        "status": "pass",
                        "requirement_id": "BMS-REQ-112",
                    }
                },
            },
            "allow",
            {
                "primary_owner": "component_owner",
                "supporting_owners": ["release_manager"],
                "focus_component": "BMS Power",
                "escalation_level": "none",
                "corrective_actions": False,
            },
        ),
        (
            "insufficient_evidence",
            {
                "verdict": "insufficient_evidence",
                "risk": "unknown",
                "confidence": "low",
                "confidence_score": 0.12,
                "affected_components": ["BMS Diagnostics"],
            },
            {
                "status": "review",
                "gate_exit_code": 1,
                "reason_hint": "manual review verdict",
            },
            {
                "components": {},
                "tests": {},
            },
            "review",
            {
                "primary_owner": "test_and_requirements_owner",
                "supporting_owners": ["component_owner", "validation_lead"],
                "focus_component": "BMS Diagnostics",
                "escalation_level": "review_required",
                "corrective_actions": True,
            },
        ),
        (
            "requirements_coverage_gap",
            {
                "verdict": "requirements_coverage_gap",
                "risk": "medium",
                "confidence": "medium",
                "confidence_score": 0.44,
                "affected_components": ["BMS Charge Controller"],
            },
            {
                "status": "review",
                "gate_exit_code": 1,
                "reason_hint": "manual review verdict",
            },
            {
                "components": {
                    "BMS Charge Controller": {
                        "requirements": ["BMS-REQ-119"],
                        "tests": [],
                    }
                },
                "tests": {},
            },
            "review",
            {
                "primary_owner": "test_and_requirements_owner",
                "supporting_owners": ["component_owner", "validation_lead"],
                "focus_component": "BMS Charge Controller",
                "escalation_level": "review_required",
                "corrective_actions": True,
            },
        ),
        (
            "environment_failure",
            {
                "verdict": "environment_failure",
                "risk": "unknown",
                "confidence": "low",
                "confidence_score": 0.25,
                "affected_components": ["Test Harness"],
            },
            {
                "status": "review",
                "gate_exit_code": 1,
                "reason_hint": "manual review verdict",
            },
            {
                "components": {
                    "Test Harness": {
                        "requirements": [],
                        "tests": ["TC-ENV-01"],
                    }
                },
                "tests": {
                    "TC-ENV-01": {
                        "status": "error",
                        "classification": "environment_failure",
                    }
                },
            },
            "review",
            {
                "primary_owner": "ci_or_lab_owner",
                "supporting_owners": ["validation_lead"],
                "focus_component": "Test Harness",
                "escalation_level": "lab_attention",
                "corrective_actions": True,
            },
        ),
    ]

    for verdict, report, gate, traceability, expected_action, policy_expectations in scenarios:
        decision = _evaluate_decision(report, gate=gate, traceability=traceability)

        assert isinstance(decision, dict)
        assert _decision_action(decision) == expected_action
        assert decision["verdict"] == verdict
        assert decision["risk"] == report["risk"]
        _assert_recommendation_policy_v2(decision, policy_expectations)


def _evaluate_decision(
    report: dict[str, Any],
    *,
    gate: dict[str, Any] | None = None,
    traceability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    function = decisions_engine.evaluate_decision
    signature = inspect.signature(function)
    parameters = list(signature.parameters.values())

    if {"report", "gate", "traceability"}.issubset(signature.parameters):
        return function(report=report, gate=gate, traceability=traceability)

    if len(parameters) >= 3:
        return function(report, gate, traceability)

    if len(parameters) == 2:
        second_name = parameters[1].name
        if second_name in {"gate", "decision_gate"}:
            return function(report, gate)
        if second_name in {"traceability", "traceability_index"}:
            return function(report, traceability)

    if len(parameters) == 1:
        return function(report)

    try:
        return function(report=report, gate=gate, traceability=traceability)
    except TypeError:
        return function(report)


def _decision_action(decision: dict[str, Any]) -> str:
    action = decision.get("action", decision.get("status"))
    assert action is not None, "decision result must expose an action or status"
    return str(action)


def _assert_recommendation_policy_v2(
    decision: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    assert decision["schema_version"] == "avera.decision.v0.2"

    owner_routing = decision["owner_routing"]
    assert isinstance(owner_routing, dict)
    assert owner_routing["primary_owner"] == expected["primary_owner"]
    assert owner_routing["supporting_owners"] == expected["supporting_owners"]
    assert owner_routing["focus_component"] == expected["focus_component"]

    corrective_actions = decision["corrective_actions"]
    verification_playbook = decision["verification_playbook"]
    escalation = decision["escalation"]
    context = decision["context"]

    assert isinstance(corrective_actions, list)
    assert all(isinstance(item, str) for item in corrective_actions)
    assert bool(corrective_actions) is expected["corrective_actions"]

    assert isinstance(verification_playbook, list)
    assert all(isinstance(item, str) for item in verification_playbook)
    assert verification_playbook

    assert isinstance(escalation, dict)
    assert escalation["level"] == expected["escalation_level"]
    assert isinstance(escalation["notify"], list)
    assert all(isinstance(item, str) for item in escalation["notify"])
    assert escalation["notify"]

    assert isinstance(context, dict)
    assert set(context) == {"component_count", "requirement_count", "test_count", "top_components"}
    assert isinstance(context["component_count"], int)
    assert isinstance(context["requirement_count"], int)
    assert isinstance(context["test_count"], int)
    assert context["top_components"] == [expected["focus_component"]]
