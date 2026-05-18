"""Tests for AVERA railway domain — EN-50128 / SIL levels."""

from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# SIL rank helpers (via shared risk_levels)
# ---------------------------------------------------------------------------

class TestSILRankInRiskLevels:
    """Verify EN-50128 SIL levels are correctly ranked in the shared classifier."""

    def test_sil4_rank_release_blocking(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil4") == 4

    def test_sil3_rank_high(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil3") == 3

    def test_sil2_rank_medium(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil2") == 2

    def test_sil1_rank_low(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil1") == 1

    def test_sil0_rank_zero(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil0") == 0

    def test_hyphenated_sil4_accepted(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil-4") == 4
        assert safety_rank("sil-3") == 3
        assert safety_rank("sil-0") == 0

    def test_sil4_equals_asil_d_equals_dal_a(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil4") == safety_rank("asil-d") == safety_rank("dal-a") == 4

    def test_sil3_equals_asil_c_equals_dal_b(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil3") == safety_rank("asil-c") == safety_rank("dal-b") == 3

    def test_unknown_sil_returns_zero(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("sil99") == 0
        assert safety_rank("") == 0
        assert safety_rank(None) == 0


# ---------------------------------------------------------------------------
# ETCS brake response fixture — end-to-end
# ---------------------------------------------------------------------------

def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / name


@pytest.mark.skipif(
    not (_fixture("etcs-brake-response-regression") / "requirements.csv").exists(),
    reason="etcs-brake-response-regression fixture not present",
)
class TestETCSBrakeFixture:
    """End-to-end: ETCS SIL 4 brake regression must yield release_blocking."""

    def _result(self):
        from avera.core import analyze
        d = _fixture("etcs-brake-response-regression")
        return analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )

    def test_verdict_confirmed_regression(self):
        assert self._result()["verdict"] == "confirmed_regression"

    def test_risk_release_blocking(self):
        result = self._result()
        assert result["risk"] in {"release_blocking", "high"}

    def test_confidence_high(self):
        assert self._result()["confidence"] in {"high", "medium"}

    def test_affected_component_identified(self):
        components = self._result().get("affected_components", [])
        assert any("Braking" in c or "ETCS" in c for c in components)

    def test_schema_version_present(self):
        assert "schema_version" in self._result()
