"""Conservative regression and risk classification for AVERA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..compare.baseline_comparator import status_severity
from . import confidence as confidence_levels
from . import risk_levels, verdicts
from .evidence import (
    ThresholdEvidence,
    current_threshold_failures,
    environment_failure_signals,
    has_material_worsening,
    has_introduced_threshold_failure,
    introduced_threshold_failures,
    material_worsenings,
)


@dataclass(frozen=True)
class RiskAssessment:
    verdict: str
    risk: str
    confidence: str
    schema_version: str = "avera.assessment.v0.2"
    confidence_score: float = 0.0
    affected_requirements: list[dict[str, Any]] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    introduced_failures: list[Any] = field(default_factory=list)
    preexisting_failures: list[Any] = field(default_factory=list)
    threshold_evidence: list[ThresholdEvidence] = field(default_factory=list)
    evidence_summary: list[str] = field(default_factory=list)
    recommended_next_checks: list[str] = field(default_factory=list)
    comparison_summary: dict[str, int] = field(default_factory=dict)
    rules_triggered: list[str] = field(default_factory=list)
    confidence_factors: list[str] = field(default_factory=list)
    risk_drivers: list[str] = field(default_factory=list)


def classify_risk(
    comparison: Any,
    requirements: Any | None = None,
    component_map: Any | None = None,
) -> RiskAssessment:
    """Classify regression verdict, confidence, and automotive risk.

    The function favors proof-backed classifications:

    - passing baseline to failing current -> `confirmed_regression`
    - failing baseline to failing current -> `preexisting_failure`
    - no baseline/current pairing -> `insufficient_evidence`
    - current failures without strong baseline proof -> `possible_regression`
    """

    reqs = _normalize_requirements(requirements)
    reqs_by_metric = _requirements_by_metric(reqs)
    introduced = list(_get(comparison, "introduced_failures", default=[]))
    preexisting = list(_get(comparison, "preexisting_failures", default=[]))
    missing_baseline = list(_get(comparison, "missing_baseline", default=[]))
    tests = list(_get(comparison, "tests", default=[]))
    metric_deltas = _metric_deltas_for(preexisting) or list(_get(comparison, "metric_deltas", default=[]))

    threshold_evidence = _threshold_evidence(tests, reqs_by_metric)
    env_signals = environment_failure_signals(tests)
    worsened_metric_deltas = material_worsenings(metric_deltas)
    affected_requirements = _affected_requirements(reqs, introduced, threshold_evidence)
    coverage_gap = _has_coverage_gap(reqs, threshold_evidence, component_map)
    if not affected_requirements and coverage_gap:
        affected_requirements = reqs
    affected_components = _affected_components(introduced, preexisting, affected_requirements)
    affected_files = _affected_files(component_map, affected_components, affected_requirements)
    next_checks = _next_checks(affected_requirements)

    verdict = _verdict(
        introduced,
        preexisting,
        missing_baseline,
        tests,
        threshold_evidence,
        env_signals,
        worsened_metric_deltas,
        affected_requirements,
        coverage_gap,
    )
    # Fail-closed backstop: an introduced failure (baseline pass -> current fail) can
    # never be reported as a benign/pass-like outcome. If any verdict path tried to
    # do so, escalate to a confirmed regression. (Environment-failure remains a valid
    # explanation and is intentionally not overridden here.)
    if introduced and verdict in {verdicts.SUCCESSFUL_CHANGE, verdicts.EXPECTED_CHANGE}:
        verdict = verdicts.CONFIRMED_REGRESSION
    risk = _risk(verdict, affected_requirements, threshold_evidence, introduced)
    confidence = _confidence(verdict, introduced, threshold_evidence, affected_requirements)
    evidence_summary = _summary(
        verdict=verdict,
        introduced=introduced,
        preexisting=preexisting,
        threshold_evidence=threshold_evidence,
        affected_files=affected_files,
        env_signals=env_signals,
        worsened_metric_deltas=worsened_metric_deltas,
    )
    rules_triggered = _rules_triggered(
        verdict,
        introduced,
        preexisting,
        missing_baseline,
        tests,
        threshold_evidence,
        env_signals,
        worsened_metric_deltas,
    )
    confidence_factors = _confidence_factors(
        verdict,
        introduced,
        preexisting,
        threshold_evidence,
        affected_requirements,
        affected_files,
        env_signals,
        not coverage_gap,
    )
    confidence_score = confidence_levels.score_confidence(
        confidence,
        verdict=verdict,
        factors=confidence_factors,
    )
    risk_drivers = _risk_drivers(verdict, risk, affected_requirements, threshold_evidence)

    return RiskAssessment(
        verdict=verdict,
        risk=risk,
        confidence=confidence,
        confidence_score=confidence_score,
        affected_requirements=affected_requirements,
        affected_components=affected_components,
        affected_files=affected_files,
        introduced_failures=introduced,
        preexisting_failures=preexisting,
        threshold_evidence=threshold_evidence,
        evidence_summary=evidence_summary,
        recommended_next_checks=next_checks,
        comparison_summary=dict(_get(comparison, "summary", default={})),
        rules_triggered=rules_triggered,
        confidence_factors=confidence_factors,
        risk_drivers=risk_drivers,
    )


def _rules_triggered(
    verdict: str,
    introduced: list[Any],
    preexisting: list[Any],
    missing_baseline: list[Any],
    tests: list[Any],
    threshold_evidence: list[ThresholdEvidence],
    env_signals: list[dict[str, str]],
    worsened_metric_deltas: list[Any],
) -> list[str]:
    rules: list[str] = []
    if verdict == verdicts.CONFIRMED_REGRESSION:
        rules.extend(["R1_confirmed_threshold_regression", "R2_introduced_test_failure"])
    elif verdict == verdicts.SUCCESSFUL_CHANGE:
        rules.append("R7_successful_covered_change")
    elif verdict == verdicts.WORSENED_PREEXISTING_FAILURE:
        rules.append("R4_worsened_preexisting_failure")
    elif verdict == verdicts.PREEXISTING_FAILURE:
        rules.append("R3_preexisting_failure")
    elif verdict == verdicts.ENVIRONMENT_FAILURE:
        rules.append("R5_environment_failure")
    elif verdict == verdicts.REQUIREMENTS_COVERAGE_GAP:
        rules.append("R6_requirements_coverage_gap")
    elif verdict == verdicts.INSUFFICIENT_EVIDENCE:
        rules.append("R8_insufficient_evidence")
    elif verdict == verdicts.POSSIBLE_REGRESSION:
        rules.append("R2_possible_regression")

    if introduced:
        rules.append("signal_introduced_failure_present")
    if preexisting:
        rules.append("signal_preexisting_failure_present")
    if missing_baseline:
        rules.append("signal_missing_baseline_present")
    if any(_get(item, "classification") == "changed_status" for item in tests):
        rules.append("signal_unrecognized_or_inconclusive_status")
    if has_introduced_threshold_failure(threshold_evidence):
        rules.append("signal_baseline_pass_current_threshold_fail")
    if env_signals:
        rules.append("signal_environment_failure_pattern")
    if worsened_metric_deltas:
        rules.append("signal_material_metric_worsening")
    return sorted(set(rules))


def _confidence_factors(
    verdict: str,
    introduced: list[Any],
    preexisting: list[Any],
    threshold_evidence: list[ThresholdEvidence],
    affected_requirements: list[dict[str, Any]],
    affected_files: list[str],
    env_signals: list[dict[str, str]],
    has_requirement_metrics: bool,
) -> list[str]:
    factors: list[str] = []
    if introduced or preexisting or threshold_evidence:
        factors.append("+ baseline_current_pair_present")
    if introduced:
        factors.append("+ introduced_failure_detected")
    if preexisting:
        factors.append("+ preexisting_failure_detected")
    if has_introduced_threshold_failure(threshold_evidence):
        factors.append("+ threshold_crossing_detected")
    if affected_requirements:
        factors.append("+ requirement_mapped")
    else:
        factors.append("- missing_requirement_mapping")
    if affected_files:
        factors.append("+ affected_file_mapped")
    else:
        factors.append("- missing_affected_file_mapping")
    if env_signals:
        factors.append("+ environment_failure_pattern_matched")
    if not has_requirement_metrics:
        factors.append("- no_metric_requirement_coverage")
    if verdict == verdicts.INSUFFICIENT_EVIDENCE:
        factors.append("- incomplete_or_inconclusive_current_evidence")
    return factors


def _risk_drivers(
    verdict: str,
    risk: str,
    affected_requirements: list[dict[str, Any]],
    threshold_evidence: list[ThresholdEvidence],
) -> list[str]:
    drivers: list[str] = [f"verdict:{verdict}", f"risk:{risk}"]
    safety_values = sorted({str(req.get("safety_level")) for req in affected_requirements if req.get("safety_level")})
    for safety in safety_values:
        drivers.append(f"safety_level:{safety}")
    for item in threshold_evidence:
        if item.current_passed is False:
            drivers.append(f"threshold_failed:{item.requirement_id}:{item.metric}")
        elif item.current_passed is True:
            drivers.append(f"threshold_passed:{item.requirement_id}:{item.metric}")
    return drivers


def _verdict(
    introduced: list[Any],
    preexisting: list[Any],
    missing_baseline: list[Any],
    tests: list[Any],
    threshold_evidence: list[ThresholdEvidence],
    env_signals: list[dict[str, str]],
    worsened_metric_deltas: list[Any],
    affected_requirements: list[dict[str, Any]],
    coverage_gap: bool,
) -> str:
    introduced_thresholds = introduced_threshold_failures(threshold_evidence)
    current_failures = current_threshold_failures(threshold_evidence)
    # A test present only in the current run (no baseline) that FAILS is a current
    # failure with nothing to prove a regression against — honestly insufficient
    # evidence, never a clean pass. status_severity tier >= 3 is the shared
    # fail-closed taxonomy (fail/error/unrecognised), so a status-only failure
    # counts even when it carries no numeric threshold metric.
    missing_baseline_failures = [
        item for item in missing_baseline
        if status_severity(_get(item, "current_status")) >= 3
    ]
    inconclusive_tests = [
        item for item in tests
        if _get(item, "classification") in {"changed_status", "insufficient_evidence"}
    ]
    incomplete_thresholds = [
        item for item in threshold_evidence
        if item.current_passed is None or item.baseline_passed is None
    ]
    unchanged_passes = [
        item for item in tests
        if _get(item, "classification") == "unchanged_pass"
    ]

    # Environment failure only when the env signal is the WHOLE story: no
    # introduced threshold regression, and every introduced pass→fail is itself
    # explained by an environment pattern (e.g. a lone timeout). An introduced
    # failure that is NOT an env signal is real regression evidence and must not
    # be masked as flaky infra — it falls through to confirmed_regression below.
    env_signal_ids = {sig.get("test_id") for sig in env_signals}
    introduced_ids = {
        str(_get(item, "test_id", default=_get(item, "id", default="")))
        for item in introduced
    }
    unexplained_introduced = {tid for tid in introduced_ids if tid and tid not in env_signal_ids}
    if env_signals and not introduced_thresholds and not unexplained_introduced:
        return verdicts.ENVIRONMENT_FAILURE
    if introduced and introduced_thresholds:
        return verdicts.CONFIRMED_REGRESSION
    if preexisting and current_failures and has_material_worsening(worsened_metric_deltas):
        return verdicts.WORSENED_PREEXISTING_FAILURE
    if introduced:
        # A test that passed in the baseline and fails in the current run is
        # direct proof of a regression, even without a numeric threshold metric.
        # Threshold crossings (handled above) add corroborating evidence and lift
        # confidence, but are not required for the verdict. This makes AVERA work
        # for pure pass/fail software CI, not only metric/threshold verification.
        return verdicts.CONFIRMED_REGRESSION
    if preexisting and current_failures:
        return verdicts.PREEXISTING_FAILURE
    if preexisting and has_material_worsening(worsened_metric_deltas):
        return verdicts.WORSENED_PREEXISTING_FAILURE
    if missing_baseline_failures:
        return verdicts.INSUFFICIENT_EVIDENCE
    if inconclusive_tests or incomplete_thresholds:
        return verdicts.INSUFFICIENT_EVIDENCE
    if current_failures:
        if coverage_gap:
            return verdicts.REQUIREMENTS_COVERAGE_GAP
        return verdicts.POSSIBLE_REGRESSION
    if coverage_gap:
        return verdicts.REQUIREMENTS_COVERAGE_GAP
    if unchanged_passes and threshold_evidence:
        return verdicts.SUCCESSFUL_CHANGE
    return verdicts.EXPECTED_CHANGE


def _risk(
    verdict: str,
    affected_requirements: list[dict[str, Any]],
    threshold_evidence: list[ThresholdEvidence],
    introduced: list[Any],
) -> str:
    safety_rank = max(
        (risk_levels.safety_rank(req.get("safety_level")) for req in affected_requirements),
        default=0,
    )
    introduced_threshold = has_introduced_threshold_failure(threshold_evidence)

    if verdict == verdicts.CONFIRMED_REGRESSION and safety_rank >= 4:
        return risk_levels.RELEASE_BLOCKING
    if verdict == verdicts.CONFIRMED_REGRESSION and safety_rank >= 3:
        return risk_levels.HIGH
    if verdict == verdicts.CONFIRMED_REGRESSION:
        return risk_levels.MEDIUM
    if verdict == verdicts.POSSIBLE_REGRESSION and (introduced or introduced_threshold):
        return risk_levels.MEDIUM
    if verdict == verdicts.WORSENED_PREEXISTING_FAILURE:
        return risk_levels.HIGH if safety_rank >= 3 else risk_levels.MEDIUM
    if verdict == verdicts.PREEXISTING_FAILURE:
        return risk_levels.MEDIUM if safety_rank >= 3 else risk_levels.LOW
    if verdict in {
        verdicts.ENVIRONMENT_FAILURE,
        verdicts.INSUFFICIENT_EVIDENCE,
    }:
        return risk_levels.UNKNOWN
    if verdict == verdicts.REQUIREMENTS_COVERAGE_GAP:
        return risk_levels.MEDIUM
    return risk_levels.LOW


def _confidence(
    verdict: str,
    introduced: list[Any],
    threshold_evidence: list[ThresholdEvidence],
    affected_requirements: list[dict[str, Any]],
) -> str:
    has_introduced_threshold = has_introduced_threshold_failure(threshold_evidence)
    if (
        verdict == verdicts.CONFIRMED_REGRESSION
        and introduced
        and has_introduced_threshold
        and affected_requirements
    ):
        return confidence_levels.HIGH
    if verdict in {
        verdicts.CONFIRMED_REGRESSION,
        verdicts.POSSIBLE_REGRESSION,
    }:
        return confidence_levels.MEDIUM
    if verdict == verdicts.PREEXISTING_FAILURE and affected_requirements:
        return confidence_levels.HIGH
    if verdict == verdicts.WORSENED_PREEXISTING_FAILURE and affected_requirements:
        return confidence_levels.HIGH
    if verdict == verdicts.ENVIRONMENT_FAILURE:
        return confidence_levels.LOW
    if verdict == verdicts.SUCCESSFUL_CHANGE and threshold_evidence and affected_requirements:
        return confidence_levels.HIGH
    if verdict in {verdicts.EXPECTED_CHANGE, verdicts.SUCCESSFUL_CHANGE}:
        return confidence_levels.MEDIUM
    return confidence_levels.LOW


def _has_coverage_gap(
    requirements: list[dict[str, Any]],
    threshold_evidence: list[ThresholdEvidence],
    component_map: Any,
) -> bool:
    if not requirements or threshold_evidence:
        return False
    if not isinstance(component_map, dict) or not component_map:
        return False
    mapped_requirement_ids: set[str] = set()
    for mapping in component_map.values():
        mapped = _get(mapping, "requirements", default=[])
        if isinstance(mapped, list | tuple | set):
            mapped_requirement_ids.update(str(item) for item in mapped)
    requirement_ids = {str(req.get("id")) for req in requirements if req.get("id")}
    return bool(requirement_ids and mapped_requirement_ids.intersection(requirement_ids))


def _threshold_evidence(
    tests: list[Any],
    reqs_by_metric: dict[str, list[dict[str, Any]]],
) -> list[ThresholdEvidence]:
    evidence: list[ThresholdEvidence] = []
    for test in tests:
        test_id = str(_get(test, "test_id", default=_get(test, "id", default="unknown-test")))
        baseline_metrics = dict(_get(test, "baseline_metrics", default={}))
        current_metrics = dict(_get(test, "current_metrics", default={}))
        for metric, reqs in reqs_by_metric.items():
            if metric not in baseline_metrics and metric not in current_metrics:
                continue
            baseline_value = _number(baseline_metrics.get(metric))
            current_value = _number(current_metrics.get(metric))
            for req in reqs:
                operator = str(req.get("operator", "<=")).strip()
                threshold = _number(req.get("threshold"))
                if threshold is None:
                    continue
                evidence.append(
                    ThresholdEvidence(
                        requirement_id=str(req.get("id", "")),
                        metric=metric,
                        operator=operator,
                        threshold=threshold,
                        baseline_value=baseline_value,
                        current_value=current_value,
                        baseline_passed=_evaluate(baseline_value, operator, threshold),
                        current_passed=_evaluate(current_value, operator, threshold),
                        test_id=test_id,
                    )
                )
    return evidence


def _affected_requirements(
    requirements: list[dict[str, Any]],
    introduced: list[Any],
    threshold_evidence: list[ThresholdEvidence],
) -> list[dict[str, Any]]:
    affected_ids = {
        item.requirement_id
        for item in threshold_evidence
        if item.current_passed is not None
    }
    introduced_components = {
        _get(item, "component")
        for item in introduced
        if _get(item, "component") is not None
    }
    for req in requirements:
        if req.get("component") in introduced_components:
            affected_ids.add(str(req.get("id", "")))

    return [req for req in requirements if str(req.get("id", "")) in affected_ids]


def _affected_components(
    introduced: list[Any],
    preexisting: list[Any],
    requirements: list[dict[str, Any]],
) -> list[str]:
    components = {
        str(component)
        for component in [_get(item, "component") for item in introduced + preexisting]
        if component
    }
    components.update(str(req["component"]) for req in requirements if req.get("component"))
    return sorted(components)


def _affected_files(
    component_map: Any,
    components: list[str],
    requirements: list[dict[str, Any]],
) -> list[str]:
    if not isinstance(component_map, dict):
        return []

    req_ids = {str(req.get("id")) for req in requirements if req.get("id")}
    component_set = set(components)
    files: list[str] = []

    for path, mapping in component_map.items():
        mapped_component = _get(mapping, "component")
        mapped_reqs = _get(mapping, "requirements", default=[])
        mapped_req_ids = {str(item) for item in mapped_reqs} if isinstance(mapped_reqs, list) else set()
        if mapped_component in component_set or req_ids.intersection(mapped_req_ids):
            files.append(str(path))

    return sorted(files)


def _summary(
    verdict: str,
    introduced: list[Any],
    preexisting: list[Any],
    threshold_evidence: list[ThresholdEvidence],
    affected_files: list[str],
    env_signals: list[dict[str, str]],
    worsened_metric_deltas: list[Any],
) -> list[str]:
    lines = [f"Verdict is {verdict.replace('_', ' ')}."]
    for item in introduced:
        lines.append(f"{_get(item, 'test_id', default='unknown-test')} failed only in the current run.")
    for item in preexisting:
        lines.append(f"{_get(item, 'test_id', default='unknown-test')} failed in both baseline and current runs.")
    for item in threshold_evidence:
        if item.current_passed is False:
            lines.append(
                f"{item.metric} for {item.requirement_id} was {item.current_value:g}, "
                f"outside {item.operator} {item.threshold:g}."
            )
    if affected_files:
        lines.append(f"Mapped affected files: {', '.join(affected_files)}.")
    for signal in env_signals:
        lines.append(f"{signal['test_id']} matched environment failure pattern: {signal['reason']}.")
    for delta in worsened_metric_deltas:
        lines.append(
            f"{_get(delta, 'metric', default='metric')} materially worsened from "
            f"{_get(delta, 'baseline', default='unknown')} to {_get(delta, 'current', default='unknown')}."
        )
    return lines


def _next_checks(requirements: list[dict[str, Any]]) -> list[str]:
    checks: list[str] = []
    for req in requirements:
        raw = req.get("next_checks") or req.get("next_check")
        if not raw:
            continue
        if isinstance(raw, list | tuple | set):
            checks.extend(str(item).strip() for item in raw if str(item).strip())
        else:
            checks.extend(part.strip() for part in str(raw).split(";") if part.strip())
    return sorted(set(checks))


def _metric_deltas_for(items: list[Any]) -> list[Any]:
    deltas: list[Any] = []
    for item in items:
        raw = _get(item, "metric_deltas", default=[])
        if isinstance(raw, list | tuple):
            deltas.extend(raw)
    return deltas


def _normalize_requirements(requirements: Any | None) -> list[dict[str, Any]]:
    if requirements is None:
        return []
    if isinstance(requirements, dict):
        if isinstance(requirements.get("requirements"), list):
            requirements = requirements["requirements"]
        else:
            requirements = list(requirements.values())
    if not isinstance(requirements, list):
        return []
    return [_as_dict(item) for item in requirements]


def _requirements_by_metric(requirements: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_metric: dict[str, list[dict[str, Any]]] = {}
    for req in requirements:
        metric = req.get("metric")
        if metric:
            by_metric.setdefault(str(metric), []).append(req)
    return by_metric


def _evaluate(value: float | None, operator: str, threshold: float) -> bool | None:
    if value is None:
        return None
    if operator == "<":
        return value < threshold
    if operator == "<=":
        return value <= threshold
    if operator == ">":
        return value > threshold
    if operator == ">=":
        return value >= threshold
    if operator in {"=", "=="}:
        return value == threshold
    if operator in {"!=", "<>"}:
        return value != threshold
    return None


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


def _as_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return dict(item)
    if hasattr(item, "__dict__"):
        return dict(vars(item))
    return {}
