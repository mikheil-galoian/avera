# AVERA Roadmap

**Date:** 29 April 2026  
**Status:** Updated against implemented kernel state

## Roadmap Baseline

The roadmap now starts from the fact that AVERA already has a working local
kernel and first demo shell.

Already implemented as of 29 April 2026:

- workspace validation and ingestion
- baseline vs current comparison
- conservative classification and reporting
- evidence graph export
- gate policy
- engineering memory ledger
- traceability index
- decision engine
- trend index
- stable artifact contract validation
- workspace pack export
- thin Streamlit demo shell
- `avera demo-refresh` orchestration

So the next roadmap question is no longer "should these layers exist?".
It is "how do we harden, extend, and productize the implemented kernel without
breaking its conservative proof model?".

## Phase 0: Concept Capture

Status:

- complete

What this phase established:

- AVERA as a standalone automotive engineering project direction
- the evidence-first positioning
- the narrow first workflow around change impact and regression evidence
- the initial architecture, product brief, and MVP planning documents

## Phase 1: Local Evidence Kernel

Status:

- largely complete

What shipped:

- local evidence workspace contract
- local CLI analysis flow
- BMS fixture matrix
- baseline vs current comparison
- risk and confidence classification
- JSON and Markdown report generation
- evidence graph generation
- workspace validation and report validation

What still belongs here:

- reliability hardening
- fixture expansion where it sharpens existing verdict policy
- clearer runtime ergonomics and packaging

Primary audience:

- automotive embedded software engineers
- validation engineers
- BMS/ECU teams

## Phase 2: Kernel Completion And Demo Productization

Status:

- in progress

Goal:

- stabilize the kernel layers that are now implemented and make the canonical
  demo consistently reviewable

Scope:

- decision engine policy hardening
- workspace pack polish
- stable artifact contract enforcement across artifacts
- trend layer hardening
- demo shell usability and artifact presentation
- repeatable `demo-refresh` output for the canonical BMS path
- stronger local verification through `pytest` and fixture runs

Exit criteria:

- the end-to-end demo flow can be regenerated deterministically
- the architecture-facing docs match shipped behavior
- the shell remains thin and artifact-driven
- downstream consumers can trust the stable contract layer

## Phase 3: Richer Local Evidence Inputs

Status:

- next

Goal:

- expand the kernel from the current fixture/workspace contract to more realistic
  automotive verification artifacts while staying local-first

Scope:

- JUnit XML ingestion
- richer generic test-log ingestion
- requirements CSV/JSON variants
- simulation result CSV/JSON
- CAN trace CSV normalization
- stronger signal trace use in analysis, not only in reporting
- better local change-artifact capture

Important boundary:

- this phase should deepen the current proof chain, not replace it with looser
  heuristics

## Phase 4: Validation Workflow Integration

Goal:

- connect the local kernel to more realistic engineering validation workflows

Scope:

- SIL result ingestion
- HIL result ingestion through exported reports
- scenario mapping
- test case reuse tracking
- Jama/Polarion-style export ingestion
- safety-relevance tagging
- stronger requirement-to-verification provenance

Primary audience:

- validation teams
- systems engineering teams
- safety engineering teams

## Phase 5: Compliance Evidence Builder

Goal:

- help teams assemble reviewable evidence for release, audit, and safety
  workflows

Scope:

- ISO 26262 evidence organization
- ASPICE traceability support
- ISO/SAE 21434 cybersecurity evidence organization
- release review report assembly
- human approval workflow

Important boundary:

- AVERA should help assemble and explain evidence.
- AVERA should not claim automatic certification.

## Phase 6: Team Memory And Shared Review

Goal:

- evolve the current local memory and pack layers into a stronger engineering
  memory boundary for team use

Scope:

- persistent multi-run history beyond a single local ledger
- richer decision history
- shared review bundles
- pack comparison and inspection workflows
- durable lineage for requirements, tests, and repeated failures
- preparation for a shared graph or knowledge layer

This phase should build on the current memory, trend, and workspace-pack layers
rather than bypassing them.

## Phase 7: Field Feedback And Lifecycle Intelligence

Goal:

- connect engineering evidence to later lifecycle signals without weakening the
  current proof discipline

Scope:

- fleet telemetry summaries
- warranty and service event correlation
- field failure similarity search
- OTA update risk comparison
- lifecycle evidence graph extensions

Primary audience:

- connected vehicle teams
- reliability teams
- warranty analytics teams
- software-defined vehicle platform teams

## Current Priorities

The most important near-term work is:

1. keep architecture and product docs synchronized with the implemented kernel
2. stabilize the runtime and local environment path around the already proven kernel
3. improve the thin demo shell without moving product logic into it
4. expand evidence inputs only after the current kernel remains stable
5. prepare the pilot-readiness layer defined in [AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md](/Users/mac/Desktop/AVERA/docs/AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md)

## 20-30 Year Direction

AVERA should still grow beyond a single automotive software tool into:

`Engineering Memory Infrastructure for Mobility`

Potential long-term domains:

- passenger vehicles
- commercial trucks
- buses
- robotaxis
- off-highway equipment
- agricultural machinery
- construction machinery
- battery energy systems
- robotics and autonomous machines

The durable need is still preserving evidence, traceability, decision history,
and risk reasoning across long-lived engineered systems. The difference now is
that AVERA already has a real local kernel to evolve from, instead of only a
concept sketch.
