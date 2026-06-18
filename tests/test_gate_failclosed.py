"""Adversarial-hardening tests: the gate must fail CLOSED on degenerate input.

These lock in fixes for holes found by the adversarial audit (see
docs/AVERA_ADVERSARIAL_HARDENING.md): a gate must never pass on malformed evidence.
"""

from __future__ import annotations

import math

from avera.gates import evaluate_gate


def _r(**kw):
    base = {"verdict": "successful_change", "risk": "low", "confidence": "high", "confidence_score": 0.95}
    base.update(kw)
    return base


# --- non-finite confidence must not satisfy the minimum ---------------------

def test_nan_confidence_does_not_pass():
    d = evaluate_gate(_r(confidence_score=float("nan")))
    assert d.status != "pass"
    assert d.report_summary["confidence_score"] is None


def test_inf_confidence_does_not_pass():
    assert evaluate_gate(_r(confidence_score=float("inf"))).status != "pass"


def test_bool_confidence_is_treated_as_malformed():
    # True would coerce to 1.0 and sail past the minimum — must not.
    assert evaluate_gate(_r(confidence_score=True)).status != "pass"


# --- unknown / mis-cased risk must fail closed ------------------------------

def test_unknown_risk_string_blocks():
    d = evaluate_gate(_r(risk="ATOMIC_MELTDOWN"))
    assert d.status == "block"
    assert any("unrecognised risk" in r for r in d.reasons)


def test_uppercase_risk_is_normalised_not_passed_as_safe():
    # "HIGH" must be read as high risk (block under default medium ceiling),
    # not silently treated as the safest rank.
    assert evaluate_gate(_r(risk="HIGH")).status == "block"


def test_empty_risk_defaults_to_unknown_recognised():
    d = evaluate_gate(_r(risk=""))
    assert d.report_summary["risk"] == "unknown"
    assert d.status == "pass"  # unknown rank 0, successful_change, good confidence


# --- non-string verdict must not bypass blocking ----------------------------

def test_list_wrapped_blocking_verdict_does_not_pass():
    d = evaluate_gate(_r(verdict=["confirmed_regression"], risk="high"))
    assert d.status != "pass"


def test_uppercase_blocking_verdict_still_blocks():
    assert evaluate_gate(_r(verdict="CONFIRMED_REGRESSION", risk="high")).status == "block"


# --- valid inputs unchanged (regression guard) ------------------------------

def test_valid_confirmed_regression_still_blocks():
    assert evaluate_gate(_r(verdict="confirmed_regression", risk="high")).status == "block"


def test_valid_successful_change_still_passes():
    d = evaluate_gate(_r())
    assert d.status == "pass"
    assert d.report_summary["confidence_score"] == 0.95
