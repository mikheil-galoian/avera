"""Adversarial-hardening tests: the comparator must fail CLOSED on unusual statuses.

Locks in fixes for failure-hiding holes found by the adversarial audit: a current
failure must never be dropped because its status word is unfamiliar, and a
non-pass baseline must not mask a current failure.
"""

from __future__ import annotations

from avera.compare.baseline_comparator import compare_runs


def _run(rid, tests):
    return {"runId": rid, "tests": tests}


def _classify(baseline_status, current_status):
    res = compare_runs(
        _run("b", [{"id": "T1", "status": baseline_status}]),
        _run("c", [{"id": "T1", "status": current_status}]),
    )
    return res


def test_unknown_failure_words_surface_as_introduced():
    for word in ["crash", "crashed", "segfault", "panic", "aborted", "regression", "broken", "ko"]:
        res = _classify("passed", word)
        assert len(res.introduced_failures) == 1, f"{word!r} must be an introduced failure"


def test_empty_current_status_fails_closed():
    res = _classify("passed", "")
    assert len(res.introduced_failures) == 1


def test_nonpass_baseline_then_fail_is_introduced():
    # xfail/flaky baseline that then fails must not be masked.
    for base in ["xfail", "flaky", "warning"]:
        res = _classify(base, "failed")
        # flaky/warning are unknown non-pass => treated as failure baseline => preexisting;
        # xfail is neutral => introduced. Either way the current failure is surfaced.
        surfaced = len(res.introduced_failures) + len(res.preexisting_failures)
        assert surfaced == 1, f"baseline {base!r} -> failed must surface a failure"


def test_inconclusive_is_not_a_failure():
    res = _classify("passed", "inconclusive")
    assert len(res.introduced_failures) == 0
    assert res.tests[0].classification == "changed_status"


def test_unknown_is_inconclusive_not_failure():
    res = _classify("passed", "unknown")
    assert len(res.introduced_failures) == 0


def test_skipped_is_neutral():
    res = _classify("passed", "skipped")
    assert len(res.introduced_failures) == 0


def test_clean_pass_fail_unchanged():
    assert len(_classify("passed", "failed").introduced_failures) == 1
    assert len(_classify("passed", "passed").unchanged_passes) == 1
    assert len(_classify("failed", "passed").resolved_failures) == 1
    assert len(_classify("failed", "failed").preexisting_failures) == 1
