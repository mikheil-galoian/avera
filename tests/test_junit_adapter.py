from __future__ import annotations

from pathlib import Path

from avera.adapters import adapt_junit_xml


def test_adapt_junit_xml_converts_common_testcase_states(tmp_path: Path) -> None:
    junit_xml = tmp_path / "results.xml"
    junit_xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="battery_suite">
    <testcase classname="bms.thermal" name="fast_charge_ok" time="1.25" />
    <testcase classname="bms.thermal" name="fast_charge_hot" time="1.75">
      <failure message="temperature exceeded">max_cell_temp_c above threshold</failure>
    </testcase>
    <testcase classname="bms.env" name="hil_unreachable">
      <error message="connection lost">environment not reachable</error>
    </testcase>
    <testcase classname="bms.optional" name="long_tail">
      <skipped message="not scheduled" />
    </testcase>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )

    payload = adapt_junit_xml(junit_xml, run_id="bms-junit-run", stage="hil")

    assert payload["runId"] == "bms-junit-run"
    assert payload["stage"] == "hil"
    assert "junit_xml" in payload["metadata"]["adapter"]
    assert payload["metadata"]["suite_count"] == 1

    tests = payload["tests"]
    assert len(tests) == 4

    assert tests[0]["id"] == "bms.thermal.fast_charge_ok"
    assert tests[0]["component"] == "bms.thermal"
    assert tests[0]["status"] == "passed"
    assert tests[0]["metrics"]["duration_s"] == 1.25

    assert tests[1]["status"] == "failed"
    assert "temperature exceeded" in tests[1]["evidence"]
    assert "max_cell_temp_c above threshold" in tests[1]["evidence"]
    assert tests[1]["metadata"]["failure_message"] == "temperature exceeded"

    assert tests[2]["status"] == "error"
    assert tests[2]["metadata"]["error_message"] == "connection lost"

    assert tests[3]["status"] == "skipped"
    assert tests[3]["metadata"]["skipped_message"] == "not scheduled"
