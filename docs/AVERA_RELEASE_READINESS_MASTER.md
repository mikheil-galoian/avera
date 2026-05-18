# AVERA Release & Readiness Master Document

**Date:** 30 April 2026  
**Status:** Master release/readiness framing for the current AVERA stage  
**Purpose:** Consolidate the structure, operator model, release boundary, and readiness logic for the current AVERA product state in one document

## Why This Document Exists

AVERA now has enough working surface that the project no longer needs scattered
answers to simple questions like:

- what exactly is the product boundary today?
- what is already real versus still aspirational?
- how should an operator run it?
- what should be considered release-ready for the current stage?
- what still must be hardened before broader use?

This document is the single release/readiness entry point for the current
project stage.

It does not replace the deeper architecture, verification, pilot, or positioning
documents. It gives one operator- and release-oriented frame over all of them.

## Product Frame

AVERA stands for:

`Automotive Verification, Evidence & Risk Architecture`

Current practical product shape:

`AVERA Change Impact`

Current product promise:

AVERA helps an engineering team compare baseline versus current evidence, map
the impact of a change, identify affected requirements/tests/components, and
produce a conservative review package before release.

AVERA is not currently framed as:

- a hosted platform
- a broad enterprise integration suite
- an autonomous engineering agent
- a final release authority

The current stage is:

`local-first evidence kernel with demo and pilot-readiness packaging`

## Current Release Boundary

The current release boundary should be understood as:

1. a working local Python kernel
2. a supported operator path
3. a thin review shell
4. stable review artifacts
5. design-partner and pilot-facing documentation

That means the project is already beyond concept stage, but not yet at a
generalized production platform stage.

## Current Readiness Statement

At the time of this document, AVERA should be described as:

`design-partner-ready local prototype with pilot-oriented operating boundary`

That framing is precise because the project already has:

- implemented evidence pipeline layers
- full fixture matrix coverage
- a working second domain proof
- full test-suite verification
- a one-command demo launcher
- operator guidance
- release-facing artifacts and demo material

But it still has open next-stage work around:

- shell hardening
- broader real artifact adapters
- wider domain expansion
- narrower first-pilot execution

## System Structure

The current system should be read in five layers.

### 1. Kernel

The kernel is the source of truth.

It is responsible for:

- workspace validation
- evidence ingestion
- baseline/current comparison
- fault and risk classification
- report generation
- evidence graph generation
- gate evaluation
- traceability
- decision generation
- trend generation
- workspace pack export

### 2. Contracts

The contract layer makes the kernel dependable.

It is responsible for:

- stable artifact schemas
- workspace validation rules
- report validation
- bundle validation
- deterministic output expectations

### 3. Operator Path

The operator path is how AVERA is actually used.

It is responsible for:

- runtime preflight
- supported command sequence
- repeatable demo/pilot execution
- artifact handoff flow

### 4. Review Surface

The review surface exists to read outputs, not to redefine them.

It is responsible for:

- shell navigation
- scenario presentation
- artifact readability
- review continuity during live demos or pilot walkthroughs

### 5. Release/Pilot Materials

The outer layer prepares AVERA for external use.

It is responsible for:

- one-pager
- case study
- design-partner packet
- design-partner playbook
- external demo flow
- pilot operating model

## Supported Runtime

The supported runtime path for the current stage is:

1. repository-local `.venv`
2. `scripts/runtime_doctor.py` as preflight
3. `./start_demo.sh` as the canonical demo/shell launcher
4. CLI execution as the source-of-truth path

Current runtime policy:

- the CLI is authoritative
- the shell is secondary and review-oriented
- static showcase assets are approved fallback continuity material

This is especially important because the current shell/runtime experience can be
affected by local Streamlit cold-start behavior even when the kernel itself is
healthy.

## Supported Inputs

The current supported input boundary is:

1. change description
2. baseline verification results
3. current verification results
4. requirements export
5. component mapping
6. optional signal trace

Current practical formats:

- structured JSON verification results
- CSV requirements export
- JSON component mapping
- plain-text change description
- CSV signal trace

This input boundary is curated and explicit. It is not yet a broad enterprise
ingestion layer.

## Supported Outputs

The current supported output boundary is:

1. assessment report
2. evidence graph
3. gate artifact
4. traceability index
5. decision artifact
6. trend artifact
7. workspace pack

These outputs define the current release-ready review package.

## Operator Sequence

The expected operator sequence today is:

1. run runtime preflight
2. validate the workspace
3. run analysis
4. build traceability
5. evaluate decision
6. build trend
7. build workspace pack
8. inspect outputs in shell or artifacts
9. hand off the portable bundle for review

Canonical command flow:

