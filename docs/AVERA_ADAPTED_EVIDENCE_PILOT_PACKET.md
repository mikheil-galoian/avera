# AVERA Adapted Evidence Pilot Packet

**Date:** 1 May 2026  
**Status:** Narrow pilot packet for adapted evidence paths  
**Purpose:** Define the first practical pilot boundary for AVERA using adapted external artifacts rather than only hand-authored fixture inputs

## Why This Packet Exists

AVERA is now beyond a fixture-only demo.

It can accept external artifacts through thin adapters and turn them into a
normal local AVERA workspace. This packet defines how to present and pilot that
capability without pretending the product is already a broad enterprise
platform.

## Current Adapted Paths

### 1. ADAS Simulation Path

Workspace:

- `fixtures/adas-simulation-adapted`

External inputs:

- `baseline_simulation_results.csv`
- `current_simulation_results.csv`

Adapter:

- `adapt-simulation`

Result:

- adapted `baseline_results.json`
- adapted `current_results.json`
- full AVERA analysis, traceability, decision, trend, and workspace pack

### 2. BMS Requirements Path

Workspace:

- `fixtures/bms-requirements-adapted`

External input:

- `requirements_export_variant.csv`

Adapter:

- `adapt-requirements`

Result:

- adapted `requirements.csv`
- full AVERA analysis on a workspace whose requirements came from a richer
  upstream export

## Operator Demo Order

Use this order:

1. show the canonical BMS path
2. show the adapted ADAS simulation path
3. show the adapted BMS requirements path
4. explain that AVERA keeps the kernel contract stable while the adapters absorb
   external artifact variety

## Pilot Scope

The first adapted-evidence pilot should stay narrow:

- one domain at a time
- one adapter path at a time
- one local operator path
- one human review boundary

Good first pilot examples:

- ADAS simulation regression review
- BMS requirements/export normalization before change review
- BMS verification-log normalization before review triage

## What To Show In The Shell

For adapted scenarios, highlight:

- scenario profile
- raw source artifact visibility
- normalized AVERA artifacts
- evidence-backed verdict
- workspace handoff readiness

## What Success Looks Like

An adapted-evidence pilot is successful when:

1. the upstream artifact is realistic enough to matter
2. the adapter output is inspectable
3. the normalized workspace still behaves like a standard AVERA workspace
4. the reviewer trusts the evidence path more than ad hoc artifact reading

## Limits To State Honestly

- adapters are still local and explicit
- supported artifact varieties are still narrow
- operator setup is still local-first
- this is a pilot path, not a broad integration rollout
