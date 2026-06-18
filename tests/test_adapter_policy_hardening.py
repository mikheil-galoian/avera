"""Hardening tests for adapter status merging (K4/K5) and policy loading (Gp/Pol).

K4 — a single JUnit file with a duplicate test id (a retried test reported
     fail-then-pass) must not drop the failure.
K5 — the CSV log adapter must merge statuses fail-closed and order-independently:
     an unknown status word ranks as a failure, never tying with ``passed``.
Gp — policy_from_dict rejects malformed fields instead of silently degrading.
Pol — built-in policy resolution prefers the trusted package dir over env/cwd.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from avera.adapters.junit import adapt_junit_xml
from avera.adapters.logs import adapt_log_csv
from avera.compare.baseline_comparator import status_severity
from avera.gates.policy_loader import PolicyError, policy_from_dict


# --- shared taxonomy: unknown/empty is a failure, never a pass ---------------

def test_status_severity_fail_closed():
    assert status_severity("passed") < status_severity("skipped")
    assert status_severity("skipped") < status_severity("failed")
    assert status_severity("failed") <= status_severity("error")
    # Unknown / empty tokens outrank passed → cannot be hidden by a later pass.
    for unknown in ("crash", "segfault", "panic", "", None, "regression"):
        assert status_severity(unknown) > status_severity("passed")


# --- K4: single-file JUnit duplicate id, fail-then-pass ----------------------

def _write(text: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "r.xml"
    p.write_text(text, encoding="utf-8")
    return p


def test_junit_single_file_retry_keeps_failure():
    xml = """<testsuite name="s">
      <testcase classname="m" name="t" time="0.1"><failure message="boom"/></testcase>
      <testcase classname="m" name="t" time="0.1"/>
    </testsuite>"""
    run = adapt_junit_xml(_write(xml), run_id="r", stage="current")
    tests = [t for t in run["tests"] if t["id"] == "m.t"]
    assert len(tests) == 1, "duplicate id must be merged into one entry"
    assert tests[0]["status"] == "failed", "retry pass must not drop the failure"


# --- K5: CSV unknown status is fail-closed and order-independent --------------

def _csv(rows: str) -> Path:
    p = Path(tempfile.mkdtemp()) / "r.csv"
    p.write_text("test_id,component,status,message\n" + rows, encoding="utf-8")
    return p


def test_csv_unknown_status_does_not_lose_to_pass():
    # passed first, then an unknown failure-like status.
    a = adapt_log_csv(_csv("t,c,passed,ok\nt,c,segfault,died\n"), run_id="r", stage="current")
    # reversed order — result must be identical (order-independent).
    b = adapt_log_csv(_csv("t,c,segfault,died\nt,c,passed,ok\n"), run_id="r", stage="current")
    sa = a["tests"][0]["status"]
    sb = b["tests"][0]["status"]
    assert sa == sb == "segfault", f"unknown failure must win over passed, got {sa!r}/{sb!r}"


# --- Gp: policy validation ----------------------------------------------------

def _base(**over):
    d = {"policy_id": "p", "max_allowed_risk": "low", "min_confidence_score": 0.7}
    d.update(over)
    return d


def test_policy_rejects_nonfinite_confidence():
    with pytest.raises(PolicyError):
        policy_from_dict(_base(min_confidence_score=float("nan")))
    with pytest.raises(PolicyError):
        policy_from_dict(_base(min_confidence_score=1.5))


def test_policy_rejects_unknown_max_risk():
    with pytest.raises(PolicyError):
        policy_from_dict(_base(max_allowed_risk="bogus"))


def test_policy_rejects_bad_risk_rank_value():
    with pytest.raises(PolicyError):
        policy_from_dict(_base(risk_rank={"low": "x"}))


def test_policy_rejects_empty_id():
    with pytest.raises(PolicyError):
        policy_from_dict(_base(policy_id="   "))


def test_policy_accepts_valid_custom_rank():
    pol = policy_from_dict(_base(max_allowed_risk="hi", risk_rank={"lo": 0, "hi": 1}))
    assert pol.max_allowed_risk == "hi"


# --- Pol: env cannot swap a present built-in ---------------------------------

def test_builtin_resolves_from_package_not_env(monkeypatch):
    from avera.gates import policy_loader as pl

    # Point the env at a directory holding a *laxer* automotive policy.
    evil_dir = Path(tempfile.mkdtemp())
    (evil_dir / "automotive_policy.json").write_text(
        json.dumps({"policy_id": "evil", "max_allowed_risk": "safety_critical",
                    "min_confidence_score": 0.0}),
        encoding="utf-8",
    )
    monkeypatch.setenv("AVERA_POLICIES_DIR", str(evil_dir))
    pol = pl.load_builtin_policy("automotive")
    # The trusted package policy wins; the env copy is ignored when present.
    assert pol.policy_id != "evil"
