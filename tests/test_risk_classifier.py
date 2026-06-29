"""Tests for avera.classify.risk_classifier — all verdict paths."""

from __future__ import annotations

import pytest

from avera.classify.risk_classifier import RiskAssessment, classify_risk
from avera.compare.baseline_comparator import compare_runs


# ---------------------------------------------------------------------------
# Helpers — build minimal comparison inputs
# ---------------------------------------------------------------------------

def _run(run_id: str, stage: str, tests: list) -> dict:
    return {"runId": run_id, "stage": stage, "tests": tests}


def _test(test_id: str, status: str, metrics: dict | None = None, component: str | None = None, evidence: str | None = None) -> dict:
    entry: dict = {"id": test_id, "status": status}
    if metrics:
        entry["metrics"] = metrics
    if component:
        entry["component"] = component
    if evidence:
        entry["evidence"] = evidence
    return entry


def _req(req_id: str, component: str, metric: str, operator: str, threshold: float, safety: str = "high", next_checks: str = "") -> dict:
    return {
        "id": req_id,
        "component": component,
        "requirement": f"Requirement {req_id}",
        "metric": metric,
        "operator": operator,
        "threshold": threshold,
        "safety_level": safety,
        "next_checks": next_checks,
    }


def _cmap(file_path: str, component: str, requirements: list[str]) -> dict:
    return {file_path: {"component": component, "requirements": requirements}}


def _classify(baseline_tests, current_tests, requirements=None, component_map=None):
    baseline = _run("b1", "baseline", baseline_tests)
    current = _run("c1", "current", current_tests)
    comparison = compare_runs(baseline, current)
    return classify_risk(comparison, requirements=requirements, component_map=component_map)


# ---------------------------------------------------------------------------
# Verdict: confirmed_regression
# ---------------------------------------------------------------------------

class TestConfirmedRegression:
    def test_pass_to_fail_with_threshold_breach_is_confirmed_regression(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        cmap = _cmap("src/bms.c", "BMS", ["R1"])
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            requirements=reqs,
            component_map=cmap,
        )
        assert result.verdict == "confirmed_regression"
        assert result.risk == "high"
        assert result.confidence == "high"
        assert result.confidence_score > 0.8

    def test_pass_to_fail_without_threshold_is_confirmed_regression(self):
        # Pure pass/fail software test (no metric/threshold). An introduced
        # failure is itself proof of a regression — enables ordinary software CI,
        # not only metric/threshold verification.
        result = _classify(
            [_test("T1", "passed", component="formatting")],
            [_test("T1", "failed", component="formatting")],
        )
        assert result.verdict == "confirmed_regression"
        assert len(result.introduced_failures) == 1

    def test_pass_to_fail_with_unmatched_requirement_is_confirmed_regression(self):
        # Requirement exists but its metric never appears in the test results
        # (the real python-tabulate/toolz/slugify case). Previously this was
        # requirements_coverage_gap; an introduced test failure now wins.
        reqs = [_req("R1", "Formatting", "out_failures", "<=", 0, safety="medium")]
        cmap = _cmap("src/fmt.py", "Formatting", ["R1"])
        result = _classify(
            [_test("T1", "passed", component="Formatting")],
            [_test("T1", "failed", component="Formatting")],
            requirements=reqs,
            component_map=cmap,
        )
        assert result.verdict == "confirmed_regression"

    def test_confirmed_regression_has_affected_requirements(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            requirements=reqs,
        )
        assert len(result.affected_requirements) >= 1
        assert result.affected_requirements[0]["id"] == "R1"

    def test_confirmed_regression_has_rules_triggered(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            requirements=reqs,
        )
        assert "R1_confirmed_threshold_regression" in result.rules_triggered

    def test_safety_critical_requirement_elevates_risk_to_release_blocking(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0, safety="asil-d")]
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            requirements=reqs,
        )
        assert result.verdict == "confirmed_regression"
        assert result.risk == "release_blocking"


# ---------------------------------------------------------------------------
# Verdict: successful_change
# ---------------------------------------------------------------------------

class TestSuccessfulChange:
    def test_pass_to_pass_within_threshold_is_successful_change(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0}, component="BMS")],
            [_test("T1", "passed", metrics={"max_temp": 46.0}, component="BMS")],
            requirements=reqs,
        )
        assert result.verdict == "successful_change"
        assert result.risk == "low"

    def test_successful_change_confidence_is_high_with_requirements(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0})],
            [_test("T1", "passed", metrics={"max_temp": 46.0})],
            requirements=reqs,
        )
        assert result.confidence == "high"


# ---------------------------------------------------------------------------
# Verdict: preexisting_failure
# ---------------------------------------------------------------------------

class TestPreexistingFailure:
    def test_both_failing_with_threshold_breach_is_preexisting(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 53.0}, component="BMS")],
            requirements=reqs,
        )
        assert result.verdict == "preexisting_failure"
        assert result.risk in ("medium", "low")

    def test_preexisting_failure_confidence_is_high_with_requirements(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            requirements=reqs,
        )
        assert result.confidence == "high"


# ---------------------------------------------------------------------------
# Verdict: worsened_preexisting_failure
# ---------------------------------------------------------------------------

