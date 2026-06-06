# AVERA Gate Policy

**Date:** 6 June 2026  
**Status:** Draft policy v1 — policy-as-data

## Purpose

AVERA gates turn a generated report into a deterministic engineering decision.

The gate is not a certification authority. It is a local policy layer for CI,
review workflows, and release readiness checks.

The gate stays **deterministic**. Thresholds and verdict sets are no longer
hardcoded — they are loaded from versioned **policy files** under `policies/`. A
policy only *parametrises* the same deterministic decision logic; it never
introduces non-deterministic behaviour.

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

## Policy-as-data

Policies are JSON files under `policies/` (JSON, not YAML, to keep AVERA
dependency-free — a deterministic gate must not depend on an optional parser).

Built-in policies:

| Policy file | `max_allowed_risk` | `min_confidence_score` | Notable |
|---|---|---|---|
| `general_policy.json` | medium | 0.50 | Reproduces the original default behaviour |
| `automotive_policy.json` | low | 0.70 | `possible_regression` is blocking |
| `aviation_policy.json` | low | 0.80 | `possible_regression` + `requirements_coverage_gap` blocking |
| `medical_policy.json` | low | 0.80 | `possible_regression` + `requirements_coverage_gap` blocking |
| `railway_policy.json` | low | 0.70 | `possible_regression` is blocking |
| `ai_agent_policy.json` | high | 0.40 | Permissive iteration tier; regressions still block |

Each file declares `schema_version`, `policy_id`, `domain`, `max_allowed_risk`,
`min_confidence_score`, `blocking_verdicts`, `review_verdicts`, and an optional
`risk_rank`.

The built-in `DEFAULT_GATE_POLICY` reproduces AVERA's original behaviour exactly,
so existing callers and tests are unaffected. The **same report can produce
different gate decisions under different policies** — e.g. a medium-risk
successful change passes under `general` but blocks under `aviation`.

Loader API: `avera.gates.load_builtin_policy(name)`, `load_policy(path)`,
`list_builtin_policies()`.

## CLI

`avera analyze` exits successfully when it can generate a valid report. Release
blocking belongs to `avera gate`, so real CLI/runtime failures are not confused
with engineering risk findings.

```bash
# Default (general) policy:
PYTHONPATH=src python3 -B -m avera gate \
  --report reports/fixtures/bms-fast-charge/avera-report.json

# Apply a built-in domain policy:
PYTHONPATH=src python3 -B -m avera gate \
  --report reports/fixtures/bms-fast-charge/avera-report.json \
  --policy aviation

# Or a custom policy file:
PYTHONPATH=src python3 -B -m avera gate \
  --report reports/fixtures/bms-fast-charge/avera-report.json \
  --policy-file policies/automotive_policy.json
```

`--max-risk` / `--min-confidence-score` still work and override the policy when
set. Omitting them and `--policy` reproduces the original default behaviour. The
gate output prints the active `policy_id`.

Expected behavior for `bms-fast-charge` (a confirmed regression) under any policy:

```text
Status: block
```