```bash
.venv/bin/python scripts/runtime_doctor.py
PYTHONPATH=src python3 -B -m avera validate-workspace <workspace>
PYTHONPATH=src python3 -B -m avera demo-refresh --project <workspace> ...
PYTHONPATH=src python3 -B -m avera validate-artifact --artifact workspace_pack --path <pack_json> --bundle
./start_demo.sh
```

If the shell is not cooperative during a live session, the operator may continue
with approved static continuity assets such as:

- `AVERA_ADAS_SHOWCASE.html`
- case study documents
- packet and playbook materials

## Release Readiness Tiers

The project should be evaluated through four readiness tiers.

### Tier 1. Kernel Ready

This means:

- fixtures pass
- test suite passes
- artifact generation is stable
- contracts validate

### Tier 2. Demo Ready

This means:

- launcher path is documented
- at least one live scenario is stable
- second-domain proof exists
- fallback assets exist
- operator script is documented

### Tier 3. Pilot Ready

This means:

- supported runtime is explicit
- supported inputs/outputs are explicit
- operator sequence is explicit
- first pilot workflow is explicit
- limitations are explicit
- release handoff artifacts are stable

### Tier 4. Broader Release Candidate

This means:

- shell is hardened for repeated use
- real artifact adapters are stronger
- domain matrix is wider
- pilot proof exists
- reproducibility is strong enough for outside teams

AVERA is currently strongest across Tier 1 through Tier 3, and is preparing for
Tier 4.

## What "Release" Means Right Now

For the current stage, "release" should not be interpreted as public mass
distribution.

It should mean:

- a stable local package for internal review
- a design-partner-ready demonstration boundary
- a narrow pilot candidate with documented operating rules

This is the correct release meaning for the current project stage.

## What Counts As Ready For External Showing

AVERA is ready for external showing when the following are true:

1. runtime preflight passes from the documented path
2. the test and fixture contour is green
3. one-command demo launch is documented
4. canonical BMS story is presentation-ready
5. ADAS second-domain proof is available through live or fallback form
6. operator script is documented
7. packet and playbook materials are current

## What Counts As Ready For Narrow Pilot Use

AVERA is ready for narrow pilot use when the following are true:

1. the supported runtime contract is stable
2. the supported input/output contract is stable
3. the workspace pack is sufficient for human review
4. the operator sequence is repeatable without hidden steps
5. known runtime quirks are documented up front
6. one team / one workflow / one artifact family scope is chosen
7. human decision responsibility remains explicit

## Release Checklist For The Current Stage

Before calling the current AVERA state release-ready for demo or pilot-facing
use, confirm:

- runtime doctor passes
- fixture matrix passes
- test suite passes
- artifact contract validation passes
- canonical demo path is documented
- fallback path is documented
- one-pager is current
- case study is current
- playbook is current
- pilot operating model is current

## Known Limits That Must Be Stated Honestly

The project should continue to state these limits clearly:

- local-first runtime, not hosted deployment
- curated artifact families, not broad enterprise ingestion
- review shell, not a mature application shell yet
- conservative evidence logic, not universal certainty
- human engineering decision remains the final release decision

## Next Implementation Sequence

The correct next implementation sequence after this document is:

1. shell hardening
2. real artifact adapters
3. domain matrix expansion
4. narrow pilot execution
5. broader release candidate packaging

That order protects the architecture from drifting into presentation-only work
or speculative platform work too early.

## Canonical Companion Documents

This document is the master release/readiness frame.

The main companion documents under it are:

- [AVERA_IMPLEMENTATION_STATUS.md](/Users/mac/Desktop/AVERA/docs/AVERA_IMPLEMENTATION_STATUS.md)
- [AVERA_RUNTIME_STABILIZATION.md](/Users/mac/Desktop/AVERA/docs/AVERA_RUNTIME_STABILIZATION.md)
- [AVERA_VERIFICATION_GUIDE.md](/Users/mac/Desktop/AVERA/docs/AVERA_VERIFICATION_GUIDE.md)
- [AVERA_PILOT_OPERATING_MODEL_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_OPERATING_MODEL_V0.md)
- [AVERA_DESIGN_PARTNER_PACKET.md](/Users/mac/Desktop/AVERA/docs/AVERA_DESIGN_PARTNER_PACKET.md)
- [AVERA_DESIGN_PARTNER_PLAYBOOK.md](/Users/mac/Desktop/AVERA/docs/AVERA_DESIGN_PARTNER_PLAYBOOK.md)
- [AVERA_EXTERNAL_DEMO_FLOW.md](/Users/mac/Desktop/AVERA/docs/AVERA_EXTERNAL_DEMO_FLOW.md)
- [AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md](/Users/mac/Desktop/AVERA/docs/AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md)

## One-Sentence Summary

AVERA is currently a locally runnable, evidence-first automotive change review
system with a supported operator path, stable review artifacts, and enough
readiness structure to support external showing and the first narrow pilot.
