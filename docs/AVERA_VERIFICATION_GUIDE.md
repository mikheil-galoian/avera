# AVERA Verification Guide

**Date:** 29 April 2026  
**Status:** Active verification path for the local prototype

## Purpose

This guide defines the practical verification contour for the current AVERA
prototype.

It is intentionally focused on the cheapest repeatable commands that prove the
kernel, orchestration path, and demo artifacts are still healthy.

## Verification Priorities

Use the lowest-cost command that proves the intended surface:

1. fixture matrix health
2. canonical demo artifact chain
3. artifact contract integrity
4. focused runtime tests
5. broader suite expansion when the environment is cooperative

## Fast Smoke Path

Run the fixture matrix:

```bash
python3 -B scripts/run_all_fixtures.py
```

Expected result:

```text
AVERA fixture matrix passed.
```

## Canonical Demo Path

Refresh the full canonical BMS demo chain:

```bash
PYTHONPATH=src python3 -B -m avera demo-refresh \
  --project fixtures/bms-fast-charge \
  --report-out reports/fixtures/bms-fast-charge \
  --memory reports/avera-memory.jsonl \
  --traceability-out reports/avera-traceability-index.json \
  --decision-out reports/avera-decision.json \
  --trend-out reports/avera-trend-index.json \
  --pack-out reports/avera-workspace-pack.json
```

This proves:

- analysis
- traceability
- decision
- trend
- workspace pack

## Cross-Domain Proof

Validate the working ADAS scenario:

```bash
PYTHONPATH=src python3 -B -m avera validate-workspace \
  fixtures/adas-pedestrian-detection-regression
```

```bash
PYTHONPATH=src python3 -B -m avera analyze \
  --project fixtures/adas-pedestrian-detection-regression \
  --out reports/fixtures/adas-pedestrian-detection-regression
```

Current expected shape:

- verdict: `confirmed_regression`
- risk: `high`
- confidence score: `0.95`

## Artifact Contracts

Validate the exported workspace pack:

```bash
PYTHONPATH=src python3 -B -m avera validate-artifact \
  --artifact workspace_pack \
  --path reports/avera-workspace-pack.json \
  --bundle
```

Validate a report artifact:

```bash
PYTHONPATH=src python3 -B -m avera validate-artifact \
  --artifact report \
  --path reports/fixtures/bms-fast-charge/avera-report.json
```

## Focused Runtime Tests

Use the project runtime:

```bash
.venv/bin/python -m pytest tests/test_artifact_contracts.py tests/test_demo_refresh_contract.py tests/test_cli_demo_refresh.py -q
```

These are the highest-value focused checks for the current productization stage:

- artifact contracts
- demo-refresh CLI surface
- orchestration order and failure handling

## Known Reality Of The Current Environment

The logical verification state is stronger than a single long full-suite runner
may suggest in this session environment.

Current verified facts:

- `pytest` is installed in `.venv`
- focused `pytest` subsets passed
- `demo-refresh` orchestration tests passed
- fixture matrix smoke passed
- artifact contract validation passed
- full project suite passed:
  - `63 passed, 5 subtests passed`

Current remaining verification tail:

- broader shell-facing verification beyond code-path and artifact checks

That tail should be treated as presentation-surface hardening work, not as
evidence that the kernel is unproven.

## Operator Recommendation

For live demo preparation, use this order:

1. run fixture matrix
2. run canonical `demo-refresh`
3. validate workspace pack contract
4. optionally run focused `pytest` subset
5. launch `./start_demo.sh`
