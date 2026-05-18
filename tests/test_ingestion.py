"""Tests for avera.ingestion — requirements, verification_results, component_map loaders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from avera.ingestion import load_component_map, load_requirements, load_verification_results
from avera.models.requirements import Requirement
from avera.models.verification import TestResult, VerificationRun


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQ_HEADER = "id,component,requirement,metric,operator,threshold,safety_level,next_checks\n"


def _req_csv(*rows: str) -> str:
    return REQ_HEADER + "\n".join(rows) + "\n"


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_requirements
# ---------------------------------------------------------------------------

class TestLoadRequirements:
    def test_loads_single_requirement(self, tmp_path):
        path = _write(
            tmp_path, "req.csv",
            _req_csv("R1,BMS,Max temp must not exceed 50C,max_temp,<=,50.0,high,BMS-HIL-007"),
        )
        reqs = load_requirements(path)
        assert len(reqs) == 1
        r = reqs[0]
        assert r.id == "R1"
        assert r.component == "BMS"
        assert r.metric == "max_temp"
        assert r.operator == "<="
        assert r.threshold == pytest.approx(50.0)
        assert r.safety_level == "high"
        assert "BMS-HIL-007" in r.next_checks

    def test_loads_multiple_requirements(self, tmp_path):
        path = _write(
            tmp_path, "req.csv",
            _req_csv(
                "R1,BMS,Req 1,max_temp,<=,50.0,high,",
                "R2,BMS,Req 2,cooling_ms,<=,500.0,medium,",
            ),
        )
        reqs = load_requirements(path)
        assert len(reqs) == 2
        ids = [r.id for r in reqs]
        assert "R1" in ids and "R2" in ids

    def test_threshold_as_float(self, tmp_path):
        path = _write(tmp_path, "req.csv", _req_csv("R1,C,R,m,<=,123.4,h,"))
        reqs = load_requirements(path)
        assert isinstance(reqs[0].threshold, float)
        assert reqs[0].threshold == pytest.approx(123.4)

    def test_threshold_as_string_when_not_numeric(self, tmp_path):
        path = _write(tmp_path, "req.csv", _req_csv("R1,C,R,m,==,pass,h,"))
        reqs = load_requirements(path)
        assert reqs[0].threshold == "pass"

    def test_raises_on_missing_required_column(self, tmp_path):
        path = _write(tmp_path, "req.csv", "id,component\nR1,BMS\n")
        with pytest.raises(ValueError, match="missing fields"):
            load_requirements(path)

    def test_returns_requirement_model_instances(self, tmp_path):
        path = _write(tmp_path, "req.csv", _req_csv("R1,C,R,m,<=,1.0,h,"))
        reqs = load_requirements(path)
        assert all(isinstance(r, Requirement) for r in reqs)

    def test_loads_bms_fast_charge_requirements(self):
        path = Path("fixtures/bms-fast-charge/requirements.csv")
        reqs = load_requirements(path)
        assert len(reqs) >= 2
        ids = [r.id for r in reqs]
        assert "BMS-REQ-112" in ids

    def test_utf8_bom_header_is_handled(self, tmp_path):
        # Write file with UTF-8 BOM using utf-8-sig encoding (no manual BOM in string)
        content = REQ_HEADER + "R1,C,R,m,<=,1.0,h,\n"
        path = tmp_path / "req.csv"
        path.write_bytes(content.encode("utf-8-sig"))
        reqs = load_requirements(path)
        assert len(reqs) == 1


# ---------------------------------------------------------------------------
# load_verification_results
# ---------------------------------------------------------------------------

class TestLoadVerificationResults:
    def _write_run(self, tmp_path, name, run_id, stage, tests):
        data = {"runId": run_id, "stage": stage, "tests": tests}
        return _write(tmp_path, name, json.dumps(data))

    def test_loads_minimal_run(self, tmp_path):
        path = self._write_run(
            tmp_path, "run.json", "run-001", "baseline",
            [{"id": "T1", "status": "passed", "metrics": {}}],
        )
        run = load_verification_results(path)
        assert isinstance(run, VerificationRun)
        assert run.run_id == "run-001"
        assert run.stage == "baseline"
        assert len(run.tests) == 1

    def test_loads_test_with_metrics(self, tmp_path):
        path = self._write_run(
            tmp_path, "run.json", "run-001", "current",
            [{"id": "T1", "status": "failed", "metrics": {"max_temp": 52.8}}],
        )
        run = load_verification_results(path)
        assert run.tests[0].metrics["max_temp"] == pytest.approx(52.8)

    def test_raises_when_tests_missing(self, tmp_path):
        data = {"runId": "r1", "stage": "baseline"}
        path = _write(tmp_path, "run.json", json.dumps(data))
        with pytest.raises(ValueError):
            load_verification_results(path)

    def test_raises_on_invalid_json(self, tmp_path):
        path = _write(tmp_path, "run.json", "NOT JSON")
        with pytest.raises((ValueError, json.JSONDecodeError, Exception)):
            load_verification_results(path)

    def test_returns_verification_run_instance(self, tmp_path):
        path = self._write_run(tmp_path, "r.json", "r1", "baseline", [{"id": "T1", "status": "passed"}])
        run = load_verification_results(path)
        assert isinstance(run, VerificationRun)

    def test_test_results_are_test_result_instances(self, tmp_path):
        path = self._write_run(tmp_path, "r.json", "r1", "baseline", [{"id": "T1", "status": "passed"}])
        run = load_verification_results(path)
        assert all(isinstance(t, TestResult) for t in run.tests)

    def test_loads_bms_baseline_fixture(self):
        path = Path("fixtures/bms-fast-charge/baseline_results.json")
        run = load_verification_results(path)
        assert run.stage == "baseline"
        assert len(run.tests) >= 1

    def test_snake_case_run_id_accepted(self, tmp_path):
        data = {"run_id": "r1", "stage": "baseline", "tests": [{"id": "T1", "status": "passed"}]}
        path = _write(tmp_path, "r.json", json.dumps(data))
        run = load_verification_results(path)
        assert run.run_id == "r1"

    def test_component_field_preserved(self, tmp_path):
        tests = [{"id": "T1", "status": "passed", "component": "BMS Thermal Control"}]
        path = self._write_run(tmp_path, "r.json", "r1", "baseline", tests)
        run = load_verification_results(path)
        assert run.tests[0].component == "BMS Thermal Control"


# ---------------------------------------------------------------------------
# load_component_map
# ---------------------------------------------------------------------------

class TestLoadComponentMap:
    def test_loads_single_mapping(self, tmp_path):
        data = {"src/bms.c": {"component": "BMS", "requirements": ["R1"], "tests": ["T1"]}}
        path = _write(tmp_path, "cmap.json", json.dumps(data))
        cmap = load_component_map(path)
        assert "src/bms.c" in cmap

    def test_loads_bms_fast_charge_component_map(self):
        path = Path("fixtures/bms-fast-charge/component_map.json")
        cmap = load_component_map(path)
        assert len(cmap) >= 1

    def test_raises_on_invalid_json(self, tmp_path):
        path = _write(tmp_path, "cmap.json", "INVALID")
        with pytest.raises((ValueError, json.JSONDecodeError, Exception)):
            load_component_map(path)

    def test_raises_when_file_does_not_exist(self, tmp_path):
        with pytest.raises((FileNotFoundError, OSError, Exception)):
            load_component_map(tmp_path / "nonexistent.json")
