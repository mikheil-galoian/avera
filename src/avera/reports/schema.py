"""Public report schema constants for AVERA reports."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from avera.classify.confidence import ALL_CONFIDENCE_LEVELS
from avera.classify.risk_levels import ALL_RISK_LEVELS
from avera.classify.verdicts import ALL_VERDICTS

ASSESSMENT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AVERA Change Impact Assessment",
    "type": "object",
    "required": ["verdict", "risk", "confidence"],
    "properties": {
        "verdict": {"type": "string", "enum": list(ALL_VERDICTS)},
        "risk": {"type": "string", "enum": list(ALL_RISK_LEVELS)},
        "confidence": {"type": "string", "enum": list(ALL_CONFIDENCE_LEVELS)},
        "affected_requirements": {"type": "array", "items": {"type": "object"}},
        "affected_components": {"type": "array", "items": {"type": "string"}},
        "affected_files": {"type": "array", "items": {"type": "string"}},
        "introduced_failures": {"type": "array"},
        "preexisting_failures": {"type": "array"},
        "threshold_evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "requirement_id",
                    "metric",
                    "operator",
                    "threshold",
                    "baseline_passed",
                    "current_passed",
                    "test_id",
                ],
                "properties": {
                    "requirement_id": {"type": "string"},
                    "metric": {"type": "string"},
                    "operator": {"type": "string"},
                    "threshold": {"type": "number"},
                    "baseline_value": {"type": ["number", "null"]},
                    "current_value": {"type": ["number", "null"]},
                    "baseline_passed": {"type": ["boolean", "null"]},
                    "current_passed": {"type": ["boolean", "null"]},
                    "test_id": {"type": "string"},
                },
            },
        },
        "evidence_summary": {"type": "array", "items": {"type": "string"}},
        "recommended_next_checks": {"type": "array", "items": {"type": "string"}},
        "comparison_summary": {
            "type": "object",
            "additionalProperties": {"type": "integer"},
        },
    },
    "additionalProperties": True,
}


def assessment_schema() -> dict[str, Any]:
    """Return a copy of the public assessment schema."""

    return deepcopy(ASSESSMENT_SCHEMA)
