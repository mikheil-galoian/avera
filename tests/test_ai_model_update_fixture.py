"""Tests for AI model update regression detection.

Validates that AVERA correctly detects a safety-critical regression
introduced by an AI model update (v2.4.0 → v2.4.1) where the
pedestrian detection rate dropped below the required threshold.

This proves the kernel works for AI change verification without
any modifications to the core pipeline.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from avera.adapters.ai_evaluation import load_ai_evaluation, model_card_to_metadata
from avera.core import analyze

FIXTURE = Path("fixtures/adas-model-update-regression")


@pytest.mark.skipif(
    not FIXTURE.exists(),
    reason="AI model update fixture not found",
)
class TestAIModelUpdateFixture:
    """Full pipeline test for AI model regression detection."""

    def test_ai_regression_detected_as_confirmed_regression(self):
        """Kernel detects AI model regression as confirmed_regression."""
        report = analyze(
            baseline_path=FIXTURE / "baseline_results.json",
            current_path=FIXTURE / "current_results.json",
            requirements_path=FIXTURE / "requirements.csv",
            component_map_path=FIXTURE / "component_map.json",
            change_description_path=FIXTURE / "change_description.txt",
        )
        assert report["verdict"] == "confirmed_regression", (
            f"Expected confirmed_regression for AI model update causing "
            f"safety threshold violation, got: {report['verdict']}"
        )

    def test_ai_regression_risk_is_high_or_release_blocking(self):
        """Safety-critical AI regression produces high or release_blocking risk."""
        report = analyze(
            baseline_path=FIXTURE / "baseline_results.json",
            current_path=FIXTURE / "current_results.json",
            requirements_path=FIXTURE / "requirements.csv",
            component_map_path=FIXTURE / "component_map.json",
            change_description_path=FIXTURE / "change_description.txt",
        )
        assert report["risk"] in ("high", "release_blocking"), (
            f"Expected high or release_blocking risk for ASIL-D requirement "
            f"violation, got: {report['risk']}"
        )

    def test_affected_component_is_perception_module(self):
        """Affected component is correctly identified as adas-perception-module."""
        report = analyze(
            baseline_path=FIXTURE / "baseline_results.json",
            current_path=FIXTURE / "current_results.json",
            requirements_path=FIXTURE / "requirements.csv",
            component_map_path=FIXTURE / "component_map.json",
            change_description_path=FIXTURE / "change_description.txt",
        )
        components = report.get("affected_components", [])
        assert "adas-perception-module" in components, (
            f"Expected adas-perception-module in affected_components, "
            f"got: {components}"
        )

    def test_safety_requirement_appears_in_affected_requirements(self):
        """REQ-SAFETY-012 (violated requirement) appears in affected requirements."""
        report = analyze(
            baseline_path=FIXTURE / "baseline_results.json",
            current_path=FIXTURE / "current_results.json",
            requirements_path=FIXTURE / "requirements.csv",
            component_map_path=FIXTURE / "component_map.json",
            change_description_path=FIXTURE / "change_description.txt",
        )
        affected = report.get("affected_requirements", [])
        assert "REQ-SAFETY-012" in affected, (
            f"Expected REQ-SAFETY-012 in affected_requirements, got: {affected}"
        )

    def test_report_contains_evidence(self):
        """Report contains threshold evidence for the failed scenario."""
        report = analyze(
            baseline_path=FIXTURE / "baseline_results.json",
            current_path=FIXTURE / "current_results.json",
            requirements_path=FIXTURE / "requirements.csv",
            component_map_path=FIXTURE / "component_map.json",
            change_description_path=FIXTURE / "change_description.txt",
        )
        evidence = report.get("evidence", {})
        assert len(evidence) > 0, (
            "Report should contain threshold evidence for the failed test"
        )

    def test_change_description_in_report(self):
        """Change description is present in the report."""
        report = analyze(
            baseline_path=FIXTURE / "baseline_results.json",
            current_path=FIXTURE / "current_results.json",
            requirements_path=FIXTURE / "requirements.csv",
            component_map_path=FIXTURE / "component_map.json",
            change_description_path=FIXTURE / "change_description.txt",
        )
        assert "change_description" in report
        assert "v2.4.0" in report["change_description"]


class TestAIEvaluationAdapter:
    """Unit tests for the AI evaluation adapter."""

    def test_load_baseline_evaluation(self):
        """Baseline evaluation loads and contains all tests."""
        if not FIXTURE.exists():
            pytest.skip("Fixture not found")
        result = load_ai_evaluation(FIXTURE / "baseline_results.json")
        assert result["runId"] == "eval-adas-perception-v2.4.0"
        assert result["stage"] == "sil"
        assert len(result["tests"]) == 6

    def test_load_current_evaluation(self):
        """Current evaluation loads and contains the failing test."""
        if not FIXTURE.exists():
            pytest.skip("Fixture not found")
        result = load_ai_evaluation(FIXTURE / "current_results.json")
        assert result["runId"] == "eval-adas-perception-v2.4.1"
        failing = [t for t in result["tests"] if not t["passed"]]
        assert len(failing) == 1
        assert failing[0]["testId"] == "SC-SAFETY-012-night-rain"

    def test_all_baseline_tests_pass(self):
        """All baseline evaluation tests pass."""
        if not FIXTURE.exists():
            pytest.skip("Fixture not found")
        result = load_ai_evaluation(FIXTURE / "baseline_results.json")
        failing = [t for t in result["tests"] if not t["passed"]]
        assert len(failing) == 0, f"Baseline should have no failures, got: {failing}"

    def test_current_has_exactly_one_failure(self):
        """Current evaluation has exactly one failing test."""
        if not FIXTURE.exists():
            pytest.skip("Fixture not found")
        result = load_ai_evaluation(FIXTURE / "current_results.json")
        failing = [t for t in result["tests"] if not t["passed"]]
        assert len(failing) == 1

    def test_load_ai_evaluation_missing_file_raises(self):
        """Loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_ai_evaluation(Path("nonexistent/evaluation.json"))

    def test_model_card_baseline_loads(self):
        """Baseline model card loads with correct version."""
        if not FIXTURE.exists():
            pytest.skip("Fixture not found")
        meta = model_card_to_metadata(FIXTURE / "model_card_baseline.json")
        assert meta["model_version"] == "2.4.0"
        assert meta["certification_status"] == "validated"

    def test_model_card_current_loads(self):
        """Current model card loads with correct version and changes."""
        if not FIXTURE.exists():
            pytest.skip("Fixture not found")
        meta = model_card_to_metadata(FIXTURE / "model_card_current.json")
        assert meta["model_version"] == "2.4.1"
        assert meta["certification_status"] == "pending_validation"
        assert len(meta["changes_from_baseline"]) > 0

    def test_model_card_missing_file_returns_empty(self):
        """Missing model card returns empty dict without raising."""
        meta = model_card_to_metadata(Path("nonexistent/model_card.json"))
        assert meta == {}
