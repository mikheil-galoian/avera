# AVERA Architecture

**Date:** 29 April 2026  
**Status:** Implemented local kernel plus thin demo shell  
**Project:** `AVERA`

## Current Architectural State

As of 29 April 2026, AVERA is no longer just a concept stack.

The implemented product boundary is a local Python kernel under `src/avera/`,
with deterministic JSON artifacts, a thin Streamlit demo shell under `demo/`,
and an orchestration command that refreshes the full demo artifact chain.

The architecture should therefore be read as:

```text
validated local workspace
  -> ingestion
  -> baseline/current comparison
  -> conservative classification and report generation
  -> evidence graph
  -> gate policy
  -> engineering memory ledger
  -> traceability index
  -> decision engine
  -> trend index
  -> workspace pack export
  -> thin demo shell / demo-refresh orchestration
```

This is a local, artifact-driven system first. It is not yet a hosted platform,
shared graph service, or broad connector mesh.

## Implemented Layer Map

### 1. Workspace Contract And Ingestion

Implemented in:

- `src/avera/validation/workspace.py`
- `src/avera/ingestion/requirements.py`
- `src/avera/ingestion/component_map.py`
- `src/avera/ingestion/verification_results.py`

The current kernel expects a minimal local workspace with:

- `requirements.csv`
- `component_map.json`
- `baseline_results.json`
- `current_results.json`
- `change_description.txt`

Optional evidence can include:

- `signal_trace.csv`

This layer validates the workspace shape first, then loads normalized
requirements, component mappings, and verification results for downstream use.

### 2. Comparison And Classification Core

Implemented in:

- `src/avera/compare/baseline_comparator.py`
- `src/avera/classify/`
- `src/avera/core.py`

This is the first stable reasoning core.

It compares baseline vs current results, identifies introduced versus
preexisting or environmental failures, computes risk and confidence, and emits
a deterministic public report shape.

The current classifier and report flow already preserve conservative verdicts
such as:

- `confirmed_regression`
- `successful_change`
- `preexisting_failure`
- `worsened_preexisting_failure`
- `environment_failure`
- `insufficient_evidence`
- `requirements_coverage_gap`

### 3. Stable Report And Graph Artifacts

Implemented in:

- `src/avera/reports/`
- `src/avera/graph/`

The kernel produces:

- `avera-report.json`
- `avera-report.md`
- `avera-evidence-graph.json`

These artifacts are deterministic outputs of the local run, not hand-edited
documents or UI-only summaries.

The evidence graph is a derived proof path representation for requirements,
components, tests, failures, rules, confidence factors, risk drivers, and
signal summaries.

### 4. Gate And Engineering Memory

Implemented in:

- `src/avera/gates/`
- `src/avera/memory/`

The gate layer evaluates the generated report against explicit local policy and
returns `pass`, `review`, or `block`.

The memory layer is an append-only JSONL ledger that records analysis and gate
events so later layers can reason over run history without mutating the source
report artifacts.

### 5. Traceability Index

Implemented in:

- `src/avera/traceability/`
- `src/avera/query/`

The traceability layer builds a deterministic local index over component,
requirement, test, failure, risk, and gate relationships.

This index is the first queryable relationship layer in the implemented kernel.
It supports both downstream artifact generation and direct local queries.

### 6. Decision Engine

Implemented in:

- `src/avera/decisions/engine.py`

The decision engine consumes:

- report output
- optional gate output
- optional traceability output

It emits a stable decision artifact with:

- `schema_version`
- `action`
- `status`
- `category`
- `priority`
- `release_recommendation`
- `owner`
- `owner_routing`
- `actions`
- `corrective_actions`
- `verification_playbook`
- `escalation`
- `context`
- `rationale`

This layer is now part of the implemented kernel, not a future placeholder.
Its role is conservative operational routing, not free-form AI advice.

### 7. Trend Layer

Implemented in:

- `src/avera/trends/index.py`

The trend layer builds a deterministic history view from memory records and
optional traceability data.

The current export includes:

