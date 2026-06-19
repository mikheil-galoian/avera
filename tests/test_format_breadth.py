"""`avera check` must work on JUnit XML from any toolchain, not only pytest.

jest (jest-junit) and go (go-junit-report / gotestsum) emit standard JUnit XML
with slightly different shapes. This locks in that AVERA catches an introduced
regression in each, so the "works with anything that emits JUnit" claim is real.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from avera.cli import run_check

# jest-junit shape: <testsuites><testsuite name="*.test.js"><testcase classname/name>
_JEST = """<testsuites name="jest tests">
  <testsuite name="math.test.js" tests="2" failures="{f}">
    <testcase classname="math" name="adds numbers" time="0.01"/>
    <testcase classname="math" name="subtracts numbers" time="0.01">{fail}</testcase>
  </testsuite>
</testsuites>"""

# go-junit-report shape: <testsuites><testsuite name="pkg"><testcase classname=pkg name=TestX>
_GO = """<testsuites>
  <testsuite name="pkg/calc" tests="2" failures="{f}">
    <testcase classname="pkg/calc" name="TestAdd"/>
    <testcase classname="pkg/calc" name="TestSub">{fail}</testcase>
  </testsuite>
</testsuites>"""


def _write(template: str, failing: bool) -> Path:
    fail = '<failure message="assertion">want 2 got 3</failure>' if failing else ""
    p = Path(tempfile.mkdtemp()) / "r.xml"
    p.write_text(template.format(f=1 if failing else 0, fail=fail), encoding="utf-8")
    return p


def _check(template: str, expect_id: str, capsys):
    baseline = _write(template, failing=False)
    current = _write(template, failing=True)
    run_check(baseline, current, "general", as_json=True)
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "confirmed_regression"
    assert out["gate_status"] == "block"
    assert expect_id in out["introduced_failures"]


def test_jest_junit_regression_caught(capsys):
    _check(_JEST, "math.subtracts numbers", capsys)


def test_go_junit_regression_caught(capsys):
    _check(_GO, "pkg/calc.TestSub", capsys)
