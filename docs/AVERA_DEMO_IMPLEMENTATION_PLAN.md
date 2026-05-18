# AVERA Demo Implementation Plan

**Date:** 28 April 2026  
**Status:** Thin demo shell plan  
**Scope:** Streamlit-style MVP shell over the existing AVERA core

## Purpose

This document turns `AVERA_DEMO_SHELL.md` into an implementation plan for a
thin, local-first demo shell.

The shell is intentionally narrow. It should make the existing AVERA evidence
kernel easier to show, easier to inspect, and easier to hand off without
changing the core analysis pipeline.

## Planning Assumptions

- the core evidence pipeline already produces report JSON, report Markdown,
  evidence graph JSON, traceability index data, decision records, and workspace
  pack outputs
- the shell reads artifacts from the local workspace rather than re-implementing
  analysis logic
- the shell is a productization layer, not a second source of truth
- the canonical demo path is the BMS thermal regression scenario

## Shell Layout

The MVP shell should behave like a small Streamlit app with a fixed workflow:

1. choose or load a scenario
2. inspect the inputs and artifact availability
3. run or load the analysis result
4. inspect verdict, evidence, traceability, and raw artifacts
5. export the run bundle

Recommended page structure:

- left rail: scenario and run selector
- top strip: run status, scenario metadata, artifact health
- central workspace: one active screen at a time
- bottom drawer or tab bar: raw artifact viewers and export output

## Screen Plan

### 1. Scenario Launcher

Purpose: load the canonical scenario or switch to another prepared fixture.

Interface sections:

- scenario picker
- artifact path summary
- input health indicators
- primary `Analyze` or `Load Run` action
- optional notes panel for the demo story

Core artifacts read:

- `requirements.csv`
- `component_map.json`
- `baseline_results.json`
- `current_results.json`
- optional diff file
- optional signal trace CSV
- fixture or workspace manifest if available

Demo-ready v0:

- one canonical BMS scenario is selectable
- the shell shows whether each input artifact exists and is readable
- the launcher can open a precomputed run without re-running core logic
- the launcher can also point to the input paths used by the CLI workflow

Deferred:

- multi-project scenario management
- remote or hosted artifact loading
- editable artifact authoring
- batch comparison across many scenarios

### 2. Run Overview

Purpose: answer the first question fast: what happened, and how serious is it?

Interface sections:

- verdict summary
- risk and confidence summary
- affected requirement summary
- affected component summary
- top evidence drivers
- next check recommendation

Core artifacts read:

- `avera-report.json`
- `avera-report.md`
- `avera-evidence-graph.json`
- decision record if present
- gate result if present

Demo-ready v0:

- verdict, risk, and confidence are visible above the fold
- the affected requirement and changed file are explicit
- the top evidence is summarized in plain language
- the screen points to the recommended next verification

Deferred:

- trend history across runs
- aggregate portfolio dashboards
- ranking or comparison across unrelated scenarios
- automatic narrative generation beyond the existing report content

### 3. Evidence View

Purpose: show why the verdict exists.

Interface sections:

- baseline vs current comparison
- changed metric list
- threshold comparison panel
- signal evidence panel
- confidence factor panel
- risk driver panel

Core artifacts read:

- `baseline_results.json`
- `current_results.json`
- `signal_trace.csv` if present
- `avera-report.json`
- `avera-evidence-graph.json`

Demo-ready v0:

- the baseline and current values are shown side by side
- threshold breach or compliance is explicit
- the evidence chain is traceable back to a specific metric and requirement
- the shell distinguishes strong evidence from thin evidence

Deferred:

- interactive signal analytics
- editable threshold exploration
- custom evidence scoring controls
- multi-run evidence comparison

### 4. Traceability View

Purpose: explain the mapping chain from change to requirement to test result.

Interface sections:

- changed file or path
- component mapping
- requirement mapping
- test mapping
- failure mapping
- gate or decision outcome
- provenance path view

Core artifacts read:

- `component_map.json`
- `requirements.csv`
- `avera-traceability-index.json` if available
- `avera-report.json`
- `avera-decision.json` if available

Demo-ready v0:

- the shell shows the exact path from changed file to requirement
- the component and test associations are explicit
- provenance is legible without opening raw JSON
- missing mappings are called out instead of inferred

Deferred:

- graph exploration with free-form traversal
- cross-run lineage history
- ownership or org charts
- automatic remediation workflow routing

### 5. Artifact Inspector

Purpose: let a reviewer open the raw material without leaving the shell.

Interface sections:

- JSON viewer
- Markdown viewer
- CSV preview
- raw diff viewer
- artifact path list
- copy-path or open-file controls

Core artifacts read:

- `avera-report.json`
- `avera-report.md`
- `avera-evidence-graph.json`
- `requirements.csv`
- `component_map.json`
- `baseline_results.json`
- `current_results.json`
- diff file
- `signal_trace.csv`
- workspace pack manifest if available

Demo-ready v0:

- raw artifacts are readable in-place
- file paths are shown explicitly
- the user can inspect the exact source material behind the summary
- missing artifacts are surfaced as missing, not synthesized

Deferred:

- inline editing
- artifact diffing between arbitrary runs
- downloadable binary bundles from the shell itself
- attachment management

### 6. Export View

Purpose: hand the run off as a compact, inspectable package.

Interface sections:

- export bundle summary
- included artifact list
- schema version summary
- source path summary
- manifest preview
- copy or download action

Core artifacts read:

- `avera-workspace-pack.json` if available
- `avera-report.json`
- `avera-report.md`
- `avera-evidence-graph.json`
- `avera-traceability-index.json` if available
- `avera-decision.json` if available
- memory ledger slice if available

Demo-ready v0:

- the export view lists what is included and what is omitted
- the manifest reflects the local source paths and schema versions
- the shell can hand off the same evidence bundle the CLI produced

Deferred:

- cloud export targets
- share links
- team collaboration features
- export customization beyond the canonical bundle

## MVP Data Flow

The shell should follow the existing core artifact chain rather than inventing a
new one:

`fixture inputs -> core analysis -> report / graph / traceability / decision -> shell views -> export`

The shell should not reclassify evidence or recalculate verdicts. It should only
read, display, and package the outputs that the core already produced.

## Demo-Ready V0 Definition

The shell is demo-ready when it can do all of the following on the canonical BMS
scenario:

- load the prepared scenario and show input health
- display the verdict, risk, and confidence clearly
- show baseline vs current evidence with the threshold breach
- show the changed-file to requirement trace
- let a reviewer inspect raw artifacts in place
- present the exported bundle or manifest for handoff
- make missing evidence obvious instead of filling gaps with guesswork

## Deferred Beyond V0

Keep the first shell narrow. Defer anything that would make it feel like a
general analytics product:

- dashboard-style summaries across many runs
- trend exploration UI
- editable artifacts or reports
- remote storage and collaboration
- provider-specific integrations
- speculative insights not backed by core artifacts
- any view that hides the underlying evidence chain

## Implementation Notes

- Keep each screen aligned to one user question.
- Read artifacts directly from the local workspace.
- Prefer deterministic renderers for JSON, Markdown, CSV, and diff files.
- Keep empty states explicit and factual.
- Use the core report and traceability outputs as the source of truth for all
  displayed verdicts and relationships.

