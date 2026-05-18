"""Determinism regression tests for the AVERA kernel.

Verifies that identical inputs always produce bit-for-bit identical outputs
across multiple independent runs. Any non-determinism in classification,
comparison, confidence scoring, or report serialisation is a regression.
"""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import pytest

from avera.cli import run_analyze
from avera.compare import compare_runs
from avera.classify import classify_risk
from avera.ingestion import load_component_map, load_requirements, load_verification_results
from avera.reports import assessment_to_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_fixture(name: str) -> Path:
    """Return path to a fixture directory relative to project root."""
    root = Path(__file__).resolve().parents[1]
    return root / "fixtures" / name


def _run_to_dict(fixture_path: Path, tmp_root: Path, run_index: int) -> dict:
    """Run run_analyze on fixture_path into an isolated subdirectory."""
    out = tmp_root / f"run_{run_index}"
    rc = run_analyze(fixture_path, out)
    assert rc == 0, f"run_analyze failed with code {rc} on run {run_index}"
    report = json.loads((out / "avera-report.json").read_text(encoding="utf-8"))
    return report


def _reports_equal(a: dict, b: dict, *, ignore_keys: set[str] | None = None) -> list[str]:
    """Return list of differing fields between two report dicts."""
    ignore = ignore_keys or set()
    diffs = []
    all_keys = set(a) | set(b)
    for key in sorted(all_keys):
        if key in ignore:
            continue
        if a.get(key) != b.get(key):
            diffs.append(f"  {key}: {a.get(key)!r} != {b.get(key)!r}")
    return diffs


# ---------------------------------------------------------------------------
# Core verdict/risk/confidence fields are deterministic
# ---------------------------------------------------------------------------

class TestVerdictDeterminism:
    @pytest.mark.parametrize("fixture_name", [
        "bms-fast-charge",
        "bms-successful-change",
        "bms-preexisting-failure",
        "bms-mixed-results",
        "adas-pedestrian-detection-regression",
        "adas-model-update-regression",
    ])
    def test_verdict_identical_across_runs(self, fixture_name, tmp_path):
        fixture = _load_fixture(fixture_name)
        r1 = _run_to_dict(fixture, tmp_path, 1)
        r2 = _run_to_dict(fixture, tmp_path, 2)
        r3 = _run_to_dict(fixture, tmp_path, 3)

        assert r1["verdict"] == r2["verdict"] == r3["verdict"], (
            f"{fixture_name}: verdict not deterministic: {r1['verdict']!r}, {r2['verdict']!r}, {r3['verdict']!r}"
        )

    @pytest.mark.parametrize("fixture_name", [
        "bms-fast-charge",
        "bms-successful-change",
        "bms-preexisting-failure",
        "bms-mixed-results",
        "adas-pedestrian-detection-regression",
        "adas-model-update-regression",
    ])
    def test_risk_identical_across_runs(self, fixture_name, tmp_path):
        fixture = _load_fixture(fixture_name)
        r1 = _run_to_dict(fixture, tmp_path, 1)
        r2 = _run_to_dict(fixture, tmp_path, 2)

        assert r1["risk"] == r2["risk"], (
            f"{fixture_name}: risk not deterministic: {r1['risk']!r} vs {r2['risk']!r}"
        )

    @pytest.mark.parametrize("fixture_name", [
        "bms-fast-charge",
        "bms-successful-change",
        "adas-model-update-regression",
    ])
    def test_confidence_score_identical_across_runs(self, fixture_name, tmp_path):
        fixture = _load_fixture(fixture_name)
        r1 = _run_to_dict(fixture, tmp_path, 1)
        r2 = _run_to_dict(fixture, tmp_path, 2)

        assert r1["confidence_score"] == r2["confidence_score"], (
            f"{fixture_name}: confidence_score not deterministic: "
            f"{r1['confidence_score']!r} vs {r2['confidence_score']!r}"
        )


# ---------------------------------------------------------------------------
# Full report structure is deterministic
# ---------------------------------------------------------------------------

