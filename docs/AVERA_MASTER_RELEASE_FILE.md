# AVERA Master Release File

**Date:** 30 April 2026  
**Status:** Primary single-file operating document  
**Purpose:** Hold the full project logic in one place for continued development, shell creation, pilot preparation, and eventual release assembly

## What This File Is

This is the one file that should let a future operator, builder, reviewer, or
release owner understand AVERA without reconstructing the whole document tree
from scratch.

It is not meant to replace every supporting document.

It is meant to be the single master reference that explains:

- what AVERA is
- what is already implemented
- how the architecture is organized
- how the system is run and tested
- what the current product boundary is
- what still needs to be built
- how the shell should evolve
- how the project moves toward pilot and release

For outward-facing and pilot-readiness work, the companion reference is:

- [AVERA_READINESS_BASE.md](/Users/mac/Desktop/AVERA/docs/AVERA_READINESS_BASE.md)
- [AVERA_PILOT_EXECUTION_PREP_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_EXECUTION_PREP_V0.md)
- [AVERA_PILOT_SAFETY_CHECKLIST.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_SAFETY_CHECKLIST.md)
- [AVERA_REAL_PILOT_RUN_01.md](/Users/mac/Desktop/AVERA/docs/AVERA_REAL_PILOT_RUN_01.md)
- [AVERA_PILOT_OUTREACH_RUN_01.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_OUTREACH_RUN_01.md)
- [AVERA_PILOT_MOTION_LAUNCH_KIT_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_MOTION_LAUNCH_KIT_V0.md)

## Product Definition

**AVERA** means:

`Automotive Verification, Evidence & Risk Architecture`

AVERA is an evidence-first automotive engineering platform.

The first product boundary is:

`AVERA Change Impact`

That boundary focuses on one narrow but valuable workflow:

`change review with baseline-vs-current evidence and human release triage`

## Core Product Promise

AVERA helps engineering teams answer:

- what changed?
- what requirements are affected?
- what tests or failures are involved?
- what evidence proves the issue?
- what risk is present?
- what should happen before release?

Core principle:

`engineering truth, preserved as evidence`

## Current Product Boundary

The current AVERA boundary is:

- local-first
- operator-driven
- evidence-first
- review-oriented
- conservative in verdicts

It is not yet:

- a hosted SaaS product
- a broad enterprise rollout
- a generic AI assistant
- an automatic compliance or certification engine

## What Is Already Implemented

The local kernel already includes:

- ingestion
- baseline vs current comparison
- conservative classification
- reports
- evidence graph
- gate policy
- engineering memory
- traceability index
- decision engine
- trend layer
- stable artifact contracts
- workspace pack
- query layer
- demo shell
- canonical BMS demo path
- ADAS second-domain proof
- full green `pytest` suite

## Implemented Artifact Flow

The effective kernel flow is:

```text
workspace evidence
  -> ingestion
  -> normalized models
  -> comparison
  -> classification
  -> report
  -> evidence graph
  -> gate
  -> traceability
  -> decision
  -> trend
  -> workspace pack
```

The shell is a thin review layer above those artifacts.

## Current Domain Proof

The current domain proofs are:

### 1. BMS

Primary story:

- `bms-fast-charge`

Purpose:

- canonical regression story
- main demo narrative
- main case study

### 2. ADAS

Primary story:

- `adas-pedestrian-detection-regression`

Purpose:

- second-domain portability proof
- evidence model survives domain change
- presentation-safe fallback through static showcase asset

## Supported Inputs v0

Current supported pilot inputs:

1. change description
2. baseline verification results
3. current verification results
4. requirements export
5. component map
6. optional signal trace

Current practical artifact types:

- JSON verification results
- CSV requirements
- JSON component map
- text change description
- CSV signal trace

Current adapter bridge:

- JUnit / xUnit XML can now be adapted into AVERA verification-results JSON
- simulation-results CSV can now be adapted into AVERA verification-results JSON
- requirements export variants can now be adapted into stable `requirements.csv`
- richer verification log CSV can now be adapted into AVERA verification-results JSON

## Supported Outputs v0

Current supported outputs:

1. assessment report
2. evidence graph
3. gate result
4. traceability index
5. decision artifact
6. trend artifact
7. workspace pack

These are the current release-grade review artifacts of the kernel.

## Runtime Contract

The supported runtime path is:

1. repository `.venv`
2. `scripts/runtime_doctor.py`
3. `./start_demo.sh`
4. CLI commands as source-of-truth execution

Important runtime truth:

