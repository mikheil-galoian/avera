"""Tests for avera.compare.baseline_comparator."""

from __future__ import annotations

import pytest

from avera.compare.baseline_comparator import (
    ComparisonResult,
    MetricDelta,
    TestComparison,
    compare_runs,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(run_id: str, stage: str, tests: list) -> dict:
    return {"runId": run_id, "stage": stage, "tests": tests}


def _test(test_id: str, status: str, metrics: dict | None = None, component: str | None = None) -> dict:
    entry: dict = {"id": test_id, "status": status}
    if metrics:
        entry["metrics"] = metrics
    if component:
        entry["component"] = component
    return entry


# ---------------------------------------------------------------------------
# Basic classification paths
# ---------------------------------------------------------------------------

class TestIntroducedFailure:
    def test_passing_baseline_failing_current_is_introduced(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed")])
        current = _run("c1", "current", [_test("T1", "failed")])
        result = compare_runs(baseline, current)
        assert len(result.introduced_failures) == 1
        assert result.introduced_failures[0].test_id == "T1"
        assert result.introduced_failures[0].classification == "introduced_failure"

    def test_summary_counts_introduced_correctly(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed"), _test("T2", "passed")])
        current = _run("c1", "current", [_test("T1", "failed"), _test("T2", "passed")])
        result = compare_runs(baseline, current)
        assert result.summary["introduced_failures"] == 1
        assert result.summary["unchanged_passes"] == 1


class TestPreexistingFailure:
    def test_failing_baseline_and_current_is_preexisting(self):
        baseline = _run("b1", "baseline", [_test("T1", "failed")])
        current = _run("c1", "current", [_test("T1", "failed")])
        result = compare_runs(baseline, current)
        assert len(result.preexisting_failures) == 1
        assert result.preexisting_failures[0].classification == "preexisting_failure"

    def test_no_introduced_failures_when_preexisting(self):
        baseline = _run("b1", "baseline", [_test("T1", "failed")])
        current = _run("c1", "current", [_test("T1", "failed")])
        result = compare_runs(baseline, current)
        assert len(result.introduced_failures) == 0


class TestResolvedFailure:
    def test_failing_baseline_passing_current_is_resolved(self):
        baseline = _run("b1", "baseline", [_test("T1", "failed")])
        current = _run("c1", "current", [_test("T1", "passed")])
        result = compare_runs(baseline, current)
        assert len(result.resolved_failures) == 1
        assert result.resolved_failures[0].classification == "resolved_failure"


class TestUnchangedPass:
    def test_both_passing_is_unchanged_pass(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed")])
        current = _run("c1", "current", [_test("T1", "passed")])
        result = compare_runs(baseline, current)
        assert len(result.unchanged_passes) == 1
        assert result.unchanged_passes[0].classification == "unchanged_pass"


class TestMissingBaseline:
    def test_test_only_in_current_is_missing_baseline(self):
        baseline = _run("b1", "baseline", [])
        current = _run("c1", "current", [_test("T1", "failed")])
        result = compare_runs(baseline, current)
        assert len(result.missing_baseline) == 1
        assert result.missing_baseline[0].classification == "missing_baseline"


class TestMissingCurrent:
    def test_test_only_in_baseline_is_missing_current(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed")])
        current = _run("c1", "current", [])
        result = compare_runs(baseline, current)
        assert len(result.missing_current) == 1
        assert result.missing_current[0].classification == "missing_current"


# ---------------------------------------------------------------------------
# Status normalization
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["pass", "passed", "ok", "success", "successful"])
def test_pass_status_variants_recognized(status):
    baseline = _run("b1", "baseline", [_test("T1", status)])
    current = _run("c1", "current", [_test("T1", "failed")])
    result = compare_runs(baseline, current)
    assert result.introduced_failures[0].classification == "introduced_failure"


@pytest.mark.parametrize("status", ["fail", "failed", "failure", "error", "errored", "timeout"])
def test_fail_status_variants_recognized(status):
    baseline = _run("b1", "baseline", [_test("T1", "passed")])
    current = _run("c1", "current", [_test("T1", status)])
    result = compare_runs(baseline, current)
    assert result.introduced_failures[0].classification == "introduced_failure"


# ---------------------------------------------------------------------------
# Metric deltas
# ---------------------------------------------------------------------------

class TestMetricDeltas:
    def test_numeric_metric_delta_is_computed(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed", metrics={"latency_ms": 100})])
        current = _run("c1", "current", [_test("T1", "passed", metrics={"latency_ms": 150})])
        result = compare_runs(baseline, current)
        assert len(result.metric_deltas) == 1
        delta = result.metric_deltas[0]
        assert delta.test_id == "T1"
        assert delta.metric == "latency_ms"
        assert delta.baseline == 100.0
        assert delta.current == 150.0
        assert delta.delta == 50.0

    def test_percent_delta_computed_for_nonzero_baseline(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed", metrics={"temp": 50.0})])
        current = _run("c1", "current", [_test("T1", "passed", metrics={"temp": 55.0})])
        result = compare_runs(baseline, current)
        assert result.metric_deltas[0].percent_delta == pytest.approx(10.0)

    def test_percent_delta_is_none_for_zero_baseline(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed", metrics={"x": 0})])
        current = _run("c1", "current", [_test("T1", "passed", metrics={"x": 5})])
        result = compare_runs(baseline, current)
        assert result.metric_deltas[0].percent_delta is None

    def test_metrics_not_in_both_runs_are_ignored(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed", metrics={"a": 1})])
        current = _run("c1", "current", [_test("T1", "passed", metrics={"b": 2})])
        result = compare_runs(baseline, current)
        assert result.metric_deltas == []


# ---------------------------------------------------------------------------
# Run IDs and empty runs
# ---------------------------------------------------------------------------

class TestRunIds:
    def test_run_ids_are_preserved(self):
        baseline = _run("baseline-001", "baseline", [])
        current = _run("current-001", "current", [])
        result = compare_runs(baseline, current)
        assert result.baseline_run_id == "baseline-001"
        assert result.current_run_id == "current-001"

    def test_empty_runs_produce_empty_result(self):
        result = compare_runs(_run("b", "baseline", []), _run("c", "current", []))
        assert result.summary["total_tests"] == 0
        assert result.introduced_failures == []
        assert result.preexisting_failures == []

    def test_run_id_from_snake_case_key(self):
        baseline = {"run_id": "b1", "stage": "baseline", "tests": []}
        current = {"run_id": "c1", "stage": "current", "tests": []}
        result = compare_runs(baseline, current)
        assert result.baseline_run_id == "b1"


# ---------------------------------------------------------------------------
# Multiple tests in a single run
# ---------------------------------------------------------------------------

class TestMultipleTests:
    def test_mixed_results_are_classified_independently(self):
        baseline = _run("b1", "baseline", [
            _test("T1", "passed"),
            _test("T2", "failed"),
            _test("T3", "passed"),
        ])
        current = _run("c1", "current", [
            _test("T1", "failed"),   # introduced
            _test("T2", "failed"),   # preexisting
            _test("T3", "passed"),   # unchanged
        ])
        result = compare_runs(baseline, current)
        assert result.summary["introduced_failures"] == 1
        assert result.summary["preexisting_failures"] == 1
        assert result.summary["unchanged_passes"] == 1

    def test_component_is_carried_from_current_test(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed")])
        current = _run("c1", "current", [_test("T1", "failed", component="BMS Thermal Control")])
        result = compare_runs(baseline, current)
        assert result.introduced_failures[0].component == "BMS Thermal Control"

    def test_summary_total_tests_matches_union(self):
        baseline = _run("b1", "baseline", [_test("T1", "passed"), _test("T2", "passed")])
        current = _run("c1", "current", [_test("T2", "failed"), _test("T3", "failed")])
        result = compare_runs(baseline, current)
        assert result.summary["total_tests"] == 3  # T1, T2, T3


# ---------------------------------------------------------------------------
# Evidence preservation
# ---------------------------------------------------------------------------

class TestEvidence:
    def test_evidence_field_is_included_in_comparison(self):
        baseline = _run("b1", "baseline", [{"id": "T1", "status": "passed"}])
        current = _run("c1", "current", [{"id": "T1", "status": "failed", "evidence": "threshold exceeded"}])
        result = compare_runs(baseline, current)
        comparison = result.introduced_failures[0]
        assert any("threshold exceeded" in line for line in comparison.evidence)
