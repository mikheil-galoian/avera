# AVERA Fixture Matrix

**Date:** 22 April 2026  
**Status:** Active validation matrix

## Purpose

Fixtures prove that AVERA does not always produce the same conclusion.

Each fixture should represent a controlled engineering evidence pack with a known expected outcome.

## v0.1 Fixtures

| Fixture | Purpose | Expected Verdict | Expected Risk | Expected Confidence |
|---|---|---|---|---|
| `bms-fast-charge` | baseline pass to current fail with threshold violation | `confirmed_regression` | `high` | `high` |
| `bms-successful-change` | baseline pass to current pass | `expected_change` | `low` | `medium` |
| `bms-preexisting-failure` | baseline fail and current fail without new blame | `preexisting_failure` | `medium` | `medium` |
| `bms-insufficient-evidence` | current failure without baseline evidence | `insufficient_evidence` | `medium` or `low` | `low` |
| `bms-worsened-preexisting` | baseline failed and current materially worsened | `worsened_preexisting_failure` | `high` | `high` |
| `bms-environment-failure` | current run failed due to environment/bench issue | `environment_failure` | `unknown` | `low` |
| `bms-coverage-gap` | mapped requirement lacks relevant verification evidence | `requirements_coverage_gap` | `medium` | `low` |
| `bms-mixed-results` | introduced + preexisting + unchanged in one run | `confirmed_regression` | `high` | `high` |

## v0.2 Fixtures

| Fixture | Purpose | Expected Verdict |
|---|---|---|
| `bms-signal-backed-regression` | signal trace directly backs threshold evidence | `confirmed_regression` |

## Fixture Rules

Each fixture must include:

- `requirements.csv`
- `component_map.json`
- `baseline_results.json`
- `current_results.json`
- `change_description.txt`

Future fixtures should include:

- `expected_report.json`

## Acceptance Rule

No fixture may produce `high` confidence unless it has:

- baseline/current evidence
- requirement mapping
- threshold or test failure evidence
