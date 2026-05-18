"""Hardened tests for the JUnit / xUnit XML adapter (v1.1).

Covers:
- Backward-compatible single-file parsing
- <properties> on testcase and testsuite level
- <system-out> / <system-err> appended to evidence
- Non-numeric time attribute
- Missing classname / name attributes
- Malformed XML → ValueError
- Missing file → FileNotFoundError
- Empty testsuite → zero tests (no crash)
- Batch merge (adapt_junit_xml_batch)
- Worst-status-wins on batch deduplication
- Metrics merge on batch deduplication
- JUnitXmlAdapter class (SDK interface)
- metadata version bump to 1.1.0
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from avera.adapters.junit import (
    JUnitXmlAdapter,
    adapt_junit_xml,
    adapt_junit_xml_batch,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Fixtures — XML strings
# ---------------------------------------------------------------------------

_XML_BASIC = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuites>
      <testsuite name="bms_suite">
        <testcase classname="bms.thermal" name="fast_charge_ok" time="1.25"/>
        <testcase classname="bms.thermal" name="fast_charge_hot" time="1.75">
          <failure type="AssertionError" message="temperature exceeded">
            max_cell_temp_c above threshold
          </failure>
        </testcase>
        <testcase classname="bms.env" name="hil_unreachable">
          <error type="IOError" message="connection lost">environment not reachable</error>
        </testcase>
        <testcase classname="bms.optional" name="long_tail">
          <skipped message="not scheduled"/>
        </testcase>
      </testsuite>
    </testsuites>
"""

_XML_WITH_PROPERTIES = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="props_suite">
      <properties>
        <property name="build" value="123"/>
        <property name="env" value="hil"/>
      </properties>
      <testcase classname="drv.speed" name="max_speed" time="2.0">
        <properties>
          <property name="max_speed_kph" value="201.5"/>
          <property name="iterations" value="5"/>
          <property name="tag" value="regression"/>
        </properties>
      </testcase>
    </testsuite>
"""

_XML_WITH_SYSOUT = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="sysout_suite">
      <testcase classname="net.ping" name="latency_check" time="0.3">
        <failure message="latency too high">Latency was 312 ms</failure>
        <system-out>Ping attempt 1: 312 ms</system-out>
        <system-err>Warning: packet loss detected</system-err>
      </testcase>
    </testsuite>
"""

_XML_BARE_TESTSUITE = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="bare_suite">
      <testcase name="no_classname" time="0.1"/>
    </testsuite>
"""

_XML_EMPTY_SUITE = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuites>
      <testsuite name="empty_suite"/>
    </testsuites>
"""

_XML_NON_NUMERIC_TIME = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="timing_suite">
      <testcase classname="x" name="slow_test" time="N/A"/>
    </testsuite>
"""

_XML_BATCH_A = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="batch_a">
      <testcase classname="mod.a" name="tc1" time="1.0"/>
      <testcase classname="mod.a" name="tc2" time="2.0">
        <failure message="assertion failed"/>
      </testcase>
    </testsuite>
"""

_XML_BATCH_B = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="batch_b">
      <testcase classname="mod.a" name="tc1" time="0.5">
        <failure message="flaky failure"/>
      </testcase>
      <testcase classname="mod.b" name="tc3" time="0.8"/>
    </testsuite>
"""

_XML_BATCH_C = """\
    <?xml version="1.0" encoding="UTF-8"?>
    <testsuite name="batch_c">
      <testcase classname="mod.a" name="tc1" time="0.3">
        <error message="runtime crash"/>
      </testcase>
    </testsuite>
