"""Formal decision-table specification of the AVERA verdict function.

This module is the *precise definition* of how AVERA assigns a verdict. The
production classifier (:func:`avera.classify.risk_classifier._verdict`) is an
ordered ``if`` chain that grew case by case; this file re-expresses the exact
same logic as an explicit, total function over a small set of named boolean
**predicates**. Having two independent expressions of the same rule lets us
*prove* properties that an ``if`` chain alone cannot guarantee:

* **Totality** — every combination of predicates maps to exactly one known
  verdict; there is no input for which the verdict is undefined.
* **Consistency** — the table and the production code agree on every one of the
  enumerated predicate combinations (``tests/test_verdict_specification.py``).
  A future edit that makes them disagree is a caught error, not a silent drift.
* **Safety invariant** — an introduced regression (a test that passed in the
  baseline and fails now) that is not fully explained by an environment signal
  can never produce a pass-like verdict. This is the property whose *absence*
  was the K3 hole: a real failure masked as ``environment_failure``.

Predicate definitions (each derived from the baseline→current comparison):

``intro``       at least one introduced failure (baseline pass → current fail).
``pre``         at least one pre-existing failure (baseline fail → current fail).
``miss``        at least one current failure whose baseline result is missing.
``env_covers``  an environment signal (timeout, missing artifact, lost runner,
                …) is present AND every introduced failure is itself explained
                by such a signal. When there are no introduced failures this is
                simply "an environment signal is present".
``ithresh``     a requirement *threshold* crossed from pass (baseline) to fail
                (current) — corroborating numeric proof of a regression.
``curfail``     at least one requirement threshold fails in the current run
                (regardless of the baseline). ``ithresh`` implies ``curfail``.
``incomplete``  a threshold whose baseline or current value is missing (can't be
                evaluated) — inconclusive numeric evidence.
``inconclusive``a test whose status changed but is not recognisably pass/fail,
                or is itself flagged insufficient.
``worsen``      a metric materially worsened (direction-aware, above noise).
``unchanged_with_thresh``  every test still passes AND there is at least one
                evaluated threshold (a clean, evidence-backed run).
``covgap``      a requirement is in scope but no evidence covers it.

The ordering below is the specification. It is deliberately written as a flat,
readable sequence of guarded returns so the table can be audited line by line.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import verdicts


@dataclass(frozen=True)
class VerdictPredicates:
    """The decision-relevant boolean view of a comparison."""

    intro: bool = False
    pre: bool = False
    miss: bool = False
    env_covers: bool = False
    ithresh: bool = False
    curfail: bool = False
    incomplete: bool = False
    inconclusive: bool = False
    worsen: bool = False
    unchanged_with_thresh: bool = False
    covgap: bool = False


def verdict_from_predicates(p: VerdictPredicates) -> str:
    """Total verdict function over the predicate space — the formal table.

    Mirrors, rule for rule, the ordered logic of
    :func:`avera.classify.risk_classifier._verdict`. Returns one of
    :data:`avera.classify.verdicts.ALL_VERDICTS` for *every* input.
    """
    # 1. Environment failure only when the env signal is the WHOLE story: it
    #    explains all introduced failures and there is no threshold regression.
    if p.env_covers and not p.ithresh:
        return verdicts.ENVIRONMENT_FAILURE
    # 2. Introduced failure corroborated by a threshold crossing → regression.
    if p.intro and p.ithresh:
        return verdicts.CONFIRMED_REGRESSION
    # 3. Pre-existing failure that materially worsened → worsened pre-existing.
    if p.pre and p.curfail and p.worsen:
        return verdicts.WORSENED_PREEXISTING_FAILURE
    # 4. Any unexplained introduced failure is direct proof of a regression,
    #    even without a numeric threshold (pure pass/fail CI).
    if p.intro:
        return verdicts.CONFIRMED_REGRESSION
    # 5. Pre-existing failure still failing → pre-existing failure.
    if p.pre and p.curfail:
        return verdicts.PREEXISTING_FAILURE
    # 6. Pre-existing with material worsening but no current threshold fail.
    if p.pre and p.worsen:
        return verdicts.WORSENED_PREEXISTING_FAILURE
    # 7. Current failure with no baseline to compare → insufficient evidence.
    if p.miss and p.curfail:
        return verdicts.INSUFFICIENT_EVIDENCE
    # 8. Inconclusive / incomplete evidence → insufficient evidence.
    if p.inconclusive or p.incomplete:
        return verdicts.INSUFFICIENT_EVIDENCE
    # 9. A current threshold failure with no baseline proof → possible
    #    regression, or a coverage gap if the requirement is unmapped.
    if p.curfail:
        return verdicts.REQUIREMENTS_COVERAGE_GAP if p.covgap else verdicts.POSSIBLE_REGRESSION
    # 10. No failure but a requirement is uncovered → coverage gap.
    if p.covgap:
        return verdicts.REQUIREMENTS_COVERAGE_GAP
    # 11. Clean run with evaluated thresholds → successful change.
    if p.unchanged_with_thresh:
        return verdicts.SUCCESSFUL_CHANGE
    # 12. Default: an expected (benign) change.
    return verdicts.EXPECTED_CHANGE


# Verdicts that the deterministic gate may pass without human review. A verdict
# NOT in this set is "regression evidence present" and must block or go to
# review — used by the safety-invariant proof.
PASS_LIKE_VERDICTS = frozenset({verdicts.SUCCESSFUL_CHANGE, verdicts.EXPECTED_CHANGE})


def is_pass_like(verdict: str) -> bool:
    """Whether a verdict represents a clean, no-regression outcome."""
    return verdict in PASS_LIKE_VERDICTS
