"""K3: an environment signal must not mask a real introduced regression.

A test that goes passed→timeout, when it is the ONLY failure, is treated as an
environment failure (review). But a real introduced failure (pass→fail) that is
NOT an environment pattern must NOT be downgraded to environment_failure just
because some *other* test timed out — it is a confirmed regression.
"""

from __future__ import annotations

from avera.classify.risk_classifier import classify_risk
from avera.classify import verdicts


def _cmp(introduced, tests):
    return {"introduced_failures": introduced, "preexisting_failures": [],
            "missing_baseline": [], "tests": tests, "metric_deltas": []}


def test_lone_timeout_stays_environment_failure():
    cmp = _cmp(
        introduced=[{"test_id": "t_slow", "component": "c"}],
        tests=[{"id": "t_slow", "status": "timeout", "classification": "introduced_failure"}],
    )
    assert classify_risk(cmp).verdict == verdicts.ENVIRONMENT_FAILURE


def test_real_failure_alongside_timeout_is_regression():
    cmp = _cmp(
        introduced=[
            {"test_id": "t_slow", "component": "c"},   # env-pattern timeout
            {"test_id": "t_logic", "component": "c"},  # genuine assertion failure
        ],
        tests=[
            {"id": "t_slow", "status": "timeout", "classification": "introduced_failure"},
            {"id": "t_logic", "status": "failed", "classification": "introduced_failure"},
        ],
    )
    # The unexplained introduced failure must dominate — not be masked as infra.
    assert classify_risk(cmp).verdict == verdicts.CONFIRMED_REGRESSION
