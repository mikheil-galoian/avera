# AVERA Realization Sequence

**Date:** 22 April 2026  
**Status:** Active execution sequence  
**Goal:** turn AVERA from concept into a working automotive engineering evidence tool

## North Star

AVERA becomes a local-first engineering evidence kernel that can later grow into a full automotive engineering memory platform.

The execution path is:

```text
Evidence Pack
  -> Validation
  -> Ingestion
  -> Comparison
  -> Classification
  -> Evidence Graph
  -> Report
  -> Engineering Review
```

## Current Position

Already working:

- local Python package
- BMS fixture matrix
- baseline/current comparison
- conservative classifier
- JSON/Markdown reports
- evidence graph v0.1
- local fixture runner

Current command:

```bash
python3 -B scripts/run_all_fixtures.py
```

## Execution Sequence

### Step 1: Stabilize Local Evidence Packs

Purpose:

- make every local project folder self-validating

Deliverables:

- `src/avera/validation/`
- `validate_workspace(path)`
- workspace validation report
- runner blocks invalid fixtures

Definition of done:

- missing required files are detected
- invalid JSON is detected
- invalid requirements headers are detected
- all current fixtures validate

### Step 2: Formalize Evidence Graph

Purpose:

- make AVERA's reasoning durable and inspectable

Deliverables:

- `avera-evidence-graph.json`
- stable graph schema
- graph summary in reports

Definition of done:

- every fixture emits graph JSON
- confirmed regression graph includes requirement, file, component, threshold evidence, risk, recommendation

### Step 3: Expand Classification Policy

Purpose:

- make AVERA conservative across more real engineering outcomes

Deliverables:

- `environment_failure`
- `requirements_coverage_gap`
- `worsened_preexisting_failure`
- confidence score
- rule IDs and factors in reports

Definition of done:

- weak evidence never produces high confidence
- safety relevance can increase risk but not confidence
- each verdict has a fixture

### Step 4: Add Signal Evidence

Purpose:

- move from summary metrics toward time-series engineering evidence

Deliverables:

- `signal_trace.csv`
- `src/avera/signals/`
- signal trace parser
- first signal-backed BMS fixture

Definition of done:

- signal trace can be loaded independently
- trace records map to test id and signal name
- future threshold evidence can cite signal source

### Step 5: Productize Local Commands

Purpose:

- make AVERA easy to run without remembering environment details

Deliverables:

- `avera validate-workspace`
- `avera analyze`
- `avera run-fixtures`
- improved README quickstart

Definition of done:

- one command validates a fixture
- one command analyzes a fixture
- one command runs all local fixtures

### Step 6: Report Hardening

Purpose:

- make output review-ready for engineers

Deliverables:

- report schema v0.2
- evidence graph path in report
- risk drivers
- confidence factors
- open questions

Definition of done:

- a human can see why the verdict exists
- report never hides insufficient evidence
- report distinguishes proof from recommendation

### Step 7: Domain Expansion

Purpose:

- move beyond BMS without losing evidence discipline

Order:

1. BMS thermal and charging
2. ECU control logic
3. ADAS scenario validation
4. Powertrain/thermal
5. Chassis/control systems

Definition of done:

- every new domain adds:
  - fixture
  - metrics
  - requirements
  - expected report
  - domain notes

## Workstream Order

### Core Workstream

1. validation
2. ingestion
3. comparison
4. classification
5. evidence graph
6. reports

### Product Workstream

1. README
2. local commands
3. fixture runner
4. demo reports
5. architecture docs

### Domain Workstream

1. BMS
2. ECU
3. ADAS
4. Powertrain

### Future AI Workstream

Only after evidence graph is stable:

1. explain report in plain language
2. answer questions over evidence graph
3. suggest next checks
4. never invent evidence

## Active Sprint

Current sprint:

```text
Sprint 5: confidence score + signal graph nodes + local command polish
```

In progress:

- confidence score
- signal summary nodes in evidence graph
- local command polish

Next after that:

- expected report snapshots
- signal-backed threshold evidence
- first ECU fixture

## Rule For Every Step

Every implementation step must produce:

- code
- fixture or test
- report output
- documentation update

If a step cannot produce evidence, it should not be treated as complete.
