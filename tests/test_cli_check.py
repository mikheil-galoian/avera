"""Zero-config `avera check` — the broad on-ramp: two JUnit files in, gate out.

No requirements, component map, or project folder. A regression (a test that
passed on the baseline and fails now) must surface as confirmed_regression +
block with a non-zero exit code, so the command drops straight into a CI step.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from avera.cli import run_check

_PASS = '<testsuite name="s"><testcase classname="m" name="t_ok"/>{extra}</testsuite>'


def _xml(failing: bool) -> Path:
    extra = '<testcase classname="m" name="t_reg"><failure message="boom"/></testcase>' if failing \
        else '<testcase classname="m" name="t_reg"/>'
    p = Path(tempfile.mkdtemp()) / "r.xml"
    p.write_text(_PASS.format(extra=extra), encoding="utf-8")
    return p


def test_check_blocks_on_introduced_regression(capsys):
    baseline = _xml(failing=False)   # both pass
    current = _xml(failing=True)     # t_reg now fails
    code = run_check(baseline, current, "general", as_json=True)
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "confirmed_regression"
    assert out["gate_status"] == "block"
    assert "m.t_reg" in out["introduced_failures"]
    assert code != 0  # fails the CI step


def test_check_passes_when_clean(capsys):
    baseline = _xml(failing=False)
    current = _xml(failing=False)    # identical, all green
    code = run_check(baseline, current, "general", as_json=True)
    out = json.loads(capsys.readouterr().out)
    assert out["gate_status"] == "pass"
    assert out["introduced_failures"] == []
    assert code == 0


def test_check_human_output_is_readable(capsys):
    code = run_check(_xml(False), _xml(True), "automotive", as_json=False)
    text = capsys.readouterr().out
    assert "AVERA Check" in text
    assert "confirmed_regression" in text
    assert "block" in text
    assert code != 0
