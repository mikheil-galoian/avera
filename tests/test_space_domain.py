"""Space domain — NASA NPR 7150.2 software classes wired into AVERA.

Verifies the new domain reuses the existing architecture: the policy loads and is
strict, NASA classes map onto the central safety-rank scale, and a real
introduced regression on a Class-A (human-rated) requirement blocks the gate.
"""

from __future__ import annotations

from avera.classify.risk_levels import safety_rank
from avera.classify.risk_classifier import classify_risk
from avera.domains.space import (
    NASA_CLASS_RANK,
    nasa_class_rank,
    independent_assurance_required,
    SPACE_REQUIREMENTS_TEMPLATE,
)
from avera.gates.policy import evaluate_gate
from avera.gates.policy_loader import load_builtin_policy, list_builtin_policies


# --- policy is registered and strict ----------------------------------------

def test_space_policy_registered_and_strict():
    assert "space" in list_builtin_policies()
    pol = load_builtin_policy("space")
    assert pol.domain == "space"
    assert pol.max_allowed_risk == "low"
    assert pol.min_confidence_score >= 0.8
    assert "possible_regression" in pol.blocking_verdicts
    assert "requirements_coverage_gap" in pol.blocking_verdicts


# --- NASA classes land on the central safety-rank scale ----------------------

def test_nasa_classes_map_onto_safety_rank():
    # Class A (human-rated) is the most critical; F the least.
    assert safety_rank("nasa-a") == 4
    assert safety_rank("nasa-b") == 3
    assert safety_rank("nasa-c") == 2
    assert safety_rank("nasa-f") == 0
    # Single-letter forms stay reserved for ASIL — not hijacked by NASA.
    assert safety_rank("a") == 1  # ASIL-A, unchanged
    assert nasa_class_rank("human_rated") == 4
    assert independent_assurance_required("nasa-a") is True
    assert independent_assurance_required("nasa-c") is False


def test_class_rank_ordering_is_monotonic():
    order = ["nasa-f", "nasa-e", "nasa-d", "nasa-c", "nasa-b", "nasa-a"]
    ranks = [NASA_CLASS_RANK[c] for c in order]
    assert ranks == sorted(ranks)


# --- end-to-end: a regression on a human-rated requirement blocks -------------

def test_introduced_regression_on_class_a_blocks_space_gate():
    gnc = next(r for r in SPACE_REQUIREMENTS_TEMPLATE if r["safety_level"] == "nasa-a")
    comparison = {
        "introduced_failures": [{"test_id": "gnc_attitude", "component": gnc["component"]}],
        "preexisting_failures": [],
        "missing_baseline": [],
        "tests": [{"id": "gnc_attitude", "status": "failed", "classification": "introduced_failure"}],
        "metric_deltas": [],
    }
    assessment = classify_risk(comparison=comparison, requirements=[gnc])
    assert assessment.verdict == "confirmed_regression"

    from avera.core import assessment_to_public_report
    report = assessment_to_public_report(assessment)
    decision = evaluate_gate(report, policy=load_builtin_policy("space"))
    assert decision.status == "block"
