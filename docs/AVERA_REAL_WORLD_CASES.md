# AVERA — Real-World Validation Cases

**Date:** 18 June 2026
**Status:** Reproducible validation on real third-party open-source code

## Why this exists

AVERA's fixture matrix (20 scenarios) is authored in-house. This document records
runs of AVERA on **real, third-party open-source projects** — code AVERA's authors
did not write — to show the evidence pipeline works beyond curated fixtures.

The verification results are **real**: each project's own test suite is run before
and after a one-line change. The change itself is introduced deliberately (to test
detection), but the pass/fail outcomes are produced by the project's real tests.

## Method (per project)

1. `git clone` the real project; install it.
2. Run its own test suite → **baseline** JUnit XML (all green).
3. Introduce **one realistic one-line regression** in a source file.
4. Run the same suite → **current** JUnit XML (real failures).
5. Adapt both via `avera adapt-junit` into AVERA verification JSON.
6. Auto-build a minimal evidence pack (change description, component map,
   one requirement) and run `avera action-run`.
7. Record AVERA's verdict, gate status, and the integrity root.

## Results

| Project | Domain | Tests | One-line regression | Introduced failures | AVERA verdict | Gate |
|---|---|---|---|---|---|---|
| [python-tabulate](https://github.com/astanin/python-tabulate) | text formatting | 204 | default float format `g`→`f` | **78** | `confirmed_regression` | **block** |
| [toolz](https://github.com/pytoolz/toolz) | functional utils | 181 | off-by-one in `first()` | **6** | `confirmed_regression` | **block** |
| [python-slugify](https://github.com/un33k/python-slugify) | string slugs | 82 | default separator `-`→`_` | **56** | `confirmed_regression` | **block** |

In all three, AVERA:

- ingested the real JUnit results,
- detected every introduced failure (baseline pass → current fail),
- mapped the changed file,
- classified `confirmed_regression` and the deterministic gate returned **block**,
- produced the full signed evidence chain (report, manifest + `integrity_root`,
  hash-chained audit log).

## What this validated — and one fix it produced

The first real run surfaced a genuine gap: AVERA's classifier was built around
**metric/threshold** requirements (e.g. BMS cell temperature), so a pure pass/fail
software test regression was under-classified as `requirements_coverage_gap`
(→ review), not `confirmed_regression`.

Fix applied: an **introduced test failure (baseline pass → current fail) is itself
proof of a regression**, independent of any numeric threshold. This makes AVERA
work for ordinary software CI — the largest segment — not only metric-based
verification. The fixture matrix (all 20) and classifier tests stayed green.

## Honest caveats

- The regressions are deliberately introduced to test detection; this measures
  AVERA's detection, not a wild-caught bug.
- `requirements.csv` / `component_map.json` are auto-built minimally; a real team
  would map tests to their own requirements.
- Risk is `medium` (not `release_blocking`) because these requirements carry no
  safety level — appropriate for general software, not safety-critical domains.

## Reproducibility

The harness (`/tmp/avera_case.py` during this run) takes a baseline + current
JUnit pair and a changed file, builds the pack, and runs AVERA. Any project whose
test runner emits JUnit XML (pytest, Jest, Go test, CTest, Surefire, `node --test
--test-reporter=junit`) can be added the same way.
