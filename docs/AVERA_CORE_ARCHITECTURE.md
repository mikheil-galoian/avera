# AVERA Core Architecture

**Date:** 22 April 2026  
**Status:** Active architecture  
**Project:** `AVERA`

## Purpose

This document defines the internal architecture for the first AVERA core.

AVERA is a local-first automotive engineering evidence engine. It reads engineering artifacts, normalizes them into stable data models, compares baseline vs current verification evidence, maps results to requirements and components, classifies risk, and generates proof-backed reports.

## Architecture Principle

AVERA must be built as a set of small engineering subsystems with explicit contracts.

The system should avoid hidden magic. Each conclusion must be traceable to:

- an input artifact
- a normalized model
- a comparison result
- a requirement or component mapping
- a classifier rule
- a report entry

## Current Runtime Choice

Primary language:

```text
Python 3.11+
```

Current implementation uses the Python standard library only.

Why Python:

- strong fit for engineering data
- common in simulation and validation workflows
- practical for CSV/JSON/log analysis
- easy local-first execution
- good future path to pandas, polars, duckdb, Jupyter, and AI tooling

## Current Pipeline

```text
Local project folder
  ↓
Artifact ingestion
  ↓
Normalized models
  ↓
Baseline comparator
  ↓
Risk classifier
  ↓
Report generator
  ↓
Markdown / JSON outputs
```

Current command:

```bash
PYTHONPATH=src python3 -B -m avera analyze \
  --project fixtures/bms-fast-charge \
  --out reports
```

## Subsystems

### 1. Artifact Ingestion

Location:

```text
src/avera/ingestion/
```

Responsibility:

- read local engineering artifacts
- validate basic structure
- convert CSV/JSON into normalized Python models

Current loaders:

- `load_requirements(path)`
- `load_component_map(path)`
- `load_verification_results(path)`

Current artifact types:

- `requirements.csv`
- `component_map.json`
- `baseline_results.json`
- `current_results.json`

Next artifact types:

- `change_description.txt`
- `signal_trace.csv`
- `simulation_results.json`
- `environment_status.json`

### 2. Domain Models

Location:

```text
src/avera/models/
```

Responsibility:

- define stable in-memory entities
- keep ingestion and reasoning decoupled

Current models:

- `Requirement`
- `ComponentMapEntry`
- `TestResult`
- `VerificationRun`

Next models:

- `EngineeringChange`
- `SignalTrace`
- `EvidenceItem`
- `EvidenceGraph`
- `RiskAssessment`
- `Recommendation`

### 3. Baseline Comparator

Location:

```text
src/avera/compare/
```

Responsibility:

- compare baseline vs current verification runs
- detect introduced failures
- preserve preexisting failures
- detect resolved failures
- compute metric deltas

Current output:

- `ComparisonResult`
- `TestComparison`
- `MetricDelta`

### 4. Risk & Classification Engine

Location:

```text
src/avera/classify/
```

Responsibility:

- classify the engineering result
- assign risk
- assign confidence
- connect failures to requirements and components
- recommend next checks

Current verdicts:

- `confirmed_regression`
- `possible_regression`
- `preexisting_failure`
- `insufficient_evidence`
- `expected_change`

Current risk levels:

- `low`
- `medium`
- `high`
- `release_blocking`

Next risk level:

- `safety_critical`

### 5. Evidence Graph

Planned location:

```text
src/avera/graph/
```

Responsibility:

- create explicit graph nodes and edges
- preserve reasoning lineage
- export `avera-evidence-graph.json`

First graph shape:

```text
change
  -> component
  -> requirement
  -> verification_test
  -> metric
  -> threshold_evidence
  -> risk_assessment
  -> recommendation
```

### 6. Report Generator

Location:

```text
src/avera/reports/
```

Responsibility:

- generate human-readable reports
- generate machine-readable reports

Current outputs:

- `avera-report.md`
- `avera-report.json`

Next output:

- `avera-evidence-graph.json`

### 7. Public Core API

Location:

```text
src/avera/core.py
```

Responsibility:

- expose stable analysis entrypoints
- hide internal module wiring from tests and future interfaces

Current function:

```python
analyze(
    baseline_path,
    current_path,
    requirements_path,
    component_map_path,
    change_description_path=None,
) -> dict
```

## Project Classifications

The core should be built in four classifications.

### Classification A: Evidence Infrastructure

Owns:

- ingestion
- schemas
- normalized models
- artifact validation

### Classification B: Reasoning Infrastructure

Owns:

- baseline/current comparison
- metric deltas
- threshold evaluation
- failure grouping

### Classification C: Risk Infrastructure

Owns:

- verdict rules
- risk scoring
- confidence scoring
- recommendations

### Classification D: Product Output Infrastructure

Owns:

- reports
- evidence graph exports
- local command interface
- demo packages

## Non-Goals For The Current Core

Do not build yet:

- hosted dashboard
- account system
- cloud sync
- GitHub workflow
- provider integrations
- automatic certification claims
- CAD/CAE native integrations
- large telemetry pipelines

## v0.1 Completion Definition

AVERA core v0.1 is complete when it can:

- run one command locally
- analyze at least four fixture scenarios
- classify successful, introduced, preexisting, and insufficient-evidence outcomes
- generate Markdown and JSON reports
- export a first evidence graph
- pass tests without external services
