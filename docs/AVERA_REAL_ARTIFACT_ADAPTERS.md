# AVERA Real Artifact Adapters

**Date:** 30 April 2026  
**Status:** First adapter layer active  
**Scope:** Bridge real external engineering artifacts into the stable AVERA workspace contract

## Purpose

This document defines how AVERA begins to move from curated fixtures toward
real external evidence without breaking the stable kernel boundary.

The rule is simple:

- the kernel keeps consuming stable AVERA workspace artifacts
- adapters translate external formats into those stable artifacts

This keeps the core conservative and inspectable.

## First Active Adapter

The first real artifact adapter is:

- `adapt-junit`

Purpose:

- convert JUnit / xUnit XML test output into an AVERA verification-results JSON
- make real test artifacts usable before deeper native ingestion exists

CLI shape:

```bash
PYTHONPATH=src python3 -B -m avera adapt-junit \
  --input sample-results.xml \
  --out current_results.json \
  --run-id adas-hil-current \
  --stage hil
```

## What The Adapter Produces

The adapter writes a JSON artifact compatible with the existing AVERA
verification contract:

- `runId`
- `stage`
- `tests[]`

Each testcase is normalized into:

- `id`
- `component`
- `status`
- `metrics`
- `evidence`
- `metadata`

## Current JUnit Status Mapping

The current mapping is intentionally conservative:

- passed testcase -> `passed`
- failure node -> `failed`
- error node -> `error`
- skipped node -> `skipped`

The adapter does not invent verdicts.
It only prepares verification evidence for the existing AVERA core.

## Second Active Adapter

The second real artifact adapter is:

- `adapt-simulation`

Purpose:

- convert simulation-results CSV into an AVERA verification-results JSON artifact
- preserve metric-heavy engineering evidence in a form the current kernel already understands

CLI shape:

```bash
PYTHONPATH=src python3 -B -m avera adapt-simulation \
  --input current-simulation-results.csv \
  --out current_results.json \
  --run-id adas-sim-current \
  --stage current
```

## Current Simulation CSV Contract

Required columns:

- `test_id`
- `component`
- `status`
- `metric`
- `value`

Useful optional columns:

- `unit`
- `scenario`
- `evidence`

Rows are grouped by `test_id`, so one test can carry multiple metrics inside a
single adapted AVERA verification result.

## Why This Layer Matters

This is the first practical move from:

- demo-driven evidence packs

to:

- use-driven evidence intake

It proves the intended architecture:

- stable kernel contract
- thin adapter layer
- external artifacts normalized before analysis

It also now proves a stronger path:

- external simulation evidence
  -> adapted verification JSON
  -> normal AVERA workspace
  -> normal AVERA analysis

## First Adapted Sample Workspace

The first realistic adapted workspace is:

- `fixtures/adas-simulation-adapted`

This workspace contains:

- raw baseline simulation CSV
- raw current simulation CSV
- adapted `baseline_results.json`
- adapted `current_results.json`
- normal AVERA requirements, component map, change description, and signal trace

This is the first sample showing that AVERA can review a workspace whose core
verification artifacts were generated through adapters rather than only written
as fixture JSON by hand.

## Third Active Adapter

The third real artifact adapter is:

- `adapt-requirements`

Purpose:

- convert a richer ALM-style requirements export CSV into the stable AVERA
  `requirements.csv` shape
- preserve the stable kernel boundary while admitting more realistic upstream
  requirement sources

CLI shape:

```bash
PYTHONPATH=src python3 -B -m avera adapt-requirements \
  --input requirements-export.csv \
  --out requirements.csv
```

## Current Requirements Variant Mapping

The current adapter accepts common richer fields such as:

- `requirement_id`
- `title`
- `module`
- `threshold_signal`
- `threshold_operator`
- `threshold_value`
- `safety_relevance`
- `next_check`

and normalizes them into:

- `id`
- `component`
- `requirement`
- `metric`
- `operator`
- `threshold`
- `safety_level`
- `next_checks`

## Second Adapted Sample Workspace

The second realistic adapted workspace is:

- `fixtures/bms-requirements-adapted`

This workspace proves a different adapted path:

- external requirements export
  -> adapted `requirements.csv`
  -> normal AVERA workspace
  -> normal AVERA analysis

## Fourth Active Adapter

The fourth real artifact adapter is:

- `adapt-logs`

Purpose:

- convert richer verification log CSV artifacts into AVERA verification-results JSON
- preserve messages, metrics, timestamps, and environment context in a stable reviewable form

## Third Adapted Sample Workspace

The third realistic adapted workspace is:

- `fixtures/bms-log-adapted`

This workspace proves a log-heavy path:

- external verification log CSV
  -> adapted verification JSON
  -> normal AVERA workspace
  -> normal AVERA analysis

## What Comes Next

After the JUnit adapter, the next realistic adapter candidates are:

1. richer test log adapter
2. simulation result adapter
3. requirements export variants
4. stronger signal-trace ingestion paths

## Boundary Rule

Adapters should:

- normalize external artifacts
- preserve source-path provenance
- stay inspectable
- avoid embedding classification logic

Adapters should not:

- replace workspace validation
- bypass stable contracts
- move decision logic out of the kernel