- `verdict_history`
- `risk_history`
- component trend summaries
- requirement trend summaries
- test stability summaries
- `test_stability_buckets`

This is a historical summary layer over emitted artifacts. It does not replace
the source report, graph, or memory ledger.

### 8. Stable Artifact Contracts

Implemented in:

- `src/avera/contracts/validator.py`
- `src/avera/validation/report.py`

The current contract validator covers:

- `report`
- `graph`
- `decision`
- `trend`
- `workspace_pack`

This makes the artifact layer an explicit kernel boundary. The CLI can validate
payload shape and schema namespace before packing or downstream handoff.

### 9. Workspace Pack

Implemented in:

- `src/avera/pack/export.py`

The workspace pack is the implemented export boundary for sharing one run's
derived state without recomputing it.

The top-level pack contract currently includes:

- `workspace`
- `summary`
- `artifacts`
- `report`
- `graph`
- `memory_slice`
- `traceability`
- `decision`
- `trend`
- `manifest`

The pack preserves source paths, presence/absence metadata, checksums where the
source file exists, and a filtered memory slice for the exported run.

### 10. Demo Shell And Demo-Refresh Orchestration

Implemented in:

- `demo/app.py`
- `demo/avera_demo/`
- CLI command: `avera demo-refresh`

The demo shell is intentionally thin. It reads local artifacts from disk and
renders them for inspection. It does not own the analysis logic.

`demo-refresh` is the orchestration layer that chains the implemented kernel in
this order:

1. `analyze`
2. `traceability`
3. `decision`
4. `trend`
5. `pack`

That command is the current end-to-end demo assembly path for the canonical BMS
scenario and any compatible local workspace.

## Architectural Diagram

```text
                                  AVERA
                  Automotive Verification, Evidence & Risk Architecture

┌─────────────────────────────────────────────────────────────────────────────┐
│ Workspace Contract                                                          │
│ requirements.csv | component_map.json | baseline/current results | change  │
│ optional signal_trace.csv                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     |
                                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│ Local Kernel                                                                │
│ ingestion -> comparison -> classification -> report -> graph -> gate       │
│ -> memory -> traceability -> decision -> trend -> workspace pack           │
└─────────────────────────────────────────────────────────────────────────────┘
                                     |
                                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│ Stable Artifact Boundary                                                    │
│ report | graph | decision | trend | workspace_pack                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                     |
                                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│ Thin Productization Layer                                                   │
│ local queries | demo shell | demo-refresh | presentation-ready artifacts   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Core Entities

The implemented kernel works primarily with these entity families:

- `requirement`
- `component`
- `test`
- `verification_run`
- `failure`
- `risk`
- `verdict`
- `gate_status`
- `decision`
- `memory_record`
- `trend_summary`
- `workspace_pack`

The long-term automotive entity model may grow beyond this, but the current
kernel is organized around these shipped artifact and relationship types.

## Architectural Principles That Are Now Real

The following principles are already implemented, not merely intended:

- local-first analysis
- deterministic JSON exports
- explicit schema versions
- conservative classification and decision policy
- artifact-driven provenance
- append-only engineering memory
- stable export boundaries for future UI and automation

## What Is Not Yet The Architecture

The following ideas may still matter strategically, but they are not the
implemented architecture as of 29 April 2026:

- hosted graph services
- fleet telemetry correlation
- supplier exchange layers
- PLM/ALM platform integrations
- broad compliance automation
- enterprise dashboard surfaces

Those belong to future roadmap phases, not to the present-state kernel diagram.

AI should not be the sole authority for:

- safety approval
- confirmed root cause
- compliance certification
- release decisions

## Storage Strategy

MVP storage can be file-based:

- JSON reports
- Markdown reports
- JSONL evidence ledger
- local artifact directory

Later storage can become:

- SQLite for local graph state
- PostgreSQL for hosted/team state
- graph projection over relational tables
- object storage for large logs and traces

## MVP Boundary

The first version should not attempt to ingest the whole vehicle lifecycle.

It should prove one workflow:

```text
automotive-style code change
  -> baseline vs current verification
  -> requirement impact
  -> evidence-backed risk report
```
