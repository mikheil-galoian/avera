# AVERA MVP Plan

**Date:** 21 April 2026  
**Status:** Draft  
**First product:** `AVERA Change Impact`

## MVP Objective

Build the first credible AVERA prototype as a local workspace/reporting workflow that can analyze an automotive-style software change and produce an evidence-backed risk report.

The MVP should prove that AVERA can connect:

```text
engineering change -> requirement -> verification result -> failure evidence -> risk
```

## Recommended First Domain

Start with a Battery Management System style demo.

Reason:

- BMS is understandable to automotive and non-automotive reviewers.
- Requirements can be expressed with numeric thresholds.
- Test and simulation evidence can be represented in simple CSV/JSON.
- Risk is easy to explain without claiming full vehicle certification.

Example requirement:

```text
BMS-REQ-112: Maximum cell temperature during fast charging must not exceed 50°C.
```

Example regression:

```text
baseline max_cell_temp = 47.1°C
current max_cell_temp = 52.8°C
threshold = 50.0°C
classification = confirmed_regression
risk = high
```

## MVP Inputs

Required:

- engineering change description
- baseline verification result
- current verification result
- requirements file

Recommended file formats:

- `requirements.csv`
- `baseline-results.json`
- `current-results.json`
- `signal-trace.csv`
- `avera.config.json`

Optional:

- local test logs
- JUnit XML
- simulation CSV
- CAN trace CSV
- ownership map

## MVP Outputs

Required:

- JSON report
- Markdown report

Report should include:

- verdict
- confidence
- risk level
- affected requirements
- affected files
- introduced failures
- preexisting failures
- evidence summary
- recommended next checks

## First Local Tool Shape

Possible commands:

```bash
avera analyze
avera analyze --config avera.config.json
avera analyze --baseline ./fixtures/bms/baseline --current ./fixtures/bms/current
avera report --format markdown
```

The implementation should live under an AVERA-specific boundary when code is added.

## MVP Modules

### 1. Artifact Ingestion

Reads:

- config
- requirements
- baseline results
- current results
- optional signal traces

### 2. Diff Mapper

Maps changed files, modules, and components to automotive requirements.

Maps:

- changed files
- changed paths
- changed modules

### 3. Requirement Mapper

Maps changed files or modules to requirements.

Initial approach can be simple:

```text
requirements.csv includes component/module/file path fields
```

### 4. Baseline Comparator

Compares:

- baseline test status vs current test status
- baseline signal values vs current signal values
- baseline threshold compliance vs current threshold compliance

### 5. Evidence Builder

Creates evidence records:

- failure appeared after change
- affected requirement threshold exceeded
- changed file matches requirement ownership
- signal delta supports risk

### 6. Risk Classifier

Classifies:

- `confirmed_regression`
- `possible_regression`
- `preexisting_failure`
- `environment_failure`
- `insufficient_evidence`

Adds risk:

- `low`
- `medium`
- `high`
- `safety_critical`
- `release_blocking`

### 7. Report Generator

Outputs:

- `avera-report.json`
- `avera-report.md`

## 6-8 Week Quick Start

### Week 1: Product And Fixture Definition

- finalize AVERA documents
- define BMS demo scenario
- create requirement schema
- create baseline/current fixture artifacts
- decide the standalone AVERA prototype location

### Week 2: Ingestion And Report Skeleton

- load config
- parse requirements CSV
- parse baseline/current JSON
- generate initial JSON and Markdown reports

### Week 3: Baseline Comparison

- compare baseline vs current results
- detect introduced failures
- detect threshold violations
- preserve preexisting failures

### Week 4: Requirement And Diff Mapping

- connect changed files to requirements
- connect failed checks to requirements
- include changed-file evidence in report

### Week 5: Risk Classifier

- implement risk rules
- compute confidence
- add safety-relevant and release-blocking flags

### Week 6: Demo Hardening

- add fixture variants:
  - successful change
  - confirmed BMS regression
  - preexisting failure
  - environment failure
- create one-command demo script

### Week 7: Local Automation Exploration

- produce local report artifacts
- test in a small repository or fixture repo
- add concise terminal and Markdown summaries

### Week 8: Review And Direction Decision

- review report trustworthiness
- decide whether to build AVERA first as:
  - a standalone local tool
  - a standalone package plus demo fixtures
  - a future hosted/team platform

## MVP Exit Criteria

The MVP is credible if it can:

- run locally with one command
- analyze a BMS-style change
- identify an introduced verification failure
- link the failure to a requirement
- show numeric evidence from results or signal traces
- assign conservative risk and confidence
- produce a report that can be shown to an automotive engineer

## Deferred Until After MVP

- dashboards
- hosted SaaS
- full CAD/CAE integration
- native dSPACE or Vector integrations
- full safety case generation
- supplier portal
- fleet telemetry correlation
- automatic certification claims
