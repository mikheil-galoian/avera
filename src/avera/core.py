"""Public AVERA analysis API.

This module is intentionally thin: it wires ingestion, comparison,
classification, and report-shaped output into one stable function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from avera.classify.risk_classifier import RiskAssessment, classify_risk
from avera.compare.baseline_comparator import compare_runs
from avera.ingestion.component_map import load_component_map
from avera.ingestion.requirements import load_requirements
from avera.ingestion.verification_results import load_verification_results
from avera.signals import load_signal_trace, summarize_signal_trace


def analyze(
    *,
    baseline_path: str | Path,
    current_path: str | Path,
    requirements_path: str | Path,
    component_map_path: str | Path,
    change_description_path: str | Path | None = None,
) -> dict[str, Any]:
    """Analyze one local AVERA evidence pack and return a report dictionary."""

    requirements = load_requirements(Path(requirements_path))
    component_map = load_component_map(Path(component_map_path))
    baseline = load_verification_results(Path(baseline_path))
    current = load_verification_results(Path(current_path))

    comparison = compare_runs(baseline=baseline, current=current)
    assessment = classify_risk(
        comparison=comparison,
        requirements=requirements,
        component_map=component_map,
    )

    change_description = None
    if change_description_path:
        path = Path(change_description_path)
        if path.exists():
            change_description = path.read_text(encoding="utf-8").strip()

    report = assessment_to_public_report(assessment)
    if change_description:
        report["change_description"] = change_description
    signal_trace_path = Path(current_path).parent / "signal_trace.csv"
    if signal_trace_path.exists():
        signal_points = load_signal_trace(signal_trace_path)
        report["signal_trace_points"] = len(signal_points)
        report["signal_summary"] = summarize_signal_trace(signal_points)

    model_card_path = Path(current_path).parent / "model_card_current.json"
    if model_card_path.exists():
        from avera.ingestion.model_card import load_model_card
        report["model_metadata"] = load_model_card(model_card_path)

    return report


def assessment_to_public_report(assessment: RiskAssessment) -> dict[str, Any]:
    """Flatten a classifier assessment into the first stable public report."""

    threshold_evidence = {}
    for item in assessment.threshold_evidence:
        if item.current_passed is False:
            threshold_evidence[item.metric] = {
                "baseline": item.baseline_value,
                "current": item.current_value,
                "operator": item.operator,
                "threshold": item.threshold,
            }

    affected_requirements = [
        str(item.get("id"))
        for item in assessment.affected_requirements
        if item.get("id")
    ]

    return {
        "schema_version": assessment.schema_version,
        "verdict": assessment.verdict,
        "risk": assessment.risk,
        "confidence": assessment.confidence,
        "confidence_score": assessment.confidence_score,
        "affected_component": assessment.affected_components[0]
        if assessment.affected_components
        else None,
        "affected_components": assessment.affected_components,
        "affected_requirements": affected_requirements,
        "changed_files": assessment.affected_files,
        "recommendations": assessment.recommended_next_checks,
        "evidence": threshold_evidence,
        "evidence_summary": assessment.evidence_summary,
        "comparison_summary": assessment.comparison_summary,
        "rules_triggered": assessment.rules_triggered,
        "confidence_factors": assessment.confidence_factors,
        "risk_drivers": assessment.risk_drivers,
    }
