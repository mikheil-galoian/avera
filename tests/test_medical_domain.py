"""Tests for AVERA medical domain — IEC-62304 / Class A-C levels."""

from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# IEC-62304 class rank helpers (via shared risk_levels)
# ---------------------------------------------------------------------------

class TestIEC62304RankInRiskLevels:
    """Verify IEC-62304 Class A/B/C levels are correctly ranked in the shared classifier."""

    def test_class_c_rank_high(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("class-c") == 3

    def test_class_b_rank_medium(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("class-b") == 2

    def test_class_a_rank_low(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("class-a") == 1

    def test_underscore_variants_accepted(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("class_c") == 3
        assert safety_rank("class_b") == 2
        assert safety_rank("class_a") == 1

    def test_iec_prefix_variants_accepted(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("iec-c") == 3
        assert safety_rank("iec-b") == 2
        assert safety_rank("iec-a") == 1

    def test_class_c_equals_asil_c_equals_dal_b_equals_sil3(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("class-c") == safety_rank("asil-c") == safety_rank("dal-b") == safety_rank("sil3") == 3

    def test_class_a_equals_asil_a_equals_sil1(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("class-a") == safety_rank("asil-a") == safety_rank("sil1") == 1

    def test_unknown_class_returns_zero(self):
        from avera.classify.risk_levels import safety_rank
        assert safety_rank("class-d") == 0
        assert safety_rank("class-") == 0
        assert safety_rank(None) == 0


# ---------------------------------------------------------------------------
# Infusion pump flow rate fixture — end-to-end
# ---------------------------------------------------------------------------

def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / name


@pytest.mark.skipif(
    not (_fixture("infusion-pump-flow-regression") / "requirements.csv").exists(),
    reason="infusion-pump-flow-regression fixture not present",
)
class TestInfusionPumpFixture:
    """End-to-end: IEC-62304 Class C infusion pump regression must yield high risk."""

    def _result(self):
        from avera.core import analyze
        d = _fixture("infusion-pump-flow-regression")
        return analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )

    def test_verdict_confirmed_regression(self):
        assert self._result()["verdict"] == "confirmed_regression"

    def test_risk_high(self):
        result = self._result()
        assert result["risk"] in {"high", "release_blocking"}

    def test_confidence_high(self):
        assert self._result()["confidence"] in {"high", "medium"}

    def test_affected_component_identified(self):
        components = self._result().get("affected_components", [])
        assert any("Infusion" in c or "Pump" in c or "Dosage" in c for c in components)

    def test_schema_version_present(self):
        assert "schema_version" in self._result()

    def test_threshold_evidence_captured(self):
        result = self._result()
        # analyze() returns threshold evidence in the 'evidence' dict keyed by metric name.
        evidence = result.get("evidence", {})
        assert isinstance(evidence, dict)
        assert "flow_rate_deviation_pct" in evidence
        entry = evidence["flow_rate_deviation_pct"]
        assert entry["current"] > entry["threshold"]  # 7.8 > 5.0