class TestFullReportDeterminism:
    STABLE_KEYS = {
        "verdict", "risk", "confidence", "confidence_score",
        "schema_version", "rules_triggered", "confidence_factors",
        "risk_drivers", "affected_requirements", "affected_components",
        "affected_files", "recommended_next_checks",
    }

    @pytest.mark.parametrize("fixture_name", [
        "bms-fast-charge",
        "bms-worsened-preexisting",
        "bms-insufficient-evidence",
        "bms-coverage-gap",
        "bms-environment-failure",
    ])
    def test_stable_fields_identical(self, fixture_name, tmp_path):
        fixture = _load_fixture(fixture_name)
        r1 = _run_to_dict(fixture, tmp_path, 1)
        r2 = _run_to_dict(fixture, tmp_path, 2)

        for key in self.STABLE_KEYS:
            assert r1.get(key) == r2.get(key), (
                f"{fixture_name}: field '{key}' not deterministic: "
                f"{r1.get(key)!r} vs {r2.get(key)!r}"
            )

    def test_threshold_evidence_order_stable(self, tmp_path):
        """threshold_evidence list order must be stable across runs."""
        fixture = _load_fixture("bms-fast-charge")
        r1 = _run_to_dict(fixture, tmp_path, 1)
        r2 = _run_to_dict(fixture, tmp_path, 2)

        ev1 = [(e["requirement_id"], e["metric"]) for e in r1.get("threshold_evidence", [])]
        ev2 = [(e["requirement_id"], e["metric"]) for e in r2.get("threshold_evidence", [])]
        assert ev1 == ev2, f"threshold_evidence order not stable: {ev1} vs {ev2}"

    def test_rules_triggered_order_stable(self, tmp_path):
        """rules_triggered list order must be stable across runs."""
        fixture = _load_fixture("bms-fast-charge")
        r1 = _run_to_dict(fixture, tmp_path, 1)
        r2 = _run_to_dict(fixture, tmp_path, 2)

        assert r1["rules_triggered"] == r2["rules_triggered"], (
            f"rules_triggered order not stable: {r1['rules_triggered']} vs {r2['rules_triggered']}"
        )

    def test_introduced_failures_stable(self, tmp_path):
        """introduced_failures content must be identical across runs."""
        fixture = _load_fixture("bms-fast-charge")
        r1 = _run_to_dict(fixture, tmp_path, 1)
        r2 = _run_to_dict(fixture, tmp_path, 2)

        ids1 = [f["test_id"] for f in r1.get("introduced_failures", [])]
        ids2 = [f["test_id"] for f in r2.get("introduced_failures", [])]
        assert ids1 == ids2, f"introduced_failures not stable: {ids1} vs {ids2}"


# ---------------------------------------------------------------------------
# Pipeline layer determinism — compare and classify in isolation
# ---------------------------------------------------------------------------

class TestPipelineLayerDeterminism:
    def _load_bms_fast_charge(self) -> tuple:
        fixture = _load_fixture("bms-fast-charge")
        requirements = load_requirements(fixture / "requirements.csv")
        component_map = load_component_map(fixture / "component_map.json")
        baseline = load_verification_results(fixture / "baseline_results.json")
        current = load_verification_results(fixture / "current_results.json")
        return requirements, component_map, baseline, current

    def test_comparison_is_deterministic(self):
        requirements, component_map, baseline, current = self._load_bms_fast_charge()
        c1 = compare_runs(baseline=baseline, current=current)
        c2 = compare_runs(baseline=baseline, current=current)
        assert c1 == c2, "compare_runs not deterministic"

    def test_classification_is_deterministic(self):
        requirements, component_map, baseline, current = self._load_bms_fast_charge()
        comparison = compare_runs(baseline=baseline, current=current)
        a1 = classify_risk(comparison=comparison, requirements=requirements, component_map=component_map)
        a2 = classify_risk(comparison=comparison, requirements=requirements, component_map=component_map)
        assert a1.verdict == a2.verdict
        assert a1.risk == a2.risk
        assert a1.confidence == a2.confidence
        assert a1.confidence_score == a2.confidence_score

    def test_assessment_dict_is_deterministic(self):
        requirements, component_map, baseline, current = self._load_bms_fast_charge()
        comparison = compare_runs(baseline=baseline, current=current)
        assessment = classify_risk(comparison=comparison, requirements=requirements, component_map=component_map)
        d1 = assessment_to_dict(assessment)
        d2 = assessment_to_dict(assessment)
        assert d1 == d2, "assessment_to_dict not deterministic"

    def test_report_json_keys_sorted(self, tmp_path):
        """JSON report keys must be sorted for stable diffs in version control."""
        fixture = _load_fixture("bms-fast-charge")
        out = tmp_path / "out"
        run_analyze(fixture, out)
        raw = (out / "avera-report.json").read_text(encoding="utf-8")
        parsed = json.loads(raw)
        # Top-level keys must be in sorted order
        keys_in_file = list(parsed.keys())
        assert keys_in_file == sorted(keys_in_file), (
            f"JSON report keys not sorted: {keys_in_file}"
        )