"""


# ---------------------------------------------------------------------------
# Single-file — basic (backward compat)
# ---------------------------------------------------------------------------

class TestAdaptJunitXmlBasic:
    def test_returns_dict(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        result = adapt_junit_xml(f, run_id="r1", stage="current")
        assert isinstance(result, dict)

    def test_run_id_stage_preserved(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        result = adapt_junit_xml(f, run_id="my-run", stage="baseline")
        assert result["runId"] == "my-run"
        assert result["stage"] == "baseline"

    def test_test_count(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        result = adapt_junit_xml(f, run_id="r1", stage="current")
        assert len(result["tests"]) == 4

    def test_suite_count_metadata(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        result = adapt_junit_xml(f, run_id="r1", stage="current")
        assert result["metadata"]["suite_count"] == 1

    def test_adapter_metadata_key(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        result = adapt_junit_xml(f, run_id="r1", stage="current")
        # v1 now (was v0); backward-compat check: key exists
        assert "adapter" in result["metadata"]
        assert "junit_xml" in result["metadata"]["adapter"]

    def test_passed_status(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        tests = adapt_junit_xml(f, run_id="r1", stage="current")["tests"]
        t = next(t for t in tests if t["id"] == "bms.thermal.fast_charge_ok")
        assert t["status"] == "passed"

    def test_failed_status_and_evidence(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        tests = adapt_junit_xml(f, run_id="r1", stage="current")["tests"]
        t = next(t for t in tests if "fast_charge_hot" in t["id"])
        assert t["status"] == "failed"
        assert "temperature exceeded" in t["evidence"]
        assert "max_cell_temp_c" in t["evidence"]

    def test_failed_metadata_keys(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        tests = adapt_junit_xml(f, run_id="r1", stage="current")["tests"]
        t = next(t for t in tests if "fast_charge_hot" in t["id"])
        assert t["metadata"]["failure_message"] == "temperature exceeded"
        assert t["metadata"]["failure_type"] == "AssertionError"

    def test_error_status(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        tests = adapt_junit_xml(f, run_id="r1", stage="current")["tests"]
        t = next(t for t in tests if "hil_unreachable" in t["id"])
        assert t["status"] == "error"
        assert t["metadata"]["error_message"] == "connection lost"
        assert t["metadata"]["error_type"] == "IOError"

    def test_skipped_status(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        tests = adapt_junit_xml(f, run_id="r1", stage="current")["tests"]
        t = next(t for t in tests if "long_tail" in t["id"])
        assert t["status"] == "skipped"
        assert t["metadata"]["skipped_message"] == "not scheduled"

    def test_duration_metric(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        tests = adapt_junit_xml(f, run_id="r1", stage="current")["tests"]
        t = next(t for t in tests if "fast_charge_ok" in t["id"])
        assert abs(t["metrics"]["duration_s"] - 1.25) < 1e-9

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            adapt_junit_xml(tmp_path / "missing.xml", run_id="r1", stage="current")

    def test_malformed_xml_raises(self, tmp_path):
        f = tmp_path / "bad.xml"
        f.write_text("<broken>not closed")
        with pytest.raises(ValueError, match="parse error"):
            adapt_junit_xml(f, run_id="r1", stage="current")

    def test_empty_suite_no_crash(self, tmp_path):
        f = _write(tmp_path, "empty.xml", _XML_EMPTY_SUITE)
        result = adapt_junit_xml(f, run_id="r1", stage="current")
        assert result["tests"] == []

    def test_bare_testsuite_root(self, tmp_path):
        f = _write(tmp_path, "bare.xml", _XML_BARE_TESTSUITE)
        result = adapt_junit_xml(f, run_id="r1", stage="current")
        assert len(result["tests"]) == 1

    def test_missing_classname_uses_suite(self, tmp_path):
        f = _write(tmp_path, "bare.xml", _XML_BARE_TESTSUITE)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert t["id"] == "no_classname"
        assert t["component"] == "bare_suite"

    def test_non_numeric_time_stored_in_metadata(self, tmp_path):
        f = _write(tmp_path, "timing.xml", _XML_NON_NUMERIC_TIME)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert "duration_s" not in t["metrics"]
        assert t["metadata"].get("duration_raw") == "N/A"


# ---------------------------------------------------------------------------
# <properties> support
# ---------------------------------------------------------------------------

class TestPropertiesParsing:
    def test_numeric_tc_property_in_metrics(self, tmp_path):
        f = _write(tmp_path, "props.xml", _XML_WITH_PROPERTIES)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert abs(t["metrics"]["max_speed_kph"] - 201.5) < 1e-9

    def test_integer_tc_property_in_metrics(self, tmp_path):
        f = _write(tmp_path, "props.xml", _XML_WITH_PROPERTIES)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert t["metrics"]["iterations"] == 5

    def test_string_tc_property_in_metadata(self, tmp_path):
        f = _write(tmp_path, "props.xml", _XML_WITH_PROPERTIES)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert t["metadata"]["prop_tag"] == "regression"

    def test_suite_numeric_property_not_in_metrics(self, tmp_path):
        # Suite 'build' is numeric but treated as suite metadata only
        f = _write(tmp_path, "props.xml", _XML_WITH_PROPERTIES)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        # build=123 is a suite-level property → stored with suite_prop_ prefix
        assert t["metadata"].get("suite_prop_build") == "123"

    def test_suite_string_property_in_metadata(self, tmp_path):
        f = _write(tmp_path, "props.xml", _XML_WITH_PROPERTIES)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert t["metadata"].get("suite_prop_env") == "hil"

    def test_duration_still_parsed_alongside_properties(self, tmp_path):
        f = _write(tmp_path, "props.xml", _XML_WITH_PROPERTIES)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert abs(t["metrics"]["duration_s"] - 2.0) < 1e-9


# ---------------------------------------------------------------------------
# <system-out> / <system-err> support
# ---------------------------------------------------------------------------

class TestSystemOutput:
    def test_system_out_in_evidence(self, tmp_path):
        f = _write(tmp_path, "sysout.xml", _XML_WITH_SYSOUT)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert "Ping attempt 1: 312 ms" in t["evidence"]

    def test_system_err_in_evidence(self, tmp_path):
        f = _write(tmp_path, "sysout.xml", _XML_WITH_SYSOUT)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert "packet loss detected" in t["evidence"]

    def test_failure_message_also_in_evidence(self, tmp_path):
        f = _write(tmp_path, "sysout.xml", _XML_WITH_SYSOUT)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert "latency too high" in t["evidence"]

    def test_tagged_system_out_label(self, tmp_path):
        f = _write(tmp_path, "sysout.xml", _XML_WITH_SYSOUT)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert "[system-out]" in t["evidence"]

    def test_tagged_system_err_label(self, tmp_path):
        f = _write(tmp_path, "sysout.xml", _XML_WITH_SYSOUT)
        t = adapt_junit_xml(f, run_id="r1", stage="current")["tests"][0]
        assert "[system-err]" in t["evidence"]


# ---------------------------------------------------------------------------
# Batch support
# ---------------------------------------------------------------------------

class TestAdaptJunitXmlBatch:
    def test_basic_merge_all_tests_present(self, tmp_path):
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        result = adapt_junit_xml_batch([a, b], run_id="batch-r1", stage="current")
        ids = {t["id"] for t in result["tests"]}
        assert "mod.a.tc1" in ids
        assert "mod.a.tc2" in ids
        assert "mod.b.tc3" in ids

    def test_run_id_stage_preserved(self, tmp_path):
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        result = adapt_junit_xml_batch([a], run_id="batch-r2", stage="baseline")
        assert result["runId"] == "batch-r2"
        assert result["stage"] == "baseline"

    def test_file_count_in_metadata(self, tmp_path):
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        result = adapt_junit_xml_batch([a, b], run_id="r", stage="current")
        assert result["metadata"]["file_count"] == 2

    def test_source_paths_in_metadata(self, tmp_path):
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        result = adapt_junit_xml_batch([a, b], run_id="r", stage="current")
        paths = result["metadata"]["source_paths"]
        assert len(paths) == 2

    def test_worst_status_wins_passed_vs_failed(self, tmp_path):
        # tc1: passed in A, failed in B → final: failed
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        result = adapt_junit_xml_batch([a, b], run_id="r", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "mod.a.tc1")
        assert t["status"] == "failed"

    def test_worst_status_wins_failed_vs_error(self, tmp_path):
        # tc1: failed in B, error in C → final: error
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        c = _write(tmp_path, "c.xml", _XML_BATCH_C)
        result = adapt_junit_xml_batch([b, c], run_id="r", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "mod.a.tc1")
        assert t["status"] == "error"

    def test_metrics_merge_later_overrides(self, tmp_path):
        # tc1: duration 1.0 in A, 0.5 in B → later (B) overrides → 0.5
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        result = adapt_junit_xml_batch([a, b], run_id="r", stage="current")
        t = next(t for t in result["tests"] if t["id"] == "mod.a.tc1")
        assert abs(t["metrics"]["duration_s"] - 0.5) < 1e-9

    def test_no_duplicates_in_result(self, tmp_path):
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        result = adapt_junit_xml_batch([a, b], run_id="r", stage="current")
        ids = [t["id"] for t in result["tests"]]
        assert len(ids) == len(set(ids))

    def test_empty_paths_raises(self, tmp_path):
        with pytest.raises(ValueError, match="no paths"):
            adapt_junit_xml_batch([], run_id="r", stage="current")

    def test_missing_file_in_batch_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            adapt_junit_xml_batch(
                [tmp_path / "ghost.xml"], run_id="r", stage="current"
            )

    def test_single_file_batch_equivalent_to_single(self, tmp_path):
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        single = adapt_junit_xml(a, run_id="r", stage="current")
        batch = adapt_junit_xml_batch([a], run_id="r", stage="current")
        # Same test IDs
        assert {t["id"] for t in single["tests"]} == {t["id"] for t in batch["tests"]}


# ---------------------------------------------------------------------------
# JUnitXmlAdapter class (SDK interface)
# ---------------------------------------------------------------------------

class TestJUnitXmlAdapter:
    def test_name_and_version(self):
        adapter = JUnitXmlAdapter()
        assert adapter.name == "junit_xml"
        assert adapter.version == "1.1.0"

    def test_metadata_version(self):
        adapter = JUnitXmlAdapter()
        assert "1.1.0" in adapter.metadata["adapter_version"]

    def test_metadata_keys(self):
        adapter = JUnitXmlAdapter()
        meta = adapter.metadata
        assert "adapter" in meta
        assert "adapter_name" in meta
        assert "adapter_version" in meta
        assert "source_format" in meta

    def test_adapt_dispatches_correctly(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        adapter = JUnitXmlAdapter()
        result = adapter.adapt(f, run_id="r1", stage="current")
        assert len(result["tests"]) == 4

    def test_adapt_batch_method_exists(self, tmp_path):
        a = _write(tmp_path, "a.xml", _XML_BATCH_A)
        b = _write(tmp_path, "b.xml", _XML_BATCH_B)
        adapter = JUnitXmlAdapter()
        result = adapter.adapt_batch([a, b], run_id="r1", stage="current")
        assert "tests" in result

    def test_can_handle_junit_xml(self, tmp_path):
        f = _write(tmp_path, "r.xml", _XML_BASIC)
        assert JUnitXmlAdapter().can_handle(f) is True

    def test_can_handle_non_xml(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b,c")
        assert JUnitXmlAdapter().can_handle(f) is False

    def test_can_handle_tef_xml_returns_false(self, tmp_path):
        # TEF_Report XML should be handled by CANoeAdapter, not JUnit
        f = tmp_path / "canoe.xml"
        f.write_text('<?xml version="1.0"?><TEF_Report/>')
        # JUnitXmlAdapter checks for testsuite/testcase in first 512 bytes
        assert JUnitXmlAdapter().can_handle(f) is False

    def test_repr_contains_name(self):
        assert "junit_xml" in repr(JUnitXmlAdapter())
