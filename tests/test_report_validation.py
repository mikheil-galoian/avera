"""Tests for avera.validation.report — validate_report()."""

from __future__ import annotations

import pytest

from avera.validation.report import (
    ReportValidationResult,
    validate_report,
    REQUIRED_REPORT_FIELDS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_report(**overrides) -> dict:
    base = {
        "schema_version": "avera.assessment.v0.2",
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "confidence_score": 0.95,
        "affected_requirements": [],
        "affected_components": [],
        "affected_files": [],
        "introduced_failures": [],
        "preexisting_failures": [],
        "threshold_evidence": [],
        "evidence_summary": ["Verdict is confirmed regression."],
        "recommended_next_checks": [],
        "comparison_summary": {"total_tests": 1},
        "rules_triggered": ["R1_confirmed_threshold_regression"],
        "confidence_factors": ["+ baseline_current_pair_present"],
        "risk_drivers": ["verdict:confirmed_regression", "risk:high"],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Valid report
# ---------------------------------------------------------------------------

class TestValidReport:
    def test_valid_report_passes(self):
        result = validate_report(_valid_report())
        assert result.ok is True
        assert result.errors == []

    def test_result_type(self):
        result = validate_report(_valid_report())
        assert isinstance(result, ReportValidationResult)

    def test_required_fields_list_is_non_empty(self):
        result = validate_report(_valid_report())
        assert len(result.required_fields) > 0


# ---------------------------------------------------------------------------
# Missing fields
# ---------------------------------------------------------------------------

class TestMissingFields:
    @pytest.mark.parametrize("field_name", REQUIRED_REPORT_FIELDS)
    def test_missing_required_field_fails(self, field_name):
        report = _valid_report()
        del report[field_name]
        result = validate_report(report)
        assert result.ok is False
        assert any(field_name in e for e in result.errors)

    def test_empty_report_fails_with_multiple_errors(self):
        result = validate_report({})
        assert result.ok is False
        assert len(result.errors) > 5


# ---------------------------------------------------------------------------
# Wrong field types
# ---------------------------------------------------------------------------

class TestWrongTypes:
    def test_verdict_as_number_fails(self):
        result = validate_report(_valid_report(verdict=42))
        assert result.ok is False

    def test_risk_as_list_fails(self):
        result = validate_report(_valid_report(risk=["high"]))
        assert result.ok is False

    def test_confidence_score_as_string_fails(self):
        result = validate_report(_valid_report(confidence_score="0.95"))
        assert result.ok is False

    def test_affected_requirements_as_dict_fails(self):
        result = validate_report(_valid_report(affected_requirements={}))
        assert result.ok is False

    def test_comparison_summary_as_list_fails(self):
        result = validate_report(_valid_report(comparison_summary=["total_tests", 1]))
        assert result.ok is False

    def test_rules_triggered_as_string_fails(self):
        result = validate_report(_valid_report(rules_triggered="R1_confirmed_threshold_regression"))
        assert result.ok is False


# ---------------------------------------------------------------------------
# Non-dict input
# ---------------------------------------------------------------------------

class TestNonDictInput:
    def test_list_input_fails(self):
        result = validate_report([])  # type: ignore[arg-type]
        assert result.ok is False
        assert any("object" in e.lower() for e in result.errors)

    def test_none_input_fails(self):
        result = validate_report(None)  # type: ignore[arg-type]
        assert result.ok is False

    def test_string_input_fails(self):
        result = validate_report("not a dict")  # type: ignore[arg-type]
        assert result.ok is False


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_non_avera_schema_version_produces_warning(self):
        result = validate_report(_valid_report(schema_version="v1.0"))
        # May or may not fail depending on whether schema_version is caught by string check
        # but should have a warning about namespace
        assert any("schema_version" in w for w in result.warnings)

    def test_valid_avera_schema_version_has_no_warning(self):
        result = validate_report(_valid_report(schema_version="avera.assessment.v0.2"))
        assert not any("schema_version" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Real report from fixture
# ---------------------------------------------------------------------------

class TestRealReport:
    def test_bms_fast_charge_report_passes_validation(self):
        import json
        from pathlib import Path
        report_path = Path("reports/fixtures/bms-fast-charge/avera-report.json")
        if report_path.exists():
            report = json.loads(report_path.read_text())
            result = validate_report(report)
            assert result.ok is True
