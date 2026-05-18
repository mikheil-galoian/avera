# AVERA Engineering Memory

**Date:** 23 April 2026  
**Status:** Draft contract v0.1  
**Project:** `AVERA`

## Purpose

AVERA engineering memory is the durable local record of analysis outcomes and
gate decisions.

The goal is not to replace reports. The goal is to preserve the proof trail
behind them so later reviews can answer:

- what was analyzed
- what report was produced
- what gate decision was made
- what evidence and reasoning supported that decision
- whether the same issue appears again in a later run

This layer is intentionally local, append-only, and human-auditable.

## Long-Term Meaning

For automotive engineering, engineering memory is the part of AVERA that turns
one-off verification runs into a reusable institutional record.

Over time, it should become a searchable chronology of:

- change impact analyses
- release gate decisions
- confirmed regressions
- preexisting or environmental failures
- confidence and risk trends
- evidence summaries tied to concrete artifacts

That makes AVERA more than a report generator. It becomes a memory layer for
engineering accountability, safety review, and future traceability across
vehicle programs.

## Storage Contract

The engineering memory ledger is a local JSONL file.

Rules:

- one JSON object per line
- append-only writes only
- no in-place edits
- no record deletion
- stable schema version on every record
- machine-readable and human-inspectable

Recommended invariants:

- the writer always appends a complete record
- the reader can ignore blank lines
- the reader should tolerate an unreadable historical line without corrupting the rest of the file
- records should be emitted with deterministic key ordering

The ledger is a local artifact, not a hosted service.

## Schema

### Common Fields

Every record must include:

- `schema_version`
- `record_type`
- `timestamp_utc`

Common optional fields:

- `project_path`
- `report_path`
- `evidence_graph_path`
- `output_dir`
- `verdict`
- `risk`
- `confidence`
- `confidence_score`
- `gate_status`
- `gate_exit_code`
- `affected_components`
- `affected_requirements`
- `reasons`
- `summary`

### `analysis` Record

Purpose:

Capture the result of a successful `avera analyze` run.

Expected fields:

- `record_type`: `analysis`
- `project_path`
- `output_dir`
- `report_path`
- `evidence_graph_path`
- `verdict`
- `risk`
- `confidence`
- `confidence_score`
- `affected_components`
- `affected_requirements`
- `summary`

Recommended `summary` payload:

- comparison summary
- count of introduced failures
- count of preexisting failures
- confidence or risk highlights

### `gate` Record

Purpose:

Capture the result of a `avera gate` decision on an already generated report.

Expected fields:

- `record_type`: `gate`
- `report_path`
- `verdict`
- `risk`
- `confidence`
- `confidence_score`
- `gate_status`
- `gate_exit_code`
- `reasons`
- `summary`

Recommended `summary` payload:

- report summary
- blocking reasons
- review reasons
- exit-code context

## Canonical Record Model

The current memory model is centered on a single record structure with the
following normalized fields:

- `schema_version`
- `record_type`
- `timestamp_utc`
- `project_path`
- `report_path`
- `evidence_graph_path`
- `output_dir`
- `verdict`
- `risk`
- `confidence`
- `confidence_score`
- `gate_status`
- `gate_exit_code`
- `affected_components`
- `affected_requirements`
- `reasons`
- `summary`

This gives both record types a shared shape while still allowing each record to
carry the fields that matter for its own event.

## CLI Usage

The ledger is meant to be written by the CLI after successful work completes.

Current CLI contract:

- `avera analyze` should append an `analysis` record after report generation
- `avera gate --report <path>` should append a `gate` record after the decision
- both commands should write to the same local JSONL ledger path for the current workspace

Example flow:

```bash
avera analyze --project ./fixtures/bms-fast-charge --out ./reports
avera gate --report ./reports/avera-report.json
```

Those commands should leave behind the report artifacts and one or more memory
records describing the analysis and gate outcome.

## Reader Contract

Readers should load the ledger from newest to oldest for review convenience.

Recommended reader behavior:

- skip blank lines
- ignore malformed historical lines when possible
- support optional record limits
- derive counters for record type, verdict, risk, and gate status

This makes the ledger useful both as an audit trail and as a compact trend
source for future analytics.

## Engineering Intent

The ledger exists to preserve the accountability story around AVERA runs.

It should help answer:

- was this failure seen before
- did the gate agree with the analysis
- how often do we see this verdict or risk pattern
- which projects or reports keep producing similar evidence

That is the long-term engineering memory promise: proof does not disappear
after the report is written.
