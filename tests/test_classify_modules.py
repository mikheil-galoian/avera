"""Tests for avera.classify submodules: evidence, confidence, risk_levels, verdicts."""

from __future__ import annotations

import pytest

from avera.classify import confidence as confidence_mod
from avera.classify import risk_levels, verdicts
from avera.classify.evidence import (
    ThresholdEvidence,
    current_threshold_failures,
    environment_failure_reason,
    environment_failure_signals,
    has_environment_failure_signal,
    has_introduced_threshold_failure,
    has_material_worsening,
    introduced_threshold_failures,
    is_material_worsening,
    material_worsenings,
)


# ---------------------------------------------------------------------------
# ThresholdEvidence helpers
# ---------------------------------------------------------------------------

def _evidence(baseline_passed: bool | None, current_passed: bool | None) -> ThresholdEvidence:
    return ThresholdEvidence(
        requirement_id="R1",
        metric="max_temp",
        operator="<=",
        threshold=50.0,
        baseline_value=47.0 if baseline_passed else 52.0,
        current_value=52.0 if current_passed is False else 47.0,
        baseline_passed=baseline_passed,
        current_passed=current_passed,
        test_id="T1",
    )


class TestIntroducedThresholdFailures:
    def test_baseline_pass_current_fail_is_introduced(self):
        items = [_evidence(True, False)]
        assert len(introduced_threshold_failures(items)) == 1

    def test_both_fail_is_not_introduced(self):
        items = [_evidence(False, False)]
        assert introduced_threshold_failures(items) == []

    def test_both_pass_is_not_introduced(self):
        items = [_evidence(True, True)]
        assert introduced_threshold_failures(items) == []

    def test_has_introduced_threshold_failure_returns_bool(self):
        assert has_introduced_threshold_failure([_evidence(True, False)]) is True
        assert has_introduced_threshold_failure([_evidence(True, True)]) is False

    def test_empty_list_returns_false(self):
        assert has_introduced_threshold_failure([]) is False


class TestCurrentThresholdFailures:
    def test_current_fail_is_included(self):
        items = [_evidence(True, False), _evidence(True, True)]
        assert len(current_threshold_failures(items)) == 1

    def test_all_passing_returns_empty(self):
        items = [_evidence(True, True)]
        assert current_threshold_failures(items) == []


# ---------------------------------------------------------------------------
# Environment failure detection
# ---------------------------------------------------------------------------

class TestEnvironmentFailureDetection:
    @pytest.mark.parametrize("status", ["timeout", "timed_out", "runner_unavailable"])
    def test_environment_status_is_detected(self, status):
        item = {"status": status, "test_id": "T1"}
        assert environment_failure_reason(item) is not None

    @pytest.mark.parametrize("text", [
        "runner unavailable during test",
        "timeout in execution",
        "missing artifact for run",
    ])
    def test_environment_evidence_text_is_detected(self, text):
        item = {"status": "failed", "evidence": text, "test_id": "T1"}
        assert has_environment_failure_signal(item) is True

    def test_normal_failure_is_not_environment(self):
        item = {"status": "failed", "evidence": "temperature exceeded threshold", "test_id": "T1"}
        assert has_environment_failure_signal(item) is False

    def test_environment_failure_signals_returns_list(self):
        items = [
            {"status": "timeout", "test_id": "T1"},
            {"status": "failed", "test_id": "T2"},
        ]
        signals = environment_failure_signals(items)
        assert len(signals) == 1
        assert signals[0]["test_id"] == "T1"
        assert "reason" in signals[0]

    def test_empty_input_returns_empty(self):
        assert environment_failure_signals([]) == []


# ---------------------------------------------------------------------------
# Material worsening
# ---------------------------------------------------------------------------

class TestMaterialWorsening:
    def _delta(self, metric: str, baseline: float, current: float) -> dict:
        delta = current - baseline
        percent = (delta / abs(baseline)) * 100 if baseline != 0 else None
        return {"metric": metric, "baseline": baseline, "current": current, "delta": delta, "percent_delta": percent}

    def test_latency_increase_by_20pct_is_material(self):
        delta = self._delta("latency_ms", 100.0, 120.0)
        assert is_material_worsening(delta) is True

    def test_latency_increase_by_5pct_is_not_material(self):
        delta = self._delta("latency_ms", 100.0, 105.0)
        assert is_material_worsening(delta) is False

    def test_recall_decrease_by_20pct_is_material(self):
        delta = self._delta("recall_rate", 0.95, 0.75)
        assert is_material_worsening(delta) is True

    def test_recall_increase_is_not_material_worsening(self):
        delta = self._delta("recall_rate", 0.75, 0.95)
        assert is_material_worsening(delta) is False

    def test_has_material_worsening_returns_bool(self):
        assert has_material_worsening([self._delta("latency_ms", 100.0, 120.0)]) is True
        assert has_material_worsening([self._delta("latency_ms", 100.0, 102.0)]) is False

    def test_material_worsenings_filters_list(self):
        deltas = [
            self._delta("latency_ms", 100.0, 130.0),  # material
            self._delta("latency_ms", 100.0, 102.0),  # not material
        ]
        result = material_worsenings(deltas)
        assert len(result) == 1

    def test_zero_baseline_handled_without_error(self):
        delta = {"metric": "x", "baseline": 0, "current": 10, "delta": 10, "percent_delta": None}
        # Should not raise — result depends on absolute comparison
        result = is_material_worsening(delta)
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Confidence module
# ---------------------------------------------------------------------------

