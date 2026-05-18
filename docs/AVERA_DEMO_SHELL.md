# AVERA Demo Shell

**Date:** 30 April 2026  
**Status:** Active local review shell  
**Scope:** Streamlit demo surface over the existing AVERA core

## Purpose

This document defines the current demo shell for AVERA: a lightweight, local,
inspection-first review surface that sits on top of the evidence kernel without
changing the kernel itself.

The shell is meant to make AVERA easy to show, easy to explore, and easy to
validate in front of engineers, while keeping the core workflow explicit:

`change -> baseline -> current -> evidence -> verdict -> next check`

## Current Shell Boundary

The current shell already provides:

- scenario selection from local fixtures
- an artifact inventory with ready/missing status
- overview, evidence, traceability, workspace, and raw artifact tabs
- scenario-aware context for BMS and ADAS demos
- visibility into raw adapter source artifacts when they are present in a workspace
- an explicit adapted-pilot mode for scenarios built from normalized external artifacts
- review navigation for component / requirement / test traceability focus
- pilot-use guidance and workspace-pack handoff support

The shell remains intentionally thin:

- no hidden business logic
- no alternate decision engine inside the UI
- no replacement for CLI or artifact contracts

## Design Principles

- keep the shell thin and local-first
- show evidence, not just summaries
- preserve conservative classification labels
- make every verdict traceable back to artifacts
- support a canonical BMS path and a working ADAS cross-domain path
- keep the UI inspectable enough that engineers can trust it

## Current Surface

The shell is implemented in a Streamlit-style pattern with:

- a single landing workspace for one analysis run
- side navigation for switching between runs or scenarios
- tabs for overview, evidence, traceability, workspace, and artifacts
- artifact viewers that render JSON, text, and CSV directly
- a concise control area for analysis and refresh
- scenario profiles that explain why a given fixture matters

Its job is still the same: make the AVERA reasoning legible.

## Screens

### 1. Sidebar Launcher

Purpose: select a prepared workspace and trigger local analysis.

Shows:

- scenario selector
- fixture path
- report path
- `Analyze` button
- `Refresh` button

### 2. Run Overview

Purpose: answer the first question quickly.

Shows:

- verdict
- risk
- confidence
- component impact summary
- requirement impact summary
- top evidence drivers
- release decision summary
- corrective actions
- verification playbook
- operator sequence

This screen should be the default post-run destination.

### 3. Evidence View

Purpose: show why the verdict exists.

Shows:

- baseline vs current test comparison
- changed metrics
- threshold comparisons
- supporting signal excerpts
- rules triggered
- confidence factors
- risk drivers

### 4. Artifact Inspector

Purpose: let the user open the raw material.

Shows:

- report JSON
- report Markdown
- evidence graph JSON
- requirements CSV
- component map JSON
- baseline and current result JSON
- diff contents
- signal trace CSV or preview

### 5. Traceability View

Purpose: explain the mapping chain.

Shows:

- index summary
- owner routing
- focused review navigation by component / requirement / test
- threshold evidence inside the selected entry
- risk and gate history for the selected entry
- raw traceability payload as a secondary layer

This view should make the provenance of the verdict obvious in one glance.

### 6. Workspace / Handoff View

Purpose: capture the run for handoff.

Shows:

- source inputs
- change context
- pilot-use guidance
- workspace pack summary
- handoff readiness checks
- trend snapshot
- download action for workspace pack JSON

## User Flow

1. The user opens the shell on a canonical scenario.
2. The shell explains the scenario domain, title, use case, and primary signal.
3. The user runs analysis or refreshes the prepared artifact set.
4. The shell shows verdict, risk, confidence, and release decision immediately.
5. The user inspects evidence and requirement impact.
6. The user opens traceability review and selects a component, requirement, or test focus.
7. The user checks workspace handoff readiness and exports the workspace pack.

The flow should be shallow. A good demo should not require navigation hunting.

## Artifacts To Show

The shell should display the artifacts that make the reasoning auditable:

- baseline verification results
- current verification results
- requirements export
- component map
- signal trace or signal summary
- evidence graph
- final report in Markdown
- final report in JSON
- decision or gate result
- export manifest
- memory log when available

If a fixture does not include one of these artifacts, the shell should say so
explicitly instead of inventing missing evidence.

## Canonical BMS Demo Narrative

Use the BMS thermal regression as the standard demo story.

Recommended narrative:

1. An engineer changes battery cooling logic.
2. Baseline verification passes the fast-charge scenario.
3. Current verification fails because maximum cell temperature rises above the
   allowed threshold.
4. A changed file maps to the BMS thermal control component.
5. The requirement `BMS-REQ-112` is implicated.
6. The shell shows the threshold breach and the relevant signal or metric
   delta.
7. A conservative verdict is produced: `confirmed_regression`.
8. The shell recommends the next verification step, such as BMS HIL fast-charge
   coverage.

Canonical artifact pair:

- baseline `max_cell_temp_c`: `47.1`
- current `max_cell_temp_c`: `52.8`

Canonical classification:

- verdict: `confirmed_regression`
- risk: `high`
- confidence: `high`

Canonical demo message:

`The change exceeded the thermal requirement, and the evidence chain is strong enough to block release until follow-up verification is complete.`

## Current Review-Ready Shell

The current useful shell includes:

- scenario picker
- analysis and refresh controls
- verdict / risk / confidence / decision summary
- requirement impact section
- structured traceability review navigation
- raw artifact viewer
- workspace pack export
- pilot-use guidance

Current shell success means the demo can be understood without opening CLI
output directly, and a reviewer can reach a handoff boundary from the UI.

## What The Shell Is Not

- not the primary evidence engine
- not a replacement for the CLI
- not a full data-management app
- not a dashboard for speculative analytics
- not a presentation layer that hides the underlying artifacts

## Acceptance Criteria

The shell is good enough for the current project stage when it can:

- load the canonical BMS scenario
- load the ADAS scenario or fall back to the static ADAS showcase asset
- run or display the baseline vs current comparison
- show the verdict, risk, and confidence clearly
- surface the affected requirement and changed file
- expose the raw artifacts behind the summary
- let a reviewer follow the reasoning chain without guesswork
- show structured decision and verification guidance
- export a compact run package for handoff
