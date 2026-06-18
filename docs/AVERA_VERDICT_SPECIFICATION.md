# AVERA — Formal Verdict Specification

**Status:** the verdict assignment is now a *proven-total decision table*, not an
implicit chain of `if`s. This document is the precise definition; the table is
encoded in `src/avera/classify/verdict_spec.py` and proven against the production
classifier in `tests/test_verdict_specification.py`.

## Why this exists

A safety/regression gate for regulated domains (ISO 26262, DO-178C, EN 50128,
IEC 62304) must rest on a precise, complete definition of *when a change is a
regression* — not on the accidental ordering of code branches. The K3 hole (a
real failure masked as `environment_failure` because its status word was
`timeout`) was a symptom of a missing specification: the rule ordering had a gap
no example test had hit.

The fix is structural. The decision is re-expressed as a **total function over a
small set of named boolean predicates**, and three properties are *proven by
enumeration* (not spot-checked):

| Property | What is proven | How |
|---|---|---|
| **Totality** | every one of the 2¹¹ predicate combinations maps to exactly one known verdict — no gap, no `None` | enumerate the full boolean cube |
| **Consistency** | the table and the production `_verdict` agree on every reachable comparison shape | build inputs from 2¹¹ construction knobs, compare both |
| **Safety** | an introduced regression not fully explained by an environment signal can never yield a pass-like verdict | assert over every combination |

`2051 passed` — the table is total, equivalent to the implementation, and safe.

## Predicates (precise definitions)

Each is derived from the baseline→current comparison.

| Predicate | True when … |
|---|---|
| `intro` | ≥1 introduced failure — a test passed in baseline, fails now |
| `pre` | ≥1 pre-existing failure — failed in baseline and still fails |
| `miss` | ≥1 current failure whose baseline result is missing |
| `env_covers` | an environment signal (timeout, missing artifact, lost runner, corrupt log, lost sensor stream) is present **and every introduced failure is itself explained by such a signal** (vacuously true when `intro` is false) |
| `ithresh` | a requirement threshold crossed pass→fail (baseline pass, current fail) |
| `curfail` | ≥1 requirement threshold fails in the current run (`ithresh` ⇒ `curfail`) |
| `incomplete` | a threshold whose baseline or current value is missing (cannot evaluate) |
| `inconclusive` | a test whose status changed but is not recognisably pass/fail |
| `worsen` | a metric materially worsened (direction-aware, above noise) |
| `unchanged_with_thresh` | all tests still pass **and** ≥1 threshold was evaluated |
| `covgap` | a requirement is in scope but no evidence covers it |

## The decision table (ordered; first match wins)

| # | Condition | Verdict |
|---|---|---|
| 1 | `env_covers and not ithresh` | `environment_failure` |
| 2 | `intro and ithresh` | `confirmed_regression` |
| 3 | `pre and curfail and worsen` | `worsened_preexisting_failure` |
| 4 | `intro` | `confirmed_regression` |
| 5 | `pre and curfail` | `preexisting_failure` |
| 6 | `pre and worsen` | `worsened_preexisting_failure` |
| 7 | `miss and curfail` | `insufficient_evidence` |
| 8 | `inconclusive or incomplete` | `insufficient_evidence` |
| 9 | `curfail` | `requirements_coverage_gap` if `covgap` else `possible_regression` |
| 10 | `covgap` | `requirements_coverage_gap` |
| 11 | `unchanged_with_thresh` | `successful_change` |
| 12 | *(default)* | `expected_change` |

Rule 1 is the K3 carve-out: an environment signal only wins when it explains the
*whole* failure set and there is no threshold regression. Any introduced failure
that slips past rule 1 is caught by rule 2 or rule 4 — never by a pass-like rule.

## The safety invariant, stated precisely

For every input: if `intro` holds and the verdict is not `environment_failure`
(rule 1), the verdict is in `{confirmed_regression, worsened_preexisting_failure}`.
Equivalently — a verdict in `{successful_change, expected_change}` implies
`not intro`. This is the formal statement of "a real regression is never hidden",
and it is checked against the production classifier for all 2048 reachable shapes.

## Scope and honest limits

This formalises the **deterministic, evidence-classification** layer — the part
that should be exact. It does *not* claim to resolve the genuinely *statistical*
questions (is a single timeout flaky infra or a real slowdown? is a metric move
signal or noise?). Those need repeated measurements and significance testing, and
are tracked as the next rigor step (statistics for timeouts/flakiness; confidence
as a calibrated probability validated on labelled revert-commit data). What is
proven here is that, *given* the evidence predicates, the verdict is total,
consistent, and never masks a regression.
