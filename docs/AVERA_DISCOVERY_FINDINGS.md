# AVERA — Discovery Harness Findings

**Date:** 18 June 2026
**Status:** First real finding from mining real git history (reproducible)

## Idea

Instead of inventing regressions, mine **real historical regressions** from
open-source git history — changes that passed review, were merged, then **reverted**
by a human — and check whether AVERA would have caught them.

Two payoffs:
1. Cases where AVERA catches what slipped through → real proof of value.
2. Cases where AVERA misses → a concrete backlog of new detection lenses. This is
   how the algorithm gets stronger on real data, not on fixtures.

## Where the data comes from (no fabrication)

Real git history already labels real failures:
- `revert` commits — a merged change later undone (a real regression that passed CI/review).
- `fix regression / hotfix / bug` commits — real defects and their fixes.

A revert commit names the exact bad commit (`This reverts commit <sha>`), so:
- `parent(bad)` = good state, `bad` = the merged regression.

## First real case (pytoolz/toolz)

- **Reverted regression:** `f0831e7` "Faster isiterable when x isn't iterable."
  (1 file, `toolz/itertoolz.py`, +1/-5). Merged, then reverted by `5a3b8b1`.
- **Method:** ran toolz's own test suite at `parent(f0831e7)` (good) and at
  `f0831e7` (bad); adapted both to AVERA; ran the pipeline.

### Result

| State | Tests | Failures |
|---|---|---|
| good `19edc08` | 180 | 1 (`test_inspect_wrapped_property`, pre-existing Py3.11 compat) |
| bad `f0831e7` | 180 | 1 (the **same** test) |

- **Introduced failures (pass → fail): 0.**
- AVERA verdict: `requirements_coverage_gap` → gate **review** (introduced_failures = 0).

### Honest interpretation

A real regression that **passed code review and was merged** caused **zero new test
failures** in the project's own suite. Its own CI did not catch it — a human did,
which is why it was reverted.

Therefore a pass/fail-based gate (AVERA's current primary signal) **cannot** flag
this class of regression: there is no failing test to consume. AVERA did not
green-light it (it returned *review*, not *pass*), but it did not identify the
regression either.

## What this discovers — backlog lens #1

The most dangerous regressions are the ones that **slip through the tests** — exactly
the ones humans revert. Catching them needs a **non-test lens**, analysing the
change itself, not only test outcomes:

- **diff-risk lens** — flag edits to hot/low-level functions (e.g. `isiterable`)
  that are called widely, even when tests stay green.
- **behavioural-diff lens** — same input → different output across the change,
  independent of whether a test covers it.

This is where AVERA can become genuinely differentiated: surfacing what other CI
missed, not just re-reporting test failures.

## Scaling this into a number

Running the harness across many real reverts and counting **how many introduced
zero new test failures** yields a concrete, honest, novel statistic:

> "Of N real reverted regressions mined from OSS history, X% introduced zero new
> test failures — i.e. slipped through the project's own CI."

That percentage is the size of the gap AVERA's next lens targets.

## Reproducibility

Harness (`/tmp/avera_case.py` this run) takes a baseline + current JUnit pair and a
changed file, builds an evidence pack, and runs AVERA. The history mining is plain
git: find a `revert`, extract the bad commit, test `parent(bad)` vs `bad`.

## Status / caveats

- One real case so far; the finding (regression slipped past tests → invisible to a
  pass/fail gate) is real and reproducible, not extrapolated.
- Historical commits can fail to build under a current toolchain; that friction is
  part of real-world mining and should be logged, not hidden.
