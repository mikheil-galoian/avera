"""Validate generated AVERA JSON reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


REQUIRED_REPORT_FIELDS = (
    "schema_version",
    "verdict",
    "risk",
    "confidence",
    "confidence_score",
    "affected_requirements",
    "affected_components",
    "affected_files",
    "introduced_failures",
    "preexisting_failures",
    "threshold_evidence",
    "evidence_summary",
    "recommended_next_checks",
    "comparison_summary",
    "rules_triggered",
    "confidence_factors",
    "risk_drivers",
)

LIST_REPORT_FIELDS = (
    "affected_requirements",
    "affected_components",
    "affected_files",
    "introduced_failures",
    "preexisting_failures",
    "threshold_evidence",
    "evidence_summary",
    "recommended_next_checks",
    "rules_triggered",
    "confidence_factors",
    "risk_drivers",
)

STRING_REPORT_FIELDS = (
    "schema_version",
    "verdict",
    "risk",
    "confidence",
)

NUMBER_REPORT_FIELDS = (
    "confidence_score",
)


@dataclass(frozen=True)
class ReportValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_fields: tuple[str, ...] = REQUIRED_REPORT_FIELDS


def validate_report(report: dict[str, Any]) -> ReportValidationResult:
    """Validate the stable top-level AVERA JSON report contract."""

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(report, dict):
        return ReportValidationResult(
            ok=False,
            errors=["Report must be a JSON object"],
            warnings=[],
        )

    for field_name in REQUIRED_REPORT_FIELDS:
        if field_name not in report:
            errors.append(f"Missing required report field: {field_name}")

    for field_name in STRING_REPORT_FIELDS:
        if field_name in report and not isinstance(report[field_name], str):
            errors.append(f"Report field {field_name} must be a string")

    for field_name in LIST_REPORT_FIELDS:
        if field_name in report and not isinstance(report[field_name], list):
            errors.append(f"Report field {field_name} must be an array")

    for field_name in NUMBER_REPORT_FIELDS:
        if field_name in report and not isinstance(report[field_name], int | float):
            errors.append(f"Report field {field_name} must be a number")

    if "comparison_summary" in report and not isinstance(report["comparison_summary"], dict):
        errors.append("Report field comparison_summary must be an object")

    if "schema_version" in report and not str(report["schema_version"]).startswith("avera."):
        warnings.append("Report schema_version does not use the avera.* namespace")

    return ReportValidationResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
    )
