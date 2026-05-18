"""Baseline-to-current verification comparison for AVERA.

The comparator intentionally stays schema-tolerant. It accepts dictionaries,
dataclasses, or simple objects shaped like the JSON fixtures described in the
AVERA docs and returns a plain dataclass that downstream classifiers and
reporters can serialize without external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PASS_STATUSES = {"pass", "passed", "ok", "success", "successful"}
FAIL_STATUSES = {"fail", "failed", "failure", "error", "errored", "timeout"}


@dataclass(frozen=True)
class MetricDelta:
    """Numeric metric movement between baseline and current runs."""

    test_id: str
    metric: str
    baseline: float
    current: float
    delta: float
    percent_delta: float | None


@dataclass(frozen=True)
class TestComparison:
    """Status and metric comparison for a single test."""

    test_id: str
    component: str | None
    baseline_status: str | None
    current_status: str | None
    classification: str
    baseline_metrics: dict[str, Any] = field(default_factory=dict)
    current_metrics: dict[str, Any] = field(default_factory=dict)
    metric_deltas: list[MetricDelta] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComparisonResult:
    """Aggregate result of comparing a baseline run with a current run."""

    baseline_run_id: str | None
    current_run_id: str | None
    tests: list[TestComparison]
    introduced_failures: list[TestComparison]
    preexisting_failures: list[TestComparison]
    resolved_failures: list[TestComparison]
    missing_baseline: list[TestComparison]
    missing_current: list[TestComparison]
    unchanged_passes: list[TestComparison]
    metric_deltas: list[MetricDelta]
    summary: dict[str, int]


def compare_runs(baseline: Any, current: Any) -> ComparisonResult:
    """Compare baseline and current verification runs.

    Expected run shape is compatible with:

    ```python
    {"runId": "...", "tests": [{"id": "...", "status": "passed", "metrics": {}}]}
    ```

    Unknown fields are ignored, while `evidence`/`message` fields are preserved
    in per-test evidence where present.
    """

    baseline_tests = _index_tests(_get(baseline, "tests", default=[]))
    current_tests = _index_tests(_get(current, "tests", default=[]))

    comparisons: list[TestComparison] = []
    introduced: list[TestComparison] = []
    preexisting: list[TestComparison] = []
    resolved: list[TestComparison] = []
    missing_baseline: list[TestComparison] = []
    missing_current: list[TestComparison] = []
    unchanged_passes: list[TestComparison] = []
    all_deltas: list[MetricDelta] = []

    for test_id in sorted(set(baseline_tests) | set(current_tests)):
        baseline_test = baseline_tests.get(test_id)
        current_test = current_tests.get(test_id)

        baseline_status = _status(baseline_test)
        current_status = _status(current_test)
        baseline_metrics = _metrics(baseline_test)
        current_metrics = _metrics(current_test)
        deltas = _metric_deltas(test_id, baseline_metrics, current_metrics)
        all_deltas.extend(deltas)

        classification = _classify_status(baseline_status, current_status)
        evidence = _evidence(test_id, baseline_test, current_test, deltas, classification)

        comparison = TestComparison(
            test_id=test_id,
            component=_first_present(
                _get(current_test, "component"),
                _get(baseline_test, "component"),
            ),
            baseline_status=baseline_status,
            current_status=current_status,
            classification=classification,
            baseline_metrics=baseline_metrics,
            current_metrics=current_metrics,
            metric_deltas=deltas,
            evidence=evidence,
        )
        comparisons.append(comparison)

        if classification == "introduced_failure":
            introduced.append(comparison)
        elif classification == "preexisting_failure":
            preexisting.append(comparison)
        elif classification == "resolved_failure":
            resolved.append(comparison)
        elif classification == "missing_baseline":
            missing_baseline.append(comparison)
        elif classification == "missing_current":
            missing_current.append(comparison)
        elif classification == "unchanged_pass":
            unchanged_passes.append(comparison)

    summary = {
        "total_tests": len(comparisons),
        "introduced_failures": len(introduced),
        "preexisting_failures": len(preexisting),
        "resolved_failures": len(resolved),
        "missing_baseline": len(missing_baseline),
        "missing_current": len(missing_current),
        "unchanged_passes": len(unchanged_passes),
        "metric_deltas": len(all_deltas),
    }

    return ComparisonResult(
        baseline_run_id=_run_id(baseline),
        current_run_id=_run_id(current),
        tests=comparisons,
        introduced_failures=introduced,
        preexisting_failures=preexisting,
        resolved_failures=resolved,
        missing_baseline=missing_baseline,
        missing_current=missing_current,
        unchanged_passes=unchanged_passes,
        metric_deltas=all_deltas,
        summary=summary,
    )


def _index_tests(tests: Any) -> dict[str, Any]:
    indexed: dict[str, Any] = {}
    if not isinstance(tests, list | tuple):
        return indexed

    for position, test in enumerate(tests, start=1):
        test_id = _first_present(
            _get(test, "id"),
            _get(test, "test_id"),
            _get(test, "name"),
            f"test-{position}",
        )
        indexed[str(test_id)] = test
    return indexed


def _classify_status(baseline_status: str | None, current_status: str | None) -> str:
    baseline_failed = _is_failure(baseline_status)
    current_failed = _is_failure(current_status)
    baseline_passed = _is_pass(baseline_status)
    current_passed = _is_pass(current_status)

    if baseline_status is None and current_status is None:
        return "insufficient_evidence"
    if baseline_status is None:
        return "missing_baseline"
    if current_status is None:
        return "missing_current"
    if baseline_passed and current_failed:
        return "introduced_failure"
    if baseline_failed and current_failed:
        return "preexisting_failure"
    if baseline_failed and current_passed:
        return "resolved_failure"
    if baseline_passed and current_passed:
        return "unchanged_pass"
    if current_failed:
        return "possible_failure"
    return "changed_status"


def _metric_deltas(
    test_id: str,
    baseline_metrics: dict[str, Any],
    current_metrics: dict[str, Any],
) -> list[MetricDelta]:
    deltas: list[MetricDelta] = []
    for metric in sorted(set(baseline_metrics) & set(current_metrics)):
        baseline_value = _number(baseline_metrics[metric])
        current_value = _number(current_metrics[metric])
        if baseline_value is None or current_value is None:
            continue
        delta = current_value - baseline_value
        percent_delta = None if baseline_value == 0 else (delta / abs(baseline_value)) * 100
        deltas.append(
            MetricDelta(
                test_id=test_id,
                metric=metric,
                baseline=baseline_value,
                current=current_value,
                delta=delta,
                percent_delta=percent_delta,
            )
        )
    return deltas


def _evidence(
    test_id: str,
    baseline_test: Any,
    current_test: Any,
    deltas: list[MetricDelta],
    classification: str,
) -> list[str]:
    lines: list[str] = [f"{test_id}: {classification.replace('_', ' ')}."]
    for source in (baseline_test, current_test):
        item = _first_present(_get(source, "evidence"), _get(source, "message"))
        if item:
            lines.append(str(item))
    for delta in deltas:
        direction = "increased" if delta.delta > 0 else "decreased" if delta.delta < 0 else "was unchanged"
        lines.append(
            f"{delta.metric} {direction} from {delta.baseline:g} to {delta.current:g}."
        )
    return lines


def _run_id(run: Any) -> str | None:
    value = _first_present(_get(run, "runId"), _get(run, "run_id"), _get(run, "id"))
    return None if value is None else str(value)


def _metrics(test: Any) -> dict[str, Any]:
    metrics = _get(test, "metrics", default={})
    return dict(metrics) if isinstance(metrics, dict) else {}


def _status(test: Any) -> str | None:
    value = _get(test, "status")
    return None if value is None else str(value).strip().lower()


def _is_pass(status: str | None) -> bool:
    return status in PASS_STATUSES


def _is_failure(status: str | None) -> bool:
    return status in FAIL_STATUSES


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _get(item: Any, key: str, default: Any = None) -> Any:
    if item is None:
        return default
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None