- CLI is the truth boundary
- shell is the review boundary
- static fallback assets are allowed for continuity during external showing

Known runtime quirk:

- `Python 3.14 + Streamlit` may cold-start slowly for the shell

This is treated as a runtime/presentation issue, not as a kernel failure.

## Current Visual Packet

The current visual fallback path for external showing is:

1. [AVERA_ADAPTED_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAPTED_SHOWCASE.html)
2. [AVERA_ADAPTED_VISUAL_PACKET.md](/Users/mac/Desktop/AVERA/docs/AVERA_ADAPTED_VISUAL_PACKET.md)
3. [avera-adapted-showcase-full.png](/Users/mac/Desktop/AVERA/docs/assets/avera-adapted-showcase-full.png)
4. [AVERA_FIRST_CONTACT_BUNDLE.md](/Users/mac/Desktop/AVERA/docs/AVERA_FIRST_CONTACT_BUNDLE.md)

This packet exists so AVERA can still be shown cleanly when the live Streamlit shell
is slow to cold-start on the current runtime.

## Current Go-To-Use Layer

The current outward-facing execution layer now includes:

1. [AVERA_OUTREACH_MESSAGE_VARIANT.md](/Users/mac/Desktop/AVERA/docs/AVERA_OUTREACH_MESSAGE_VARIANT.md)
2. [AVERA_TARGET_ACCOUNT_MAP_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_TARGET_ACCOUNT_MAP_V0.md)
3. [AVERA_NARROW_PILOT_INTAKE_CHECKLIST.md](/Users/mac/Desktop/AVERA/docs/AVERA_NARROW_PILOT_INTAKE_CHECKLIST.md)
4. [AVERA_PILOT_SAFETY_CHECKLIST.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_SAFETY_CHECKLIST.md)
5. [AVERA_TARGET_SHORTLIST_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_TARGET_SHORTLIST_V0.md)
6. [AVERA_PILOT_CONTACT_TRACKER_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_CONTACT_TRACKER_V0.md)
7. [AVERA_SAMPLE_EXPORT_REQUEST_TEMPLATE.md](/Users/mac/Desktop/AVERA/docs/AVERA_SAMPLE_EXPORT_REQUEST_TEMPLATE.md)
8. [AVERA_REDDIT_OUTREACH_CHECKLIST.md](/Users/mac/Desktop/AVERA/docs/AVERA_REDDIT_OUTREACH_CHECKLIST.md)
9. [AVERA_TARGET_CANDIDATE_PROFILES_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_TARGET_CANDIDATE_PROFILES_V0.md)
10. [AVERA_PILOT_CONTACT_TRACKER_SEED_01.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_CONTACT_TRACKER_SEED_01.md)
11. [AVERA_EXTERNAL_ARTIFACT_EXAMPLES_BASE.md](/Users/mac/Desktop/AVERA/docs/AVERA_EXTERNAL_ARTIFACT_EXAMPLES_BASE.md)
12. [AVERA_ENGLISH_FIRST_CONTACT_BUNDLE.md](/Users/mac/Desktop/AVERA/docs/AVERA_ENGLISH_FIRST_CONTACT_BUNDLE.md)
13. [AVERA_OUTREACH_DRAFTS_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_OUTREACH_DRAFTS_V0.md)
14. [AVERA_REDDIT_POST_DRAFT_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_REDDIT_POST_DRAFT_V0.md)
15. [AVERA_FORWARDABLE_INTRO_BLURB.md](/Users/mac/Desktop/AVERA/docs/AVERA_FORWARDABLE_INTRO_BLURB.md)
16. [AVERA_TARGET_OUTREACH_PACKET_INDEX.md](/Users/mac/Desktop/AVERA/docs/AVERA_TARGET_OUTREACH_PACKET_INDEX.md)

This layer exists to move AVERA from a prepared prototype into first real design-partner and narrow-pilot conversations.

## Operator Path

Recommended operator sequence:

1. run runtime doctor
2. validate workspace
3. run analysis
4. build traceability
5. evaluate decision
6. build trend
7. build workspace pack
8. review in shell or artifacts
9. hand off the bundle for human review

Core commands:

```bash
.venv/bin/python scripts/runtime_doctor.py
python3 -B scripts/run_all_fixtures.py
.venv/bin/python -m pytest -q tests
PYTHONPATH=src python3 -B -m avera demo-refresh \
  --project fixtures/bms-fast-charge \
  --report-out reports/fixtures/bms-fast-charge \
  --memory reports/avera-memory.jsonl \
  --traceability-out reports/avera-traceability-index.json \
  --decision-out reports/avera-decision.json \
  --trend-out reports/avera-trend-index.json \
  --pack-out reports/avera-workspace-pack.json
PYTHONPATH=src python3 -B -m avera validate-artifact \
  --artifact workspace_pack \
  --path reports/avera-workspace-pack.json \
  --bundle
./start_demo.sh
```

