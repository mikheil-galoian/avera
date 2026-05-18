# AVERA Trend Layer

**Date:** 28 April 2026  
**Status:** Draft core contract v0.1  
**Project:** `AVERA`

## Purpose

The Trend / Baseline Evolution Layer is AVERA's historical analysis layer for
understanding how evidence changes over time.

It sits above the traceability index, decision engine, and workspace pack
outputs. Its job is not to invent new facts. Its job is to summarize evolution
across runs in a deterministic, reviewable way.

Core role:

`baseline history -> trend visibility -> conservative interpretation`

## Why It Exists

AVERA already knows how to compare baseline and current evidence for a single
run. The trend layer extends that kernel across multiple runs so the system can
answer questions like:

- is this component becoming more stable or less stable?
- are the same requirements repeatedly affected?
- are failures recurring, resolving, or worsening?
- is the verdict history converging or oscillating?
- are risk signals improving, flat, or degrading?

This layer should remain conservative. It is a summary layer, not a prognostic
oracle.

## Trend Entities

The first trend contract should support these entity families:

### Component Trends

Track evolution for a component across runs.

Typical fields:

- component id and label
- run sequence
- verdict history
- risk history
- failure count history
- resolved vs repeated issue markers
- last-seen baseline context

### Requirement Trends

Track how a requirement behaves over time.

Typical fields:

- requirement id and label
- linked component history
- coverage history
- pass/fail/stability pattern
- repeated gap or regression markers
- evidence density over time

### Test Stability

Track whether a test is steady, noisy, flaky, or consistently informative.

Typical fields:

- test id and label
- pass/fail sequence
- flake indicators
- environment sensitivity
- repeated failure association
- coverage confidence

### Verdict / Risk History

Track the historical pattern of outcomes that AVERA has already emitted.

Typical fields:

- verdict sequence
- risk sequence
- confidence sequence
- transition markers
- escalation history
- gate outcome history

## Core Inputs

The layer should be derived from existing local artifacts only:

- analysis reports
- evidence graphs
- traceability indexes
- gate records
- decision records
- memory ledger entries
- optional workspace pack exports

It should not require a new source of truth.

## Expected JSON Output

The canonical export should be deterministic JSON.

Suggested top-level shape:

```json
{
  "schema_version": "0.1",
  "workspace": {
    "path": "fixtures/bms-fast-charge",
    "project": "AVERA"
  },
  "generated_at_utc": "2026-04-28T00:00:00Z",
  "inputs": {
    "report_paths": [],
    "traceability_index_path": "",
    "decision_record_paths": [],
    "memory_record_paths": []
  },
  "component_trends": [],
  "requirement_trends": [],
  "test_stability": [],
  "verdict_risk_history": [],
  "trend_summary": {
    "stability_state": "unknown",
    "risk_direction": "flat",
    "coverage_direction": "flat",
    "confidence": "low"
  },
  "provenance": [],
  "warnings": []
}
```

Required properties:

- deterministic field ordering in emitted JSON
- explicit schema version
- provenance for every derived trend
- warnings instead of silent inference when data is thin

## CLI Behavior

The CLI should expose a local trend build command under the core kernel.

Expected behavior:

- read the current workspace or exported pack
- collect prior runs and derived artifacts
- build a stable trend summary
- preserve traceability back to source evidence
- emit JSON first, with optional Markdown or terminal summary later
- fail explicitly when the workspace lacks the minimum history needed for a
  trustworthy trend view

Suggested command shape:

```bash
avera trends build --workspace <path> --out <path>
```

Expected CLI outputs:

- trend JSON export
- optional terminal summary
- optional report-path references
- warnings for weak or incomplete historical coverage

## Role Before UI

This layer belongs in the kernel before any UI shell exists.

It gives AVERA a stable way to answer historical questions in a machine-
readable form so future UI, review, or automation layers can stay thin.

The trend layer should support:

- CLI review
- regression triage
- release-readiness review
- future dashboard timelines
- future agent workflows that need history, not just the latest run

It should not become a speculative analytics layer. It should remain a derived
history view over already-proven evidence.

## Relationship To Other Core Layers

The trend layer should sit above:

- the baseline comparator, which compares a single run
- the traceability index, which links evidence inside a workspace
- the decision engine, which emits conservative recommendations
- the workspace pack, which packages derived outputs for handoff

It should produce historical summaries that are easy to inspect, easy to diff,
and safe to consume without a UI.

