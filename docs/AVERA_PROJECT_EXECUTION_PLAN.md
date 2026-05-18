# AVERA Project Execution Plan

**Date:** 22 April 2026  
**Status:** Active execution plan  
**Project:** `AVERA`

## Execution Philosophy

AVERA should be built in disciplined engineering stages.

Each stage should produce:

- a working artifact
- a testable behavior
- a documented contract
- a report or demo output

Avoid adding broad platform features before the local evidence engine is trustworthy.

## Engineering Roles

### 1. Product/System Architect

Owns:

- product boundaries
- module map
- roadmap
- milestone definitions
- non-goals

### 2. Data/Evidence Architect

Owns:

- artifact schemas
- normalized data models
- evidence graph
- storage path

### 3. Risk & Classification Engineer

Owns:

- verdict taxonomy
- confidence rules
- risk scoring
- edge cases

### 4. Validation/Test Engineer

Owns:

- fixture scenarios
- acceptance tests
- smoke checks
- report trust checks

### 5. Local Tooling Engineer

Owns:

- command interface
- local run scripts
- developer setup
- packaging later

### 6. Report/UX Engineer

Owns:

- Markdown reports
- JSON schema
- future HTML/PDF output
- clarity for engineering review

## Stage 0: Foundation Already Completed

Current state:

- standalone project folder exists
- documentation exists
- Python package exists
- BMS fast-charge fixture exists
- local analyzer command works
- Markdown and JSON reports are generated

Current validated result:

```text
Verdict: confirmed_regression
Risk: high
Confidence: high
```

## Stage 1: Stabilize Core v0.1

Goal:

- turn the first demo into a small reliable local engine

Tasks:

- add `AVERA_CORE_ARCHITECTURE.md`
- add `AVERA_PROJECT_EXECUTION_PLAN.md`
- add fixture scenarios:
  - successful change
  - confirmed regression
  - preexisting failure
  - insufficient evidence
- add `avera-evidence-graph.json`
- add smoke script
- make README run instructions exact
- add pytest or standard-library test runner decision

Exit criteria:

- all fixture scenarios run locally
- each scenario has expected verdict/risk/confidence
- reports are generated for every scenario
- no external service is required

## Stage 2: Evidence Graph v0.1

Goal:

- make AVERA's reasoning trace explicit, not only embedded in a report

Tasks:

- add `src/avera/graph/`
- define graph nodes:
  - `change`
  - `component`
  - `requirement`
  - `test`
  - `metric`
  - `threshold_evidence`
  - `risk`
  - `recommendation`
- define graph edges:
  - `affects`
  - `verifies`
  - `measures`
  - `violates`
  - `supports`
  - `recommends`
- export deterministic JSON

Exit criteria:

- BMS confirmed regression emits a graph
- every high-risk conclusion has at least one evidence path

## Stage 3: Classification v0.2

Goal:

- make verdict/risk/confidence rules clearer and safer

Tasks:

- split classifier rules into smaller functions
- add explicit `environment_failure`
- add explicit `requirements_coverage_gap`
- add confidence reason codes
- add risk reason codes
- add expected outcome tests for edge cases

Exit criteria:

- classifier can explain why it produced the verdict
- weak evidence cannot produce high confidence

## Stage 4: Artifact Expansion

Goal:

- ingest more realistic automotive evidence without becoming platform-heavy

Tasks:

- add `signal_trace.csv`
- add `simulation_results.json`
- add optional `environment_status.json`
- support multiple tests and multiple requirements per component
- support missing metric handling

Exit criteria:

- at least one fixture uses signal trace evidence
- at least one fixture uses simulation result evidence

## Stage 5: Local Tooling v0.2

Goal:

- make AVERA easy to run locally

Tasks:

- add `scripts/run_demo.sh`
- add `scripts/run_all_fixtures.py`
- improve CLI arguments
- add `--format json|markdown|both`
- add `--strict` exit policy

Exit criteria:

- a user can run all demos with one command
- reports are easy to locate

## Stage 6: AI Explanation Layer

Goal:

- add AI only after evidence is structured

Tasks:

- summarize existing reports
- generate review-ready explanation
- answer questions over the evidence graph

Boundary:

- AI explains evidence.
- AI does not create proof by itself.

## Immediate Sprint

Recommended next sprint:

```text
Sprint 1: Core v0.1 hardening
```

Scope:

- scenario fixtures
- evidence graph v0.1
- classifier reason codes
- local smoke runner

Expected duration:

```text
2-4 focused work sessions
```
