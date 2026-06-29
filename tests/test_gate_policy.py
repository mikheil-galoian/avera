"""Tests for avera.gates.policy — evaluate_gate()."""

from __future__ import annotations

import pytest

from avera.gates.policy import GateDecision, evaluate_gate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _report(
    verdict: str = "successful_change",
    risk: str = "low",
    confidence: str = "high",
    confidence_score: float = 0.95,
    schema_version: str = "avera.assessment.v0.2",
) -> dict:
    return {
        "schema_version": schema_version,
        "verdict": verdict,
        "risk": risk,
        "confidence": confidence,
        "confidence_score": confidence_score,
    }


# ---------------------------------------------------------------------------
# Status: pass
# ---------------------------------------------------------------------------

class TestGatePass:
    def test_successful_change_low_risk_is_pass(self):
        result = evaluate_gate(_report("successful_change", "low", confidence_score=0.95))
        assert result.status == "pass"
        assert result.exit_code == 0

    def test_expected_change_is_pass(self):
        result = evaluate_gate(_report("expected_change", "low", confidence_score=0.9))
        assert result.status == "pass"

    def test_pass_contains_satisfaction_reason(self):
        result = evaluate_gate(_report())
        assert any("satisfies" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Status: block
# ---------------------------------------------------------------------------

class TestGateBlock:
    def test_confirmed_regression_is_block(self):
        result = evaluate_gate(_report("confirmed_regression", "high", confidence_score=0.95))
        assert result.status == "block"
        assert result.exit_code == 1

    def test_worsened_preexisting_failure_is_block(self):
        result = evaluate_gate(_report("worsened_preexisting_failure", "high", confidence_score=0.95))
        assert result.status == "block"

    def test_high_risk_exceeding_default_medium_threshold_is_block(self):
        result = evaluate_gate(_report("preexisting_failure", "high", confidence_score=0.95))
        assert result.status == "block"

    def test_block_reason_mentions_verdict(self):
        result = evaluate_gate(_report("confirmed_regression", "high", confidence_score=0.95))
        assert any("confirmed_regression" in r for r in result.reasons)

    def test_block_reason_mentions_risk_when_risk_exceeds_limit(self):
        result = evaluate_gate(_report("preexisting_failure", "high", confidence_score=0.9))
        assert any("high" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# Status: review
# ---------------------------------------------------------------------------

class TestGateReview:
    def test_insufficient_evidence_is_review(self):
        result = evaluate_gate(_report("insufficient_evidence", "unknown", confidence_score=0.35))
        assert result.status == "review"

    def test_environment_failure_is_review(self):
        result = evaluate_gate(_report("environment_failure", "unknown", confidence_score=0.4))
        assert result.status == "review"

    def test_possible_regression_is_review(self):
        result = evaluate_gate(_report("possible_regression", "medium", confidence_score=0.6))
        assert result.status == "review"

    def test_requirements_coverage_gap_is_review(self):
        result = evaluate_gate(_report("requirements_coverage_gap", "medium", confidence_score=0.55))
        assert result.status == "review"

    def test_low_confidence_score_triggers_review(self):
        result = evaluate_gate(_report("expected_change", "low", confidence_score=0.3))
        assert result.status == "review"

    def test_review_reason_mentions_verdict(self):
        result = evaluate_gate(_report("insufficient_evidence", "unknown", confidence_score=0.35))
        assert any("review" in r.lower() for r in result.reasons)


# ---------------------------------------------------------------------------
# Custom thresholds
# ---------------------------------------------------------------------------

class TestCustomThresholds:
    def test_strict_max_risk_blocks_medium_risk(self):
        result = evaluate_gate(
            _report("preexisting_failure", "medium", confidence_score=0.9),
            max_allowed_risk="low",
        )
        assert result.status == "block"

    def test_relaxed_max_risk_allows_high_risk_preexisting(self):
        result = evaluate_gate(
            _report("preexisting_failure", "high", confidence_score=0.9),
            max_allowed_risk="high",
        )
        # Not a blocking verdict — with high risk allowed, preexisting might pass risk check
        # but verdict may still put it in review depending on score
        assert result.status in ("pass", "review")

    def test_high_min_confidence_triggers_review_for_medium_score(self):
        result = evaluate_gate(
            _report("expected_change", "low", confidence_score=0.7),
            min_confidence_score=0.8,
        )
        assert result.status == "review"


# ---------------------------------------------------------------------------
# GateDecision shape
# ---------------------------------------------------------------------------

class TestGateDecisionShape:
    def test_report_summary_included_in_decision(self):
        result = evaluate_gate(_report("successful_change", "low", confidence_score=0.95))
        assert result.report_summary["verdict"] == "successful_change"
        assert result.report_summary["risk"] == "low"
        assert result.report_summary["confidence_score"] == pytest.approx(0.95)

    def test_reasons_is_non_empty_list(self):
        result = evaluate_gate(_report())
        assert isinstance(result.reasons, list)
        assert len(result.reasons) >= 1

    def test_exit_code_2_for_review(self):
        # review still fails the build (non-zero, fail-closed) but uses a distinct
        # exit code (2) so CI can tell "needs review" apart from a confirmed block (1).
        result = evaluate_gate(_report("insufficient_evidence", "unknown", confidence_score=0.35))
        assert result.status == "review"
        assert result.exit_code == 2

    def test_missing_fields_default_gracefully(self):
        result = evaluate_gate({})
        assert result.status in ("block", "review")  # no verdict → insufficient_evidence → review


# ---------------------------------------------------------------------------
# Risk rank ordering
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("risk,expected_status", [
    ("low", "pass"),
    ("medium", "pass"),
    ("high", "block"),
    ("release_blocking", "block"),
])
def test_risk_rank_determines_gate_status_for_preexisting_verdict(risk, expected_status):
    result = evaluate_gate(_report("preexisting_failure", risk, confidence_score=0.9))
    assert result.status == expected_status