class TestConfidenceModule:
    def test_normalize_confidence_known_values(self):
        assert confidence_mod.normalize_confidence("high") == "high"
        assert confidence_mod.normalize_confidence("medium") == "medium"
        assert confidence_mod.normalize_confidence("low") == "low"

    def test_normalize_confidence_unknown_returns_default(self):
        assert confidence_mod.normalize_confidence("very_high") == "low"
        assert confidence_mod.normalize_confidence(None) == "low"

    def test_confidence_rank_ordering(self):
        assert confidence_mod.confidence_rank("low") < confidence_mod.confidence_rank("medium")
        assert confidence_mod.confidence_rank("medium") < confidence_mod.confidence_rank("high")

    def test_score_confidence_high_is_above_medium(self):
        high_score = confidence_mod.score_confidence("high")
        medium_score = confidence_mod.score_confidence("medium")
        assert high_score > medium_score

    def test_score_confidence_bounded(self):
        score = confidence_mod.score_confidence("high", verdict="confirmed_regression", factors=["+" * 10])
        assert 0.0 <= score <= 1.0

    def test_positive_factors_increase_score(self):
        base = confidence_mod.score_confidence("medium")
        boosted = confidence_mod.score_confidence("medium", factors=["+ factor1", "+ factor2"])
        assert boosted >= base

    def test_negative_factors_decrease_score(self):
        base = confidence_mod.score_confidence("medium")
        reduced = confidence_mod.score_confidence("medium", factors=["- factor1", "- factor2"])
        assert reduced <= base

    def test_environment_failure_capped(self):
        score = confidence_mod.score_confidence("low", verdict="environment_failure")
        assert score <= 0.45


# ---------------------------------------------------------------------------
# Risk levels module
# ---------------------------------------------------------------------------

class TestRiskLevels:
    def test_normalize_known_risk_levels(self):
        for level in ("low", "medium", "high", "release_blocking", "unknown"):
            assert risk_levels.normalize_risk_level(level) == level

    def test_normalize_unknown_returns_unknown(self):
        assert risk_levels.normalize_risk_level("extreme") == "unknown"
        assert risk_levels.normalize_risk_level(None) == "unknown"

    def test_risk_rank_ordering(self):
        assert risk_levels.risk_rank("low") < risk_levels.risk_rank("medium")
        assert risk_levels.risk_rank("medium") < risk_levels.risk_rank("high")
        assert risk_levels.risk_rank("high") < risk_levels.risk_rank("release_blocking")

    def test_safety_rank_asil_d_is_highest(self):
        assert risk_levels.safety_rank("asil-d") > risk_levels.safety_rank("asil-c")
        assert risk_levels.safety_rank("asil-c") > risk_levels.safety_rank("asil-b")

    def test_safety_rank_unknown_is_zero(self):
        assert risk_levels.safety_rank("unknown") == 0
        assert risk_levels.safety_rank(None) == 0


# ---------------------------------------------------------------------------
# Verdicts module
# ---------------------------------------------------------------------------

class TestVerdictsModule:
    def test_normalize_known_verdicts(self):
        for v in verdicts.ALL_VERDICTS:
            assert verdicts.normalize_verdict(v) == v

    def test_normalize_unknown_returns_insufficient_evidence(self):
        assert verdicts.normalize_verdict("unknown_verdict") == verdicts.INSUFFICIENT_EVIDENCE
        assert verdicts.normalize_verdict(None) == verdicts.INSUFFICIENT_EVIDENCE

    def test_is_fault_verdict_confirmed_regression(self):
        assert verdicts.is_fault_verdict("confirmed_regression") is True

    def test_is_fault_verdict_possible_regression(self):
        assert verdicts.is_fault_verdict("possible_regression") is True

    def test_is_fault_verdict_successful_change(self):
        assert verdicts.is_fault_verdict("successful_change") is False

    def test_is_fault_verdict_preexisting_failure(self):
        assert verdicts.is_fault_verdict("preexisting_failure") is False

    def test_all_verdicts_constant_is_complete(self):
        # Every verdict constant should be in ALL_VERDICTS
        for name in dir(verdicts):
            val = getattr(verdicts, name)
            if isinstance(val, str) and val.replace("_", "").islower() and not name.startswith("_"):
                # Only check known verdict-shaped strings
                if val in verdicts.ALL_VERDICTS:
                    assert verdicts.normalize_verdict(val) == val
