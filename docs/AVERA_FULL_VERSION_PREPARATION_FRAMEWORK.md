# AVERA Full-Version Preparation Framework

**Date:** 30 April 2026  
**Status:** Active preparation framework  
**Purpose:** Define the path from the current design-partner-ready prototype to a pilot-ready product and later a fuller engineering platform

## Why This Document Exists

AVERA now has a strong local kernel, a full green test suite, a working BMS
story, a working ADAS second domain, and a real design-partner packet.

That means the next question is no longer:

`can this be built?`

The next question is:

`what must be prepared, hardened, expanded, and tested before AVERA becomes pilot-ready and later a fuller product?`

This document answers that question in four layers:

1. what next
2. what before pilot
3. what before fuller version
4. what to test at each layer

## Current Starting Point

AVERA already has:

- local evidence ingestion
- baseline vs current comparison
- conservative classification
- report and evidence graph generation
- gate policy
- engineering memory ledger
- traceability index
- decision engine
- trend layer
- stable artifact contracts
- workspace pack
- query layer
- demo shell
- canonical BMS demo story
- ADAS second-domain proof
- full green `pytest` suite

This is enough to stop thinking like a concept team and start thinking like a
product-hardening team.

## Layer 1: What Next

### Goal

Turn the current prototype into a pilot-preparation baseline.

### Main Workstreams

#### 1. Runtime Stabilization

Needed:

- define the supported Python runtime for AVERA
- make the demo shell predictable to launch
- reduce cold-start friction in presentation and review flows
- document one reproducible local environment path

Runtime contract for the current stage:

- repository-local `.venv` is the supported execution path
- `./start_demo.sh` is the canonical demo launcher
- the CLI remains the source of truth even when the shell is used for review
- live demo continuity must not depend on a single Streamlit cold-start path
- the ADAS static showcase remains an approved fallback for external meetings

Why:

The kernel is strong enough now that runtime inconsistency is a bigger risk than
core logic uncertainty.

Exit criteria for this workstream:

- one documented Python/runtime path is treated as supported
- one clean demo launch path works without operator improvisation
- one approved fallback path exists for external showing
- runtime guidance is reflected consistently in the main docs

#### 2. Shell Hardening

Needed:

- better artifact reading ergonomics
- cleaner scenario switching
- more stable presentation states
- optional screenshot/export-friendly views

Why:

The shell should stay thin, but it must become easier to use in review and
pilot conversations.

#### 3. Domain Matrix Expansion

Needed:

- retain BMS
- retain ADAS
- add one more believable domain after that, such as ECU control logic or
  powertrain calibration

Why:

The third domain is where AVERA starts to look like a reusable engineering proof
kernel instead of a two-scenario prototype.

#### 4. Real Artifact Adapters

Needed:

- JUnit or xUnit ingestion
- richer requirements export variants
- simulation result adapters
- log parsing for more realistic evidence inputs
- stronger signal trace handling

Why:

Synthetic fixtures proved the model. Realistic artifact adapters will prove
practical usefulness.

## Layer 2: What Before Pilot

### Goal

Make AVERA safe and clear enough to try in one narrow real workflow.

### Pilot-Ready Conditions

AVERA should have:

1. a stable runtime recipe
2. one repeatable demo path
3. at least two trusted domains
4. one realistic artifact adapter set
5. one narrow pilot workflow definition
6. one operator playbook for running the pilot locally

The minimum pilot-readiness gate should be explicit:

- operator setup succeeds from the documented runtime path
- canonical demo-refresh and artifact validation commands complete cleanly
- at least one cross-domain fallback asset exists for continuity during review
- known runtime quirks are documented and separated from kernel health
- the pilot operator does not need undocumented environment fixes mid-run

### Pilot Scope Should Be Narrow

Recommended pilot boundary:

- one team
- one domain
- one artifact family
- one repeated review workflow
- local-first execution
- human review around the output

### What Must Be Ready Before A Pilot Starts

- setup instructions that actually work
- a fixture-to-real-artifact mapping strategy
- clear success criteria
- known limitations written down
- no overclaiming about automation or compliance
- a named fallback path when the shell is not the fastest way to continue a review

## Layer 3: What Before A Fuller Version

### Goal

Prepare AVERA to become a more durable engineering product rather than only a
strong local prototype.

### Major Requirements

#### 1. Stronger Ingestion Layer

- multiple artifact formats
- stronger validation
- artifact family versioning
- graceful handling of partial evidence

#### 2. Stronger Traceability Model

- richer requirement provenance
- better test lineage
- repeated failure patterns
- stronger cross-run linkage

#### 3. Stronger Review Surface

- a more mature shell or application layer
- reusable inspection views
- export-friendly review states
- clearer evidence navigation

#### 4. Durable Engineering Memory

- stronger long-run history
- comparison across runs
- component trend evolution
- better decision lineage

#### 5. Integration Preparation

- CLI remains truth boundary
- future integrations remain downstream of stable contracts
- no hidden product logic in the UI

## Layer 4: What To Test At Each Layer

### Core Kernel Tests

Always test:

- comparator behavior
- classifier behavior
- decision behavior
- traceability behavior
- trend behavior
- contract validation behavior

### Fixture Matrix Tests

Always test:

- BMS fixture family
- ADAS fixture family
- every verdict class that AVERA claims to support
- stable expected outputs

### Artifact Adapter Tests

When adapters are added, test:

- valid sample inputs
- malformed sample inputs
- partial evidence cases
- deterministic normalized outputs

### Orchestration Tests

Always test:

- `demo-refresh`
- report generation
- pack generation
- stable artifact contract validation

### Shell Tests

Test at least:

- scenario switching
- artifact presence rendering
- overview rendering
- fallback presentation path

### Pilot Readiness Tests

Before a pilot:

- clean environment startup
- repeatable end-to-end local run
- realistic artifact sample pass
- operator runbook walkthrough

## Execution Order

The right order from here is:

1. stabilize runtime
2. harden shell
3. add realistic artifact adapters
4. expand domain matrix
5. define pilot workflow
6. test the full pilot path

That order matters.

It prevents AVERA from becoming broader before it becomes steadier.

## Runtime Stabilization Deliverables

Before this layer is considered complete, AVERA should have:

1. one supported runtime statement across the docs
2. one canonical launch command for shell-driven showing
3. one verification path tied to that runtime
4. one approved fallback presentation path
5. one short operator note describing the difference between runtime quirks and kernel failures

## What Not To Prioritize Yet

Not yet:

- hosted SaaS
- broad enterprise integration
- automatic compliance claims
- multi-user platform behavior
- dashboard-first product framing

Those are later layers.

## Success Signal

This framework is working if AVERA moves from:

`strong local prototype`

to:

`pilot-ready engineering evidence product`

without losing:

- evidence discipline
- deterministic contracts
- conservative verdict logic
- human-review orientation
