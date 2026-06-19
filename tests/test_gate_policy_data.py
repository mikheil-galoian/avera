"""Tests for policy-as-data: loading policies and applying them deterministically.

Two guarantees are proven here:
1. The built-in default policy reproduces the original hardcoded behaviour.
2. The *same* report yields *different* gate decisions under different policies.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from avera.gates import (
    DEFAULT_GATE_POLICY,
    evaluate_gate,
    list_builtin_policies,
    load_builtin_policy,
    load_policy,
    policy_from_dict,
)
from avera.gates.policy_loader import POLICIES_DIR, PolicyError

ALL_BUILTINS = ["general", "automotive", "aviation", "medical", "railway", "space", "ai_agent"]


def _report(verdict="confirmed_regression", risk="high", confidence_score=0.95, confidence="high"):
    return {
        "schema_version": "avera.assessment.v0.2",
        "verdict": verdict,
        "risk": risk,
        "confidence": confidence,
        "confidence_score": confidence_score,
    }


# ---------------------------------------------------------------------------
# Policy files exist and load
# ---------------------------------------------------------------------------

def test_all_builtin_policy_files_exist():
    for name in ALL_BUILTINS:
        assert (POLICIES_DIR / f"{name}_policy.json").exists(), f"missing policy file for {name}"


def test_list_builtin_policies():
    assert sorted(list_builtin_policies()) == sorted(ALL_BUILTINS)


@pytest.mark.parametrize("name", ALL_BUILTINS)
def test_builtin_policy_loads_and_is_well_formed(name):
    policy = load_builtin_policy(name)
    assert policy.policy_id
    assert policy.max_allowed_risk in {"unknown", "low", "medium", "high", "release_blocking", "safety_critical"}
    assert 0.0 <= policy.min_confidence_score <= 1.0
    assert isinstance(policy.blocking_verdicts, frozenset)
    assert isinstance(policy.review_verdicts, frozenset)


def test_unknown_policy_name_raises():
    with pytest.raises(PolicyError):
        load_builtin_policy("does_not_exist")


def test_malformed_policy_raises(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json", encoding="utf-8")
    with pytest.raises(PolicyError):
        load_policy(bad)

    with pytest.raises(PolicyError):
        policy_from_dict({"policy_id": "x"})  # missing required fields


# ---------------------------------------------------------------------------
# Default policy preserves original behaviour
# ---------------------------------------------------------------------------

def test_general_policy_matches_builtin_default_behaviour():
    """The general policy file must behave identically to the built-in default."""
    general = load_builtin_policy("general")
    for report in (
        _report("successful_change", "low", 0.95, "high"),
        _report("confirmed_regression", "high", 0.95, "high"),
        _report("insufficient_evidence", "unknown", 0.35, "low"),
        _report("preexisting_failure", "medium", 0.9, "high"),
        {},
    ):
        default_decision = evaluate_gate(report)
        general_decision = evaluate_gate(report, policy=general)
        assert default_decision.status == general_decision.status
        assert default_decision.exit_code == general_decision.exit_code


def test_default_policy_id_is_recorded():
    decision = evaluate_gate(_report("successful_change", "low", 0.95))
    assert decision.report_summary["policy_id"] == DEFAULT_GATE_POLICY.policy_id


# ---------------------------------------------------------------------------
# Same report -> different decisions under different policies
# ---------------------------------------------------------------------------

def test_same_report_diverges_across_policies():
    # A medium-risk, medium-confidence successful change:
    # - general: medium risk allowed, conf 0.6 >= 0.5 -> pass
    # - aviation: only low risk allowed -> block
    report = _report("successful_change", "medium", confidence_score=0.6, confidence="medium")

    general = evaluate_gate(report, policy=load_builtin_policy("general"))
    aviation = evaluate_gate(report, policy=load_builtin_policy("aviation"))

    assert general.status == "pass"
    assert aviation.status == "block"
    assert general.status != aviation.status


def test_possible_regression_blocks_in_automotive_but_reviews_in_general():
    report = _report("possible_regression", "low", confidence_score=0.9, confidence="high")

    general = evaluate_gate(report, policy=load_builtin_policy("general"))
    automotive = evaluate_gate(report, policy=load_builtin_policy("automotive"))

    assert general.status == "review"      # possible_regression is review-only by default
    assert automotive.status == "block"    # automotive treats it as blocking


def test_ai_agent_policy_is_more_permissive_than_general_on_risk():
    # High risk, non-blocking verdict, decent confidence.
    report = _report("preexisting_failure", "high", confidence_score=0.9, confidence="high")

    general = evaluate_gate(report, policy=load_builtin_policy("general"))
    ai_agent = evaluate_gate(report, policy=load_builtin_policy("ai_agent"))

    assert general.status == "block"       # high risk > medium allowed
    assert ai_agent.status in ("pass", "review")  # high risk allowed under ai_agent
    assert general.status != ai_agent.status
