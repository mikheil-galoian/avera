"""Tests for the Vector CANoe adapter (XML and ASC formats)."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from avera.adapters.canoe import (
    CANoeAdapter,
    adapt_canoe_asc,
    adapt_canoe_xml,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# CANoe XML — sample fixtures
# ---------------------------------------------------------------------------

_XML_TEFREPORT = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <TEF_Report>
      <TestGroup Name="BMS_Thermal">
        <TestCase Name="BMS-TC-001" Verdict="passed" Duration="1.24">
          <Measurement Name="max_cell_temp_c" Value="48.3"/>
          <Description>Cell temperature within limit during fast charge.</Description>
        </TestCase>
        <TestCase Name="BMS-TC-002" Verdict="failed" Duration="0.87">
          <Measurement Name="cooling_response_ms" Value="512.0"/>
          <ErrorText>Cooling response exceeded threshold of 500 ms.</ErrorText>
        </TestCase>
        <TestCase Name="BMS-TC-003" Verdict="notexec"/>
      </TestGroup>
    </TEF_Report>
"""

_XML_TESTREPORT = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <TestReport>
      <TestCase Name="ADAS-TC-PEDESTRIAN" Verdict="passed">
        <Measurement Name="detection_rate" Value="0.973"/>
      </TestCase>
      <TestCase Name="ADAS-TC-BRAKE-LAT" Verdict="failed">
        <ErrorText>Brake latency exceeded 150 ms</ErrorText>
      </TestCase>
    </TestReport>
"""

_XML_NESTED_GROUPS = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <TEF_Report>
      <TestGroup Name="Domain_A">
        <TestGroup Name="SubGroup_1">
          <TestCase Name="TC-01" Verdict="passed"/>
          <TestCase Name="TC-02" Verdict="failed"/>
        </TestGroup>
        <TestCase Name="TC-03" Verdict="passed"/>
      </TestGroup>
    </TEF_Report>
"""


# ---------------------------------------------------------------------------
# adapt_canoe_xml — basic parsing
# ---------------------------------------------------------------------------