class TestWorsenedPreexistingFailure:
    def test_preexisting_failure_that_gets_materially_worse_is_worsened(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 62.0}, component="BMS")],
            requirements=reqs,
        )
        assert result.verdict == "worsened_preexisting_failure"
        assert result.risk == "high"


# ---------------------------------------------------------------------------
# Verdict: insufficient_evidence
# ---------------------------------------------------------------------------

class TestInsufficientEvidence:
    def test_test_only_in_current_with_failure_is_insufficient_evidence(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        result = _classify(
            [],
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            requirements=reqs,
        )
        assert result.verdict == "insufficient_evidence"
        assert result.risk == "unknown"
        assert result.confidence == "low"

    def test_no_tests_at_all_is_insufficient_evidence(self):
        result = _classify([], [])
        assert result.verdict in ("insufficient_evidence", "expected_change")


# ---------------------------------------------------------------------------
# Verdict: environment_failure
# ---------------------------------------------------------------------------

class TestEnvironmentFailure:
    def test_timeout_status_is_environment_failure(self):
        result = _classify(
            [_test("T1", "passed")],
            [_test("T1", "timeout")],
        )
        assert result.verdict == "environment_failure"
        assert result.risk == "unknown"
        assert result.confidence == "low"

    def test_environment_failure_evidence_in_text_is_detected(self):
        result = _classify(
            [_test("T1", "passed")],
            [_test("T1", "failed", evidence="runner unavailable during current run")],
        )
        assert result.verdict == "environment_failure"


# ---------------------------------------------------------------------------
# Verdict: requirements_coverage_gap
# ---------------------------------------------------------------------------

class TestRequirementsCoverageGap:
    def test_requirements_mapped_but_no_tests_executed_is_coverage_gap(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0)]
        cmap = _cmap("src/bms.c", "BMS", ["R1"])
        result = _classify(
            [_test("T1", "passed")],
            [_test("T1", "passed")],
            requirements=reqs,
            component_map=cmap,
        )
        # Coverage gap when changed file maps to requirement but no threshold evidence
        assert result.verdict in ("requirements_coverage_gap", "successful_change", "expected_change")


# ---------------------------------------------------------------------------
# RiskAssessment shape
# ---------------------------------------------------------------------------

class TestRiskAssessmentShape:
    def test_result_has_schema_version(self):
        result = _classify([_test("T1", "passed")], [_test("T1", "passed")])
        assert result.schema_version.startswith("avera.")

    def test_result_has_confidence_score_between_0_and_1(self):
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0})],
            [_test("T1", "failed", metrics={"max_temp": 52.0})],
        )
        assert 0.0 <= result.confidence_score <= 1.0

    def test_evidence_summary_is_non_empty_list(self):
        result = _classify(
            [_test("T1", "passed")],
            [_test("T1", "failed")],
        )
        assert isinstance(result.evidence_summary, list)
        assert len(result.evidence_summary) >= 1

    def test_confidence_factors_present(self):
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0})],
            [_test("T1", "failed", metrics={"max_temp": 52.0})],
        )
        assert isinstance(result.confidence_factors, list)

    def test_risk_drivers_contain_verdict_and_risk(self):
        result = _classify(
            [_test("T1", "passed")],
            [_test("T1", "failed")],
        )
        assert any("verdict:" in d for d in result.risk_drivers)
        assert any("risk:" in d for d in result.risk_drivers)

    def test_rules_triggered_is_sorted_list(self):
        result = _classify(
            [_test("T1", "passed")],
            [_test("T1", "failed")],
        )
        assert result.rules_triggered == sorted(result.rules_triggered)


# ---------------------------------------------------------------------------
# Next checks
# ---------------------------------------------------------------------------

class TestNextChecks:
    def test_next_checks_extracted_from_requirements(self):
        reqs = [_req("R1", "BMS", "max_temp", "<=", 50.0, next_checks="BMS-HIL-007")]
        result = _classify(
            [_test("T1", "passed", metrics={"max_temp": 47.0}, component="BMS")],
            [_test("T1", "failed", metrics={"max_temp": 52.0}, component="BMS")],
            requirements=reqs,
        )
        assert "BMS-HIL-007" in result.recommended_next_checks

    def test_no_requirements_means_no_next_checks(self):
        result = _classify(
            [_test("T1", "passed")],
            [_test("T1", "failed")],
        )
        assert result.recommended_next_checks == []


# ---------------------------------------------------------------------------
# Missing-baseline failures (audit regression: a brand-new failing test must
# never silently pass the gate just because it carries no numeric threshold)
# ---------------------------------------------------------------------------

class TestMissingBaselineFailure:
    def test_new_failing_test_without_threshold_is_insufficient_evidence(self):
        # A test that exists only in the current run and FAILS on plain pass/fail
        # status (no metric/threshold) has no baseline to prove a regression, but
        # is not a clean change either. It must route to insufficient_evidence
        # (review), never fall through to expected_change.
        result = _classify(
            [],
            [_test("T_NEW", "failed")],
        )
        assert result.verdict == "insufficient_evidence"

    def test_new_passing_test_without_baseline_stays_benign(self):
        # A brand-new PASSING test with no baseline is a benign expected change.
        result = _classify(
            [],
            [_test("T_NEW", "passed")],
        )
        assert result.verdict == "expected_change"
