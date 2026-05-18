"""Tests for the AVERA powertrain domain module.

Covers:
- constants: ASIL levels, metric names, threshold catalogue, operators
- requirements: catalogue structure, filtered views, CSV serialisation
- fixtures: structure integrity, expected AVERA pipeline outcomes
- end-to-end: avera.core.analyze() produces correct verdict + risk for each scenario
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from avera.domains.powertrain import (
    ASIL_A,
    ASIL_B,
    ASIL_C,
    ASIL_D,
    ASIL_TO_SAFETY_LEVEL,
    EMISSIONS_IMPROVEMENT,
    ALL_FIXTURES,
    Metrics,
    OVERSPEED_REGRESSION,
    POWERTRAIN_REQUIREMENTS,
    QM,
    SAFETY_LEVEL_TO_ASIL,
    SHIFT_QUALITY_REGRESSION,
    THRESHOLD_OPERATORS,
    THRESHOLDS,
    asil_for_metric,
    get_fixture,
    requirements_by_id,
    requirements_for_component,
    requirements_for_safety_level,
    threshold_operator,
    to_csv,
)


# ===========================================================================
# constants.py
# ===========================================================================

class TestAsilConstants:
    def test_asil_d_string(self):
        assert ASIL_D == "asil_d"

    def test_asil_b_string(self):
        assert ASIL_B == "asil_b"

    def test_qm_string(self):
        assert QM == "qm"

    def test_asil_d_maps_to_release_blocking(self):
        # ASIL-D must map to AVERA's highest risk-escalating safety level
        assert ASIL_TO_SAFETY_LEVEL[ASIL_D] == "release_blocking"

    def test_asil_c_maps_to_high(self):
        assert ASIL_TO_SAFETY_LEVEL[ASIL_C] == "high"

    def test_asil_b_maps_to_medium(self):
        assert ASIL_TO_SAFETY_LEVEL[ASIL_B] == "medium"

    def test_asil_a_maps_to_low(self):
        assert ASIL_TO_SAFETY_LEVEL[ASIL_A] == "low"

    def test_reverse_map_roundtrips(self):
        for asil, level in ASIL_TO_SAFETY_LEVEL.items():
            if level != "none":
                assert SAFETY_LEVEL_TO_ASIL[level] == asil


class TestMetrics:
    def test_max_engine_rpm_constant(self):
        assert Metrics.MAX_ENGINE_RPM == "max_engine_rpm"

    def test_torque_hole_ms_constant(self):
        assert Metrics.TORQUE_HOLE_MS == "torque_hole_ms"

    def test_nox_constant(self):
        assert Metrics.NOX_MG_PER_KM == "nox_mg_per_km"

    def test_injection_pressure_constant(self):
        assert Metrics.INJECTION_PRESSURE_BAR == "injection_pressure_bar"


class TestThresholds:
    def test_max_engine_rpm_threshold(self):
        assert THRESHOLDS[Metrics.MAX_ENGINE_RPM] == 7000.0

    def test_overspeed_response_threshold(self):
        assert THRESHOLDS[Metrics.OVERSPEED_RESPONSE_MS] == 50.0

    def test_torque_hole_threshold(self):
        assert THRESHOLDS[Metrics.TORQUE_HOLE_MS] == 100.0

    def test_nox_threshold(self):
        assert THRESHOLDS[Metrics.NOX_MG_PER_KM] == 60.0

    def test_injection_pressure_threshold(self):
        assert THRESHOLDS[Metrics.INJECTION_PRESSURE_BAR] == 100.0

    def test_all_thresholds_are_positive(self):
        for metric, val in THRESHOLDS.items():
            assert val > 0, f"{metric} threshold should be positive"


class TestThresholdOperators:
    def test_default_operator_is_lte(self):
        # Most metrics are upper limits
        assert threshold_operator(Metrics.MAX_ENGINE_RPM) == "<="
        assert threshold_operator(Metrics.COOLANT_TEMP_C) == "<="

    def test_injection_pressure_is_gte(self):
        # Rail pressure is a lower limit
        assert threshold_operator(Metrics.INJECTION_PRESSURE_BAR) == ">="

    def test_unknown_metric_defaults_lte(self):
        assert threshold_operator("some_unknown_metric") == "<="


class TestAsilForMetric:
    def test_max_engine_rpm_is_asil_d(self):
        assert asil_for_metric(Metrics.MAX_ENGINE_RPM) == ASIL_D

    def test_torque_hole_is_asil_b(self):
        assert asil_for_metric(Metrics.TORQUE_HOLE_MS) == ASIL_B

    def test_nox_is_qm(self):
        assert asil_for_metric(Metrics.NOX_MG_PER_KM) == QM

    def test_unknown_metric_returns_qm(self):
        assert asil_for_metric("unknown_metric_xyz") == QM


# ===========================================================================
# requirements.py
# ===========================================================================

class TestPowertrainRequirements:
    def test_catalogue_not_empty(self):
        assert len(POWERTRAIN_REQUIREMENTS) >= 10

    def test_all_reqs_have_required_keys(self):
        required_keys = {"id", "component", "requirement", "metric",
                         "operator", "threshold", "safety_level", "next_checks"}
        for req in POWERTRAIN_REQUIREMENTS:
            missing = required_keys - req.keys()
            assert not missing, f"Requirement {req.get('id')} missing: {missing}"

    def test_all_ids_unique(self):
        ids = [r["id"] for r in POWERTRAIN_REQUIREMENTS]
        assert len(ids) == len(set(ids))

    def test_all_ids_have_pt_prefix(self):
        for req in POWERTRAIN_REQUIREMENTS:
            assert req["id"].startswith("PT-REQ-"), f"Bad ID: {req['id']}"

    def test_operators_are_valid(self):
        valid = {"<=", ">="}
        for req in POWERTRAIN_REQUIREMENTS:
            assert req["operator"] in valid, f"{req['id']} has invalid operator {req['operator']!r}"

    def test_thresholds_are_numeric(self):
        for req in POWERTRAIN_REQUIREMENTS:
            assert isinstance(req["threshold"], (int, float)), \
                f"{req['id']} threshold is not numeric"

    def test_safety_levels_are_avera_strings(self):
        valid = {"release_blocking", "high", "medium", "low", "none"}
        for req in POWERTRAIN_REQUIREMENTS:
            assert req["safety_level"] in valid, \
                f"{req['id']} has unknown safety_level {req['safety_level']!r}"

    def test_req_001_asil_d_mapping(self):
        # ASIL-D requirements must use release_blocking to trigger correct risk
        r = next(r for r in POWERTRAIN_REQUIREMENTS if r["id"] == "PT-REQ-001")
        assert r["safety_level"] == "release_blocking"

    def test_req_010_asil_b_mapping(self):
        r = next(r for r in POWERTRAIN_REQUIREMENTS if r["id"] == "PT-REQ-010")
        assert r["safety_level"] == "medium"


class TestFilteredViews:
    def test_requirements_for_component_ecu(self):
        reqs = requirements_for_component("Engine Control Unit")
        assert len(reqs) >= 2
        assert all("Engine Control Unit" in r["component"] for r in reqs)

    def test_requirements_for_component_case_insensitive(self):
        upper = requirements_for_component("ENGINE CONTROL")
        lower = requirements_for_component("engine control")
        assert len(upper) == len(lower)

    def test_requirements_for_safety_level_release_blocking(self):
        reqs = requirements_for_safety_level("release_blocking")
        assert len(reqs) >= 2
        assert all(r["safety_level"] == "release_blocking" for r in reqs)

    def test_requirements_by_id_returns_correct_subset(self):
        reqs = requirements_by_id("PT-REQ-001", "PT-REQ-010")
        ids = {r["id"] for r in reqs}
        assert ids == {"PT-REQ-001", "PT-REQ-010"}

    def test_requirements_by_id_unknown_id_ignored(self):
        reqs = requirements_by_id("PT-REQ-001", "PT-REQ-NONEXISTENT")
        assert len(reqs) == 1
        assert reqs[0]["id"] == "PT-REQ-001"


class TestToCsv:
    def test_csv_has_header(self):
        text = to_csv()
        reader = csv.DictReader(io.StringIO(text))
        assert "id" in reader.fieldnames
        assert "metric" in reader.fieldnames
        assert "threshold" in reader.fieldnames

    def test_csv_row_count_matches_catalogue(self):
        text = to_csv()
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == len(POWERTRAIN_REQUIREMENTS)

    def test_csv_subset_works(self):
        subset = requirements_by_id("PT-REQ-001")
        text = to_csv(subset)
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["id"] == "PT-REQ-001"

    def test_csv_threshold_is_numeric_string(self):
        text = to_csv()
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            float(row["threshold"])  # must not raise


# ===========================================================================
# fixtures.py
# ===========================================================================

class TestFixtureStructure:
    REQUIRED_KEYS = {"baseline", "current", "requirements", "component_map",
                     "change_description", "_expected"}

    @pytest.mark.parametrize("fixture", [
        OVERSPEED_REGRESSION,
        SHIFT_QUALITY_REGRESSION,
        EMISSIONS_IMPROVEMENT,
    ])
    def test_has_required_keys(self, fixture):
        assert self.REQUIRED_KEYS <= fixture.keys()

    @pytest.mark.parametrize("fixture", [
        OVERSPEED_REGRESSION,
        SHIFT_QUALITY_REGRESSION,
        EMISSIONS_IMPROVEMENT,
    ])
    def test_baseline_has_avera_schema(self, fixture):
        bl = fixture["baseline"]
        assert "runId" in bl
        assert "stage" in bl
        assert "tests" in bl
        assert bl["stage"] == "baseline"

    @pytest.mark.parametrize("fixture", [
        OVERSPEED_REGRESSION,
        SHIFT_QUALITY_REGRESSION,
        EMISSIONS_IMPROVEMENT,
    ])
    def test_current_has_avera_schema(self, fixture):
        cur = fixture["current"]
        assert "runId" in cur
        assert cur["stage"] == "current"
        assert isinstance(cur["tests"], list)

    def test_overspeed_has_failing_current_test(self):
        tests = OVERSPEED_REGRESSION["current"]["tests"]
        failed = [t for t in tests if t["status"] == "failed"]
        assert len(failed) >= 1

    def test_shift_quality_has_failing_current_test(self):
        tests = SHIFT_QUALITY_REGRESSION["current"]["tests"]
        failed = [t for t in tests if t["status"] == "failed"]
        assert len(failed) >= 1

    def test_emissions_has_all_passing_tests(self):
        for t in EMISSIONS_IMPROVEMENT["current"]["tests"]:
            assert t["status"] == "passed"

    def test_overspeed_rpm_exceeds_threshold(self):
        # The failing test must actually breach the PT-REQ-001 threshold
        failing = next(
            t for t in OVERSPEED_REGRESSION["current"]["tests"]
            if t["status"] == "failed"
        )
        assert failing["metrics"][Metrics.MAX_ENGINE_RPM] > THRESHOLDS[Metrics.MAX_ENGINE_RPM]

    def test_shift_quality_torque_hole_exceeds_threshold(self):
        failing = next(
            t for t in SHIFT_QUALITY_REGRESSION["current"]["tests"]
            if t["status"] == "failed"
        )
        assert failing["metrics"][Metrics.TORQUE_HOLE_MS] > THRESHOLDS[Metrics.TORQUE_HOLE_MS]

    def test_all_fixtures_registered(self):
        assert "powertrain-overspeed-regression" in ALL_FIXTURES
        assert "powertrain-shift-quality" in ALL_FIXTURES
        assert "powertrain-emissions-ok" in ALL_FIXTURES

    def test_get_fixture_returns_correct_fixture(self):
        f = get_fixture("powertrain-overspeed-regression")
        assert f is OVERSPEED_REGRESSION

    def test_get_fixture_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown powertrain fixture"):
            get_fixture("does-not-exist")

    def test_requirements_are_subset_of_catalogue(self):
        catalogue_ids = {r["id"] for r in POWERTRAIN_REQUIREMENTS}
        for fixture in ALL_FIXTURES.values():
            for req in fixture["requirements"]:
                assert req["id"] in catalogue_ids


# ===========================================================================
# End-to-end: avera.core.analyze() using on-disk fixture files
# ===========================================================================

class TestPowertrainEndToEnd:
    """Run the full AVERA pipeline against the powertrain fixture directories."""

    _FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures"

    def _analyze(self, fixture_name: str) -> dict:
        from avera.core import analyze
        d = self._FIXTURE_ROOT / fixture_name
        return analyze(
            baseline_path=d / "baseline_results.json",
            current_path=d / "current_results.json",
            requirements_path=d / "requirements.csv",
            component_map_path=d / "component_map.json",
            change_description_path=d / "change_description.txt",
        )

    def test_overspeed_verdict_confirmed_regression(self):
        report = self._analyze("powertrain-overspeed-regression")
        assert report["verdict"] == "confirmed_regression"

    def test_overspeed_risk_release_blocking(self):
        # ASIL-D requirement + confirmed regression → release_blocking
        report = self._analyze("powertrain-overspeed-regression")
        assert report["risk"] == "release_blocking"

    def test_shift_quality_verdict_confirmed_regression(self):
        report = self._analyze("powertrain-shift-quality")
        assert report["verdict"] == "confirmed_regression"

    def test_shift_quality_risk_medium(self):
        # ASIL-B requirement → medium risk
        report = self._analyze("powertrain-shift-quality")
        assert report["risk"] == "medium"

    def test_emissions_verdict_successful_change(self):
        # All passing baseline + all passing current → successful_change
        report = self._analyze("powertrain-emissions-ok")
        assert report["verdict"] == "successful_change"

    def test_emissions_risk_low(self):
        report = self._analyze("powertrain-emissions-ok")
        assert report["risk"] == "low"

    def test_overspeed_affected_components_contains_ecu(self):
        report = self._analyze("powertrain-overspeed-regression")
        components = report.get("affected_components", [])
        assert any("Engine Control Unit" in c for c in components)

    def test_shift_quality_affected_components_contains_tcu(self):
        report = self._analyze("powertrain-shift-quality")
        components = report.get("affected_components", [])
        assert any("Transmission Control Unit" in c for c in components)

    def test_report_has_schema_version(self):
        report = self._analyze("powertrain-overspeed-regression")
        assert "schema_version" in report