class TestAdaptCanoeXml:
    def test_basic_tef_report_returns_dict(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        assert isinstance(result, dict)

    def test_run_id_and_stage_preserved(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="baseline-v2", stage="baseline")
        assert result["runId"] == "baseline-v2"
        assert result["stage"] == "baseline"

    def test_correct_test_count(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        assert len(result["tests"]) == 3

    def test_passed_verdict_mapped(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        passed = next(t for t in result["tests"] if t["id"] == "BMS_Thermal.BMS-TC-001")
        assert passed["status"] == "passed"

    def test_failed_verdict_mapped(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        failed = next(t for t in result["tests"] if t["id"] == "BMS_Thermal.BMS-TC-002")
        assert failed["status"] == "failed"

    def test_notexec_mapped_to_skipped(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        skipped = next(t for t in result["tests"] if t["id"] == "BMS_Thermal.BMS-TC-003")
        assert skipped["status"] == "skipped"

    def test_metrics_extracted(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        tc1 = next(t for t in result["tests"] if "BMS-TC-001" in t["id"])
        assert abs(tc1["metrics"]["max_cell_temp_c"] - 48.3) < 1e-9

    def test_duration_in_metrics(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        tc1 = next(t for t in result["tests"] if "BMS-TC-001" in t["id"])
        assert "duration_s" in tc1["metrics"]
        assert abs(tc1["metrics"]["duration_s"] - 1.24) < 1e-9

    def test_evidence_from_error_text(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        tc2 = next(t for t in result["tests"] if "BMS-TC-002" in t["id"])
        assert "500" in tc2["evidence"]

    def test_group_prefix_in_id(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        ids = [t["id"] for t in result["tests"]]
        assert all(id_.startswith("BMS_Thermal.") for id_ in ids)

    def test_nested_groups_flatten(self, tmp_path):
        f = _write(tmp_path, "nested.xml", _XML_NESTED_GROUPS)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        ids = [t["id"] for t in result["tests"]]
        assert "Domain_A.SubGroup_1.TC-01" in ids
        assert "Domain_A.TC-03" in ids

    def test_testreport_root_supported(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TESTREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        assert len(result["tests"]) == 2

    def test_metadata_present(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        result = adapt_canoe_xml(f, run_id="r1", stage="current")
        assert result["metadata"]["adapter"] == "canoe_xml.v1"
        assert result["metadata"]["test_count"] == 3

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            adapt_canoe_xml(tmp_path / "missing.xml", run_id="r1", stage="current")

    def test_malformed_xml_raises(self, tmp_path):
        f = tmp_path / "bad.xml"
        f.write_text("<broken>not closed")
        with pytest.raises(ValueError, match="parse error"):
            adapt_canoe_xml(f, run_id="r1", stage="current")

    def test_no_test_cases_raises(self, tmp_path):
        f = tmp_path / "empty.xml"
        f.write_text("<TestReport></TestReport>")
        with pytest.raises(ValueError, match="no test cases"):
            adapt_canoe_xml(f, run_id="r1", stage="current")


# ---------------------------------------------------------------------------
# adapt_canoe_asc — Vector ASC log
# ---------------------------------------------------------------------------

_ASC_BASIC = """\
    date Thu May  9 12:00:00 2026
    base hex  timestamps absolute
    // AVERA: BMS-HIL-FASTCHARGE-07 passed max_cell_temp_c=48.3 cooling_response_ms=487.0
    0.001000 1  123  Rx d 8 02 10 03 AA BB CC DD EE
    // AVERA: BMS-HIL-FASTCHARGE-08 failed max_cell_temp_c=51.2
    // AVERA: BMS-HIL-FASTCHARGE-09 skipped
"""

_ASC_UDS = """\
    date Thu May  9 12:00:00 2026
    base hex  timestamps absolute
    0.100000 1  7E8  Rx d 4 62 F2 01 0
    0.200000 1  7E8  Rx d 4 62 F2 02 1
"""

_ASC_MIXED = _ASC_BASIC + _ASC_UDS


class TestAdaptCanoeAsc:
    def test_basic_returns_dict(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        assert isinstance(result, dict)

    def test_run_id_stage_preserved(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="asc-run-1", stage="baseline")
        assert result["runId"] == "asc-run-1"
        assert result["stage"] == "baseline"

    def test_annotation_count(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        assert len(result["tests"]) == 3

    def test_passed_status(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "BMS-HIL-FASTCHARGE-07")
        assert t["status"] == "passed"

    def test_failed_status(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "BMS-HIL-FASTCHARGE-08")
        assert t["status"] == "failed"

    def test_skipped_status(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "BMS-HIL-FASTCHARGE-09")
        assert t["status"] == "skipped"

    def test_metrics_extracted(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "BMS-HIL-FASTCHARGE-07")
        assert abs(t["metrics"]["max_cell_temp_c"] - 48.3) < 1e-9
        assert abs(t["metrics"]["cooling_response_ms"] - 487.0) < 1e-9

    def test_uds_results_parsed(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_UDS)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        ids = [t["id"] for t in result["tests"]]
        assert "DID_F201" in ids
        assert "DID_F202" in ids

    def test_uds_passed_verdict(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_UDS)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "DID_F201")
        assert t["status"] == "passed"

    def test_uds_failed_verdict(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_UDS)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "DID_F202")
        assert t["status"] == "failed"

    def test_metadata_has_counts(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        assert result["metadata"]["annotation_count"] == 3
        assert result["metadata"]["test_count"] == 3

    def test_no_annotations_raises(self, tmp_path):
        f = _write(tmp_path, "empty.asc", "date Thu May  9\n0.001 1 123 Rx d 3 AA BB CC\n")
        with pytest.raises(ValueError, match="no AVERA test annotations"):
            adapt_canoe_asc(f, run_id="r1", stage="current")

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            adapt_canoe_asc(tmp_path / "missing.asc", run_id="r1", stage="current")

    def test_worst_status_wins_on_duplicate_id(self, tmp_path):
        content = textwrap.dedent("""\
            // AVERA: TC-1 passed
            // AVERA: TC-1 failed
        """)
        f = tmp_path / "dup.asc"
        f.write_text(content)
        result = adapt_canoe_asc(f, run_id="r1", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "TC-1")
        assert t["status"] == "failed"


# ---------------------------------------------------------------------------
# CANoeAdapter class (SDK interface)
# ---------------------------------------------------------------------------

class TestCANoeAdapter:
    def test_name_and_version(self):
        adapter = CANoeAdapter()
        assert adapter.name == "canoe"
        assert adapter.version == "1.0.0"

    def test_adapt_dispatches_xml(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        adapter = CANoeAdapter()
        result = adapter.adapt(f, run_id="r1", stage="current")
        assert result["metadata"]["source_format"] == "canoe_xml"

    def test_adapt_dispatches_asc(self, tmp_path):
        f = _write(tmp_path, "run.asc", _ASC_BASIC)
        adapter = CANoeAdapter()
        result = adapter.adapt(f, run_id="r1", stage="current")
        assert result["metadata"]["source_format"] == "canoe_asc"

    def test_adapt_unknown_extension_raises(self, tmp_path):
        f = tmp_path / "run.txt"
        f.write_text("x")
        adapter = CANoeAdapter()
        with pytest.raises(ValueError, match="unsupported file extension"):
            adapter.adapt(f, run_id="r1", stage="current")

    def test_can_handle_asc(self, tmp_path):
        f = tmp_path / "run.asc"
        f.write_text("x")
        assert CANoeAdapter().can_handle(f) is True

    def test_can_handle_canoe_xml(self, tmp_path):
        f = _write(tmp_path, "report.xml", _XML_TEFREPORT)
        assert CANoeAdapter().can_handle(f) is True

    def test_can_handle_junit_xml_returns_false(self, tmp_path):
        f = tmp_path / "junit.xml"
        f.write_text('<testsuite><testcase name="x"/></testsuite>')
        assert CANoeAdapter().can_handle(f) is False

    def test_metadata_keys(self):
        adapter = CANoeAdapter()
        meta = adapter.metadata
        assert meta["adapter_name"] == "canoe"
        assert "adapter_version" in meta
        assert "source_format" in meta

    def test_repr(self):
        assert "canoe" in repr(CANoeAdapter())
