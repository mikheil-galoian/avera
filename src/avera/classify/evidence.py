"""Evidence taxonomy and helpers for AVERA classification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

BASELINE_CURRENT_COMPARISON = "baseline_current_comparison"
THRESHOLD_EVALUATION = "threshold_evaluation"
REQUIREMENT_MAPPING = "requirement_mapping"
COMPONENT_MAPPING = "component_mapping"
MISSING_BASELINE = "missing_baseline"
ENVIRONMENT_SIGNAL = "environment_signal"
MATERIAL_WORSENING = "material_worsening"

ALL_EVIDENCE_TYPES = (
    BASELINE_CURRENT_COMPARISON,
    THRESHOLD_EVALUATION,
    REQUIREMENT_MAPPING,
    COMPONENT_MAPPING,
    MISSING_BASELINE,
    ENVIRONMENT_SIGNAL,
    MATERIAL_WORSENING,
)

ENVIRONMENT_FAILURE_REASONS = (
    "timeout",
    "missing_artifact",
    "unavailable_runner",
    "corrupt_log",
    "sensor_stream_lost",
)

ENVIRONMENT_STATUS_PATTERNS = {
    "timeout": ("timeout", "timed_out", "timed-out"),
    "missing_artifact": ("missing_artifact", "artifact_missing", "no_artifact"),
    "unavailable_runner": ("runner_unavailable", "unavailable_runner", "runner_offline"),
    "corrupt_log": ("corrupt_log", "log_corrupt", "malformed_log"),
    "sensor_stream_lost": ("sensor_stream_lost", "sensor-lost", "stream_lost"),
}

ENVIRONMENT_EVIDENCE_PATTERNS = {
    "timeout": ("timeout", "timed out", "deadline exceeded", "execution expired"),
    "missing_artifact": ("missing artifact", "artifact missing", "artifact not found", "no artifact"),
    "unavailable_runner": (
        "runner unavailable",
        "unavailable runner",
        "unavailable",
        "runner offline",
        "no runner available",
        "executor unavailable",
        "bench unavailable",
    ),
    "corrupt_log": ("corrupt log", "log corrupt", "malformed log", "unparseable log", "invalid log"),
    "sensor_stream_lost": (
        "sensor stream lost",
        "sensor stream disconnected",
        "stream lost",
        "telemetry stream lost",
    ),
}

DEFAULT_MATERIAL_PERCENT_DELTA = 10.0
LOWER_IS_BETTER_METRIC_HINTS = (
    "error",
    "fail",
    "failure",
    "latency",
    "duration",
    "time",
    "cost",
    "memory",
    "cpu",
    "jitter",
)
HIGHER_IS_BETTER_METRIC_HINTS = (
    "accuracy",
    "coverage",
    "precision",
    "recall",
    "success",
    "throughput",
    "score",
)


@dataclass(frozen=True)
class ThresholdEvidence:
    requirement_id: str
    metric: str
    operator: str
    threshold: float
    baseline_value: float | None
    current_value: float | None
    baseline_passed: bool | None
    current_passed: bool | None
    test_id: str


def introduced_threshold_failures(
    threshold_evidence: Iterable[ThresholdEvidence],
) -> list[ThresholdEvidence]:
    """Evidence where baseline passed and current failed the same threshold."""

    return [
        item for item in threshold_evidence
        if item.baseline_passed is True and item.current_passed is False
    ]


def current_threshold_failures(
    threshold_evidence: Iterable[ThresholdEvidence],
) -> list[ThresholdEvidence]:
    """Evidence where current results fail a requirement threshold."""

    return [item for item in threshold_evidence if item.current_passed is False]


def has_introduced_threshold_failure(threshold_evidence: Iterable[ThresholdEvidence]) -> bool:
    """Return whether there is proof of baseline-pass/current-fail threshold evidence."""

    return bool(introduced_threshold_failures(threshold_evidence))


def environment_failure_reason(item: Any) -> str | None:
    """Return the matched environment reason for a status/evidence-shaped item."""

    status = _normalized_text(_get(item, "current_status", default=_get(item, "status")))
    for reason, patterns in ENVIRONMENT_STATUS_PATTERNS.items():
        if status in patterns:
            return reason

    haystack = " ".join(_evidence_texts(item)).lower()
    for reason, patterns in ENVIRONMENT_EVIDENCE_PATTERNS.items():
        if any(pattern in haystack for pattern in patterns):
            return reason
    return None


def has_environment_failure_signal(item: Any) -> bool:
    """Return whether a single test/comparison carries environment-failure evidence."""

    return environment_failure_reason(item) is not None


def environment_failure_signals(items: Iterable[Any]) -> list[dict[str, str]]:
    """Return environment-failure matches from status and evidence patterns."""

    signals: list[dict[str, str]] = []
    for item in items:
        reason = environment_failure_reason(item)
        if not reason:
            continue
        signals.append(
            {
                "test_id": str(_get(item, "test_id", default=_get(item, "id", default="unknown-test"))),
                "reason": reason,
            }
        )
    return signals


def is_material_worsening(
    delta: Any,
    *,
    percent_threshold: float = DEFAULT_MATERIAL_PERCENT_DELTA,
    absolute_threshold: float | None = None,
    higher_is_better: bool | None = None,
) -> bool:
    """Return whether a metric delta is directionally worse and large enough."""

    metric = str(_get(delta, "metric", default="")).lower()
    raw_delta = _number(_get(delta, "delta"))
    if raw_delta is None:
        baseline = _number(_get(delta, "baseline", default=_get(delta, "baseline_value")))
        current = _number(_get(delta, "current", default=_get(delta, "current_value")))
        if baseline is None or current is None:
            return False
        raw_delta = current - baseline

    direction_higher_is_better = _higher_is_better(metric, higher_is_better)
    worsening_delta = -raw_delta if direction_higher_is_better else raw_delta
    if worsening_delta <= 0:
        return False

    if absolute_threshold is not None and worsening_delta >= absolute_threshold:
        return True

    percent_delta = _number(_get(delta, "percent_delta"))
    if percent_delta is None:
        baseline = _number(_get(delta, "baseline", default=_get(delta, "baseline_value")))
        percent_delta = None if baseline in (None, 0) else (raw_delta / abs(baseline)) * 100
    if percent_delta is None:
        return absolute_threshold is None and worsening_delta > 0

    worsening_percent = -percent_delta if direction_higher_is_better else percent_delta
    return worsening_percent >= percent_threshold


def material_worsenings(
    metric_deltas: Iterable[Any],
    *,
    percent_threshold: float = DEFAULT_MATERIAL_PERCENT_DELTA,
    absolute_threshold: float | None = None,
) -> list[Any]:
    """Return metric deltas with material worse movement."""

    return [
        delta for delta in metric_deltas
        if is_material_worsening(
            delta,
            percent_threshold=percent_threshold,
            absolute_threshold=absolute_threshold,
        )
    ]


def has_material_worsening(metric_deltas: Iterable[Any]) -> bool:
    """Return whether any metric delta materially worsened."""

    return bool(material_worsenings(metric_deltas))


def _higher_is_better(metric: str, explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    if any(hint in metric for hint in HIGHER_IS_BETTER_METRIC_HINTS):
        return True
    if any(hint in metric for hint in LOWER_IS_BETTER_METRIC_HINTS):
        return False
    return False


def _evidence_texts(item: Any) -> list[str]:
    values: list[str] = []
    for key in ("evidence", "message", "reason", "error", "details"):
        value = _get(item, key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list | tuple | set):
            values.extend(str(part) for part in value)
    return values


def _normalized_text(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


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