## Review Surface Policy

For the current stage:

- generation happens in the kernel
- navigation happens in the shell
- continuity can use static showcase assets

The shell must stay thin.

It should not silently absorb product logic that belongs in the CLI/kernel.

## Current Readiness State

The project is currently:

- kernel-proven
- test-proven
- demo-proven
- design-partner-ready
- pilot-preparation-ready

It is not yet fully:

- pilot-proven on real external artifacts
- integration-ready for wider enterprise use
- release-ready as a broad public product

## What The Project Needs Next

The next logical execution order is:

### 1. Runtime Stabilization

Goal:

- make the supported runtime path explicit and predictable

Status:

- substantially in place

### 2. Shell Hardening

Goal:

- make the review surface more usable for pilot work

Needed:

- better artifact reading ergonomics
- clearer scenario switching
- more stable review states
- better presentation-friendly states

### 3. Real Artifact Adapters

Goal:

- move beyond curated fixtures into more realistic engineering evidence

Needed:

- JUnit / xUnit
- richer logs
- simulation outputs
- requirements export variants
- stronger signal-trace use

Current progress:

- JUnit / xUnit adapter active
- simulation CSV adapter active
- first adapted ADAS sample workspace active

### 4. Domain Matrix Expansion

Goal:

- add a third believable domain

Needed:

- BMS stays
- ADAS stays
- add ECU / powertrain / calibration-style third path

### 5. Pilot Package Hardening

Goal:

- make the first narrow pilot truly runnable

Needed:

- operator kit
- supported artifact guide
- known limitations
- repeatable workflow
- fallback order

## What Must Be Tested

### Core

- comparator
- classifier
- decision
- traceability
- trend
- contracts

### Fixture Matrix

- BMS family
- ADAS family
- every claimed verdict class

### Orchestration

- `demo-refresh`
- pack generation
- contract validation

### Shell

- scenario switching
- artifact rendering
- overview rendering
- continuity fallback behavior

### Pilot Readiness

- clean startup
- repeatable local run
- operator walkthrough
- realistic artifact sample set once adapters exist

## What Counts As Pilot Success

A first pilot is successful if:

1. the workflow matches a real engineering pain
2. the inputs are realistic enough to be useful
3. the proof chain is trusted more than ad hoc triage alone
4. the reviewer can act on the output
5. the next pilot iteration is obvious

## What Counts As Release Assembly

For the current stage, “release” should mean:

- one clear runtime path
- one clear demo path
- one clear operator path
- one clear pilot boundary
- one clear document set
- one clear artifact contract

Not:

- mass distribution
- broad hosting
- enterprise-scale rollout

## Approved First Showing Kit

The current best first showing kit is:

1. [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)
2. [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)
3. [AVERA_EXTERNAL_DEMO_FLOW.md](/Users/mac/Desktop/AVERA/docs/AVERA_EXTERNAL_DEMO_FLOW.md)
4. [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)
5. `./start_demo.sh`

## Supporting Documents

If deeper context is needed, the main supporting docs are:

- [AVERA_INDEX.md](/Users/mac/Desktop/AVERA/docs/AVERA_INDEX.md)
- [AVERA_RUNTIME_STABILIZATION.md](/Users/mac/Desktop/AVERA/docs/AVERA_RUNTIME_STABILIZATION.md)
- [AVERA_REAL_ARTIFACT_ADAPTERS.md](/Users/mac/Desktop/AVERA/docs/AVERA_REAL_ARTIFACT_ADAPTERS.md)
- [AVERA_PILOT_OPERATING_MODEL_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_OPERATING_MODEL_V0.md)
- [AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md](/Users/mac/Desktop/AVERA/docs/AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md)
- [AVERA_ROADMAP.md](/Users/mac/Desktop/AVERA/docs/AVERA_ROADMAP.md)
- [AVERA_DECISION_LOG.md](/Users/mac/Desktop/AVERA/docs/AVERA_DECISION_LOG.md)

## Final Rule

From this point on, the project should not invent work arbitrarily.

It should move by this order:

1. stabilize
2. harden
3. adapt real artifacts
4. expand domains
5. prepare pilot
6. run first narrow external use
