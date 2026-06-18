"""Exhaustive proof that the formal verdict table is total, consistent, and safe.

Three things are proven here, by enumerating the input space rather than spot-
checking examples:

1. **Totality of the table** — ``verdict_from_predicates`` returns a known verdict
   for *every* one of the 2**11 predicate combinations, including ones that cannot
   physically occur. No gap, no ``None``.

2. **Consistency table ↔ implementation** — for every reachable comparison shape
   (built from independent construction knobs), the production classifier
   ``_verdict`` returns exactly what the formal table says it should. The table
   and the code are two independent encodings of the same decision; this catches
   any future drift between them.

3. **Safety invariant** — an introduced regression that is not fully explained by
   an environment signal can never yield a pass-like verdict. This is the property
   whose absence was the K3 hole.
"""

from __future__ import annotations

import itertools

import pytest

from avera.classify import verdicts
from avera.classify.evidence import (
    ThresholdEvidence,
    current_threshold_failures,
    has_material_worsening,
    introduced_threshold_failures,
)
from avera.classify.risk_classifier import _verdict
from avera.classify.verdict_spec import (
    VerdictPredicates,
    is_pass_like,
    verdict_from_predicates,
)

_FIELDS = (
    "intro", "pre", "miss", "env_covers", "ithresh", "curfail",
    "incomplete", "inconclusive", "worsen", "unchanged_with_thresh", "covgap",
)


# --- 1. Totality of the formal table over the FULL boolean cube ---------------

def test_table_is_total():
    seen = set()
    for bits in itertools.product((False, True), repeat=len(_FIELDS)):
        p = VerdictPredicates(**dict(zip(_FIELDS, bits)))
        v = verdict_from_predicates(p)
        assert v in verdicts.ALL_VERDICTS, f"undefined verdict for {p}"
        seen.add(v)
    # Sanity: the table actually exercises a spread of verdicts, not one constant.
    assert len(seen) >= 6


# --- helpers to realise a comparison from independent construction knobs -------

def _te(baseline_passed, current_passed):
    return ThresholdEvidence(
        requirement_id="R", metric="m", operator="<=", threshold=1.0,
        baseline_value=0.0, current_value=0.0,
        baseline_passed=baseline_passed, current_passed=current_passed, test_id="t",
    )


def _build(knobs):
    intro, pre, miss, env, ithresh, extra_curfail, incomplete, inconclusive, worsen, unchanged, covgap = knobs

    introduced = [{"test_id": "ti", "component": "c"}] if intro else []
    preexisting = [{"test_id": "tp", "component": "c"}] if pre else []
    missing_baseline = [{"test_id": "tm"}] if miss else []

    env_signals = []
    if env:
        # Cover every introduced failure (or just emit one signal if none).
        ids = [i["test_id"] for i in introduced] or ["tx"]
        env_signals = [{"test_id": tid, "reason": "timeout"} for tid in ids]

    te = []
    if ithresh:
        te.append(_te(True, False))           # introduced threshold (also a curfail)
    if extra_curfail:
        te.append(_te(False, False))          # current fail, not an introduced threshold
    if incomplete:
        te.append(_te(None, None))            # inconclusive numeric evidence
    if unchanged:
        te.append(_te(True, True))            # a clean evaluated threshold

    tests = []
    if inconclusive:
        tests.append({"id": "tc", "classification": "changed_status"})
    if unchanged:
        tests.append({"id": "tu", "classification": "unchanged_pass"})

    worsened = [{"metric": "latency", "baseline": 100, "current": 200}] if worsen else []
    return introduced, preexisting, missing_baseline, tests, te, env_signals, worsened, covgap


def _derive(introduced, preexisting, missing_baseline, tests, te, env_signals, worsened, covgap):
    """Compute the predicate view exactly as ``_verdict`` does internally."""
    env_ids = {s["test_id"] for s in env_signals}
    intro_ids = {str(i.get("test_id", i.get("id", ""))) for i in introduced}
    unexplained = {i for i in intro_ids if i and i not in env_ids}
    return VerdictPredicates(
        intro=bool(introduced),
        pre=bool(preexisting),
        miss=bool(missing_baseline),
        env_covers=bool(env_signals) and not unexplained,
        ithresh=bool(introduced_threshold_failures(te)),
        curfail=bool(current_threshold_failures(te)),
        incomplete=any(i.current_passed is None or i.baseline_passed is None for i in te),
        inconclusive=any(t.get("classification") in {"changed_status", "insufficient_evidence"} for t in tests),
        worsen=has_material_worsening(worsened),
        unchanged_with_thresh=any(t.get("classification") == "unchanged_pass" for t in tests) and bool(te),
        covgap=covgap,
    )


_KNOBS = list(itertools.product((0, 1), repeat=11))


@pytest.mark.parametrize("knobs", _KNOBS)
def test_table_matches_implementation(knobs):
    args = _build(knobs)
    real = _verdict(args[0], args[1], args[2], args[3], args[4], args[5], args[6], [], args[7])
    spec = verdict_from_predicates(_derive(*args))
    assert real == spec, f"table≠impl for knobs={knobs}: impl={real} spec={spec}"


def test_safety_invariant_no_masked_regression():
    """An introduced failure not fully env-explained never yields a pass-like verdict."""
    for knobs in _KNOBS:
        args = _build(knobs)
        real = _verdict(args[0], args[1], args[2], args[3], args[4], args[5], args[6], [], args[7])
        derived = _derive(*args)
        if derived.intro and real == verdicts.ENVIRONMENT_FAILURE:
            continue  # only allowed escape: the env signal explains everything
        if derived.intro:
            assert not is_pass_like(real), f"introduced regression masked as {real} for {knobs}"


def test_determinism():
    for knobs in _KNOBS[:: 7]:
        args = _build(knobs)
        a = _verdict(args[0], args[1], args[2], args[3], args[4], args[5], args[6], [], args[7])
        b = _verdict(args[0], args[1], args[2], args[3], args[4], args[5], args[6], [], args[7])
        assert a == b