# ---------------------------------------------------------------------------
# Cross-fixture determinism — adapted scenarios match originals
# ---------------------------------------------------------------------------

class TestAdaptedFixtureDeterminism:
    """Adapted fixtures must produce same verdict/risk/confidence as originals."""

    def test_log_adapted_matches_fast_charge_verdict(self, tmp_path):
        r_orig = _run_to_dict(_load_fixture("bms-fast-charge"), tmp_path / "orig", 1)
        r_adpt = _run_to_dict(_load_fixture("bms-log-adapted"), tmp_path / "adpt", 1)
        assert r_orig["verdict"] == r_adpt["verdict"], (
            f"log-adapted verdict {r_adpt['verdict']!r} != original {r_orig['verdict']!r}"
        )
        assert r_orig["risk"] == r_adpt["risk"]

    def test_requirements_adapted_matches_fast_charge_verdict(self, tmp_path):
        r_orig = _run_to_dict(_load_fixture("bms-fast-charge"), tmp_path / "orig", 1)
        r_adpt = _run_to_dict(_load_fixture("bms-requirements-adapted"), tmp_path / "adpt", 1)
        assert r_orig["verdict"] == r_adpt["verdict"], (
            f"requirements-adapted verdict {r_adpt['verdict']!r} != original {r_orig['verdict']!r}"
        )

    def test_simulation_adapted_matches_pedestrian_regression_verdict(self, tmp_path):
        r_orig = _run_to_dict(_load_fixture("adas-pedestrian-detection-regression"), tmp_path / "orig", 1)
        r_adpt = _run_to_dict(_load_fixture("adas-simulation-adapted"), tmp_path / "adpt", 1)
        assert r_orig["verdict"] == r_adpt["verdict"]
        assert r_orig["risk"] == r_adpt["risk"]


# ---------------------------------------------------------------------------
# Idempotency — running twice on same output dir gives same result
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_rerun_overwrites_cleanly(self, tmp_path):
        """Second run on same output directory must produce identical report."""
        fixture = _load_fixture("bms-fast-charge")
        out = tmp_path / "out"

        run_analyze(fixture, out)
        r1 = json.loads((out / "avera-report.json").read_text(encoding="utf-8"))

        run_analyze(fixture, out)
        r2 = json.loads((out / "avera-report.json").read_text(encoding="utf-8"))

        diffs = _reports_equal(r1, r2)
        assert not diffs, "Re-run produced different report:\n" + "\n".join(diffs)

    def test_evidence_graph_rerun_stable(self, tmp_path):
        """Evidence graph must be identical across runs."""
        fixture = _load_fixture("bms-fast-charge")
        out = tmp_path / "out"

        run_analyze(fixture, out)
        g1 = json.loads((out / "avera-evidence-graph.json").read_text(encoding="utf-8"))

        run_analyze(fixture, out)
        g2 = json.loads((out / "avera-evidence-graph.json").read_text(encoding="utf-8"))

        assert g1 == g2, "Evidence graph not idempotent across runs"
