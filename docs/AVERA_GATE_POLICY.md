# AVERA Gate Policy

**Date:** 22 April 2026  
**Status:** Draft policy v0

## Purpose

AVERA gates turn a generated report into a deterministic engineering decision.

The gate is not a certification authority. It is a local policy layer for CI,
review workflows, and release readiness checks.

## Gate Status

- `pass`: evidence satisfies the configured policy.
- `review`: evidence is incomplete, uncertain, environmental, or below the
  confidence threshold.
- `block`: evidence shows a confirmed or high-risk regression.

## Blocking Verdicts

- `confirmed_regression`
- `worsened_preexisting_failure`

## Review Verdicts

- `environment_failure`
- `insufficient_evidence`
- `possible_regression`
- `requirements_coverage_gap`

## Risk Policy

Default maximum allowed risk:

```text
medium
```

Any report above that risk blocks the gate.

## Confidence Policy

Default minimum confidence score:

```text
0.50
```

Reports below that score require review unless they already block.

## CLI

`avera analyze` exits successfully when it can generate a valid report. Release
blocking belongs to `avera gate`, so real CLI/runtime failures are not confused
with engineering risk findings.

```bash
PYTHONPATH=src python3 -B -m avera gate \
  --report reports/fixtures/bms-fast-charge/avera-report.json \
  --max-risk medium \
  --min-confidence-score 0.50
```

Expected behavior for `bms-fast-charge`:

```text
Status: block
```
