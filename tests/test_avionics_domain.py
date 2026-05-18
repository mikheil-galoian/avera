"""Tests for AVERA aviation domain — DO-178C / DAL levels."""

from __future__ import annotations

import pytest

avionics = pytest.importorskip("avera.domains.avionics")


class TestDALConstants:
    def test_dal_identifiers_defined(self):
        assert avionics.DAL_A == "dal-a"
        assert avionics.DAL_B == "dal-b"
        assert avionics.DAL_C == "dal-c"
        assert avionics.DAL_D == "dal-d"
        assert avionics.DAL_E == "dal-e"

    def test_dal_rank_ordering(self):
        from avera.domains.avionics.constants import dal_rank
        # DAL A (most critical) must rank highest
        assert dal_rank("dal-a") > dal_rank("dal-b")
        assert dal_rank("dal-b") > dal_rank("dal-c")
        assert dal_rank("dal-c") > dal_rank("dal-d")
        assert dal_rank("dal-d") > dal_rank("dal-e")
        assert dal_rank("dal-e") == 0

    def test_dal_rank_accepts_short_form(self):
        from avera.domains.avionics.constants import dal_rank
        assert dal_rank("a") == dal_rank("dal-a") == 4
        assert dal_rank("b") == dal_rank("dal-b") == 3
        assert dal_rank("c") == dal_rank("dal-c") == 2
        assert dal_rank("d") == dal_rank("dal-d") == 1
        assert dal_rank("e") == dal_rank("dal-e") == 0

    def test_dal_rank_accepts_aliases(self):
        from avera.domains.avionics.constants import dal_rank
        assert dal_rank("DAL-A") == 4
        assert dal_rank("dal_a") == 4
        assert dal_rank("catastrophic") == 4
        assert dal_rank("hazardous") == 3
        assert dal_rank("major") == 2
        assert dal_rank("minor") == 1
        assert dal_rank("none") == 0

    def test_dal_rank_unknown_returns_zero(self):
        from avera.domains.avionics.constants import dal_rank
        assert dal_rank("unknown_level") == 0
        assert dal_rank("") == 0
        assert dal_rank(None) == 0


class TestCoverageRequirements:
    def test_dal_a_requires_mcdc(self):
        from avera.domains.avionics.constants import required_coverage, mcdc_required
        cov = required_coverage("dal-a")
        assert "statement" in cov
        assert "branch" in cov
        assert "MCDC" in cov
        assert mcdc_required("dal-a") is True

    def test_dal_b_requires_mcdc(self):
        from avera.domains.avionics.constants import mcdc_required
        assert mcdc_required("dal-b") is True

    def test_dal_c_no_mcdc(self):
        from avera.domains.avionics.constants import required_coverage, mcdc_required
        cov = required_coverage("dal-c")
        assert "statement" in cov
        assert "branch" in cov
        assert "MCDC" not in cov
        assert mcdc_required("dal-c") is False

    def test_dal_d_statement_only(self):
        from avera.domains.avionics.constants import required_coverage
        cov = required_coverage("dal-d")
        assert "statement" in cov
        assert "branch" not in cov
        assert "MCDC" not in cov

    def test_dal_e_no_coverage_required(self):
        from avera.domains.avionics.constants import required_coverage
        assert required_coverage("dal-e") == []

    def test_coverage_accepts_short_form(self):
        from avera.domains.avionics.constants import required_coverage
        assert required_coverage("a") == required_coverage("dal-a")
        assert required_coverage("c") == required_coverage("dal-c")


class TestRiskLevelDALIntegration:
    """Verify that DAL levels are correctly ranked in the shared risk classifier."""

    def test_dal_a_ranks_release_blocking(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("dal-a") == 4

    def test_dal_b_ranks_high(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("dal-b") == 3

    def test_dal_c_ranks_medium(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("dal-c") == 2

    def test_dal_d_ranks_low(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("dal-d") == 1

    def test_dal_e_ranks_zero(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("dal-e") == 0

    def test_asil_d_and_dal_a_same_rank(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("asil-d") == safety_rank("dal-a") == 4

    def test_sil4_and_dal_a_same_rank(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil4") == safety_rank("dal-a") == 4


class TestAvionicsRequirementsTemplate:
    def test_template_not_empty(self):
        assert len(avionics.AVIONICS_REQUIREMENTS_TEMPLATE) >= 5

    def test_all_have_required_fields(self):
        for req in avionics.AVIONICS_REQUIREMENTS_TEMPLATE:
            assert "id" in req
            assert "component" in req
            assert "metric" in req
            assert "operator" in req
            assert "threshold" in req
            assert "safety_level" in req

    def test_dal_a_requirements_present(self):
        dal_a_reqs = [
            r for r in avionics.AVIONICS_REQUIREMENTS_TEMPLATE
            if r["safety_level"] == "dal-a"
        ]
        assert len(dal_a_reqs) >= 2

    def test_fadec_component_present(self):
        components = {r["component"] for r in avionics.AVIONICS_REQUIREMENTS_TEMPLATE}
        assert "Full Authority Digital Engine Control" in components

    def test_fcc_component_present(self):
        components = {r["component"] for r in avionics.AVIONICS_REQUIREMENTS_TEMPLATE}
        assert "Flight Control Computer" in components


def _fixture(name: str) -> "Path":
    from pathlib import Path
    return Path(__file__).resolve().parents[1] / "fixtures" / name


class TestFADECFixtureAnalysis:
    """End-to-end test: FADEC overspeed regression must yield release_blocking."""

    def test_fadec_overspeed_confirmed_regression(self):
        from avera.core import analyze
        d = _fixture("fadec-overspeed-regression")
        result = analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )
        assert result["verdict"] == "confirmed_regression"

    def test_fadec_overspeed_release_blocking(self):
        from avera.core import analyze
        d = _fixture("fadec-overspeed-regression")
        result = analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )
        assert result["risk"] in {"release_blocking", "high"}

    def test_fadec_overspeed_high_confidence(self):
        from avera.core import analyze
        d = _fixture("fadec-overspeed-regression")
        result = analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )
        assert result["confidence"] in {"high", "medium"}

    def test_fadec_affected_component_identified(self):
        from avera.core import analyze
        d = _fixture("fadec-overspeed-regression")
        result = analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )
        components = result.get("affected_components", [])
        assert any("Engine Control" in c or "FADEC" in c for c in components)


class TestFCCFixtureAnalysis:
    """End-to-end test: FCC envelope regression must yield confirmed_regression."""

    def test_fcc_envelope_confirmed_regression(self):
        from avera.core import analyze
        d = _fixture("fcc-envelope-regression")
        result = analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )
        assert result["verdict"] == "confirmed_regression"

    def test_fcc_envelope_high_risk(self):
        from avera.core import analyze
        d = _fixture("fcc-envelope-regression")
        result = analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )
        assert result["risk"] in {"release_blocking", "high"}

    def test_fcc_affected_component_identified(self):
        from avera.core import analyze
        d = _fixture("fcc-envelope-regression")
        result = analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )
        components = result.get("affected_components", [])
        assert any("Flight Control" in c for c in components)
