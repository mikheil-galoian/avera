# AVERA Adapted Pilot One-Pager

**Date:** 2 May 2026  
**Audience:** Design partner / pilot sponsor  
**Format:** Short product-facing variant focused on adapted evidence paths

## What AVERA Does

AVERA is an evidence-first engineering review layer for automotive change
impact.

It helps a team answer:

- what changed?
- what requirements are affected?
- what evidence proves the problem?
- what should happen before release?

## What Is New In This Pilot Set

AVERA now supports adapted evidence paths, not only hand-authored local demo
artifacts.

Current adapted pilot set:

1. `adas-simulation-adapted`
2. `bms-requirements-adapted`
3. `bms-log-adapted`

## Why That Matters

This means AVERA can normalize external engineering artifacts into one stable
local review contract while keeping the same kernel and review flow.

Supported artifact bridges now include:

- JUnit / xUnit XML
- simulation CSV
- richer requirements export CSV
- richer verification log CSV

## What A Team Sees

For each adapted scenario, AVERA can show:

- raw source artifact
- normalized AVERA workspace artifact
- evidence-backed verdict
- traceability
- release decision
- workspace pack for handoff

## Narrow Pilot Promise

The current promise is deliberately narrow:

`normalize external evidence into a stable review workspace and make one engineering decision path easier to trust.`

## Best Early Pilot Shapes

- ADAS simulation regression review
- BMS requirements-export normalization before change review
- BMS verification-log normalization before release triage

## Current Boundaries

AVERA is not yet:

- a broad enterprise integration platform
- a hosted SaaS rollout
- an automatic certification engine

It is strongest today as a local, evidence-first review workflow.
