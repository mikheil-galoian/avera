# AVERA Start, Use, and Show Guide

**Date:** 30 April 2026  
**Status:** Practical operator guide  
**Purpose:** Give one real path to start AVERA, verify it, use it, and show it without digging through the whole document tree

## What This Guide Is

This guide is the practical answer to:

- how do I launch it?
- how do I check that it works?
- how do I use it as a real project artifact?
- how do I show it to another person?

If someone needs to actually run AVERA instead of only reading about it, this
is the guide to follow.

## What AVERA Already Is

AVERA is already a working local project with:

- a Python evidence kernel
- repeatable fixtures
- a green test suite
- a demo shell
- a BMS proof path
- an ADAS proof path
- a review/export package

That means this guide is not speculative.
It is for the project that already exists.

## One Real Start Path

Work from:

```bash
cd /Users/mac/Desktop/AVERA
```

Then use this order:

### 1. Check the runtime

```bash
.venv/bin/python scripts/runtime_doctor.py
```

What you want to see:

- project `.venv` is in use
- Streamlit is available
- ADAS static showcase is present
- runtime is acceptable for AVERA work

### 2. Check the fixtures

```bash
python3 -B scripts/run_all_fixtures.py
```

What you want to see:

```text
AVERA fixture matrix passed.
```

### 3. Check the full test suite

```bash
.venv/bin/python -m pytest -q tests
```

What you want to see:

- green test suite

### 4. Regenerate the canonical artifact chain

```bash
PYTHONPATH=src python3 -B -m avera demo-refresh \
  --project fixtures/bms-fast-charge \
  --report-out reports/fixtures/bms-fast-charge \
  --memory reports/avera-memory.jsonl \
  --traceability-out reports/avera-traceability-index.json \
  --decision-out reports/avera-decision.json \
  --trend-out reports/avera-trend-index.json \
  --pack-out reports/avera-workspace-pack.json
```

### 5. Validate the exported review bundle

```bash
PYTHONPATH=src python3 -B -m avera validate-artifact \
  --artifact workspace_pack \
  --path reports/avera-workspace-pack.json \
  --bundle
```

### 6. Open the demo shell

```bash
./start_demo.sh
```

## One Real Use Path

If you want to use AVERA like an engineering review tool, do this:

1. collect a supported workspace
2. validate it
3. run analysis
4. build the traceability/decision/trend chain
5. build the workspace pack
6. review the results in shell or artifacts
7. use the handoff readiness view before human release discussion

This is the first practical workflow:

`change review with baseline-vs-current evidence and human release triage`

In the shell itself, use this review order:

1. Overview for verdict, requirement impact, and release decision
2. Evidence for threshold deltas and confidence factors
3. Traceability for component / requirement / test focus
4. Workspace for pack summary and pilot-use handoff
5. Artifacts for raw JSON, CSV, and text inspection

## Supported Inputs Right Now

Current supported inputs:

- change description
- baseline results
- current results
- requirements export
- component map
- optional signal trace

Current artifact families:

- JSON verification results
- CSV requirements
- JSON component map
- text change description
- CSV signal trace
- adapted JUnit / xUnit XML via `adapt-junit`
- adapted simulation CSV via `adapt-simulation`
- adapted requirements export via `adapt-requirements`
- adapted verification log CSV via `adapt-logs`

Current realistic adapted sample workspace:

- `fixtures/adas-simulation-adapted`
- `fixtures/bms-requirements-adapted`
- `fixtures/bms-log-adapted`

## Supported Outputs Right Now

Current supported outputs:

- report
- evidence graph
- gate result
- traceability index
- decision artifact
- trend artifact
- workspace pack

These are the real outputs of the project as it exists today.

## One Real Show Path

If you need to show AVERA to another person, use this order:

### A. Start with the product frame

- [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)

### B. Show the main engineering story

- [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)

### C. Use the shell for the primary live path

```bash
./start_demo.sh
```

Inside the shell, show:

- scenario profile and operator note
- overview release decision
- traceability review navigation
- workspace handoff readiness

### D. Use ADAS as the cross-domain proof

Live path if the shell is cooperative:

```bash
DEMO_SCENARIO=adas-pedestrian-detection-regression ./start_demo.sh
```

Adapted-evidence path if you want to show the bridge from external artifacts
into a normal AVERA workspace:

```bash
DEMO_SCENARIO=adas-simulation-adapted ./start_demo.sh
```

Adapted requirements path if you want to show normalized upstream requirements
feeding the same review flow:

```bash
DEMO_SCENARIO=bms-requirements-adapted ./start_demo.sh
```

Adapted log path if you want to show richer verification logs normalized into
the same review flow:

```bash
DEMO_SCENARIO=bms-log-adapted ./start_demo.sh
```

Fallback path if the live ADAS shell is slow:

- [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)

### E. Use the external demo flow

- [AVERA_EXTERNAL_DEMO_FLOW.md](/Users/mac/Desktop/AVERA/docs/AVERA_EXTERNAL_DEMO_FLOW.md)
- [AVERA_ADAPTED_PILOT_BUNDLE.md](/Users/mac/Desktop/AVERA/docs/AVERA_ADAPTED_PILOT_BUNDLE.md)

## Project Sphere Of Use

Right now AVERA is suitable for:

- software change review
- regression triage
- requirement impact review
- evidence handoff
- release-readiness review

Best-fit early users:

- validation lead
- systems engineer
- release / quality owner
- embedded software manager
- verification tooling owner

## What This Project Is Not Yet

Not yet:

- hosted platform
- broad enterprise integration layer
- automatic compliance engine
- general-purpose AI engineering system

This is important.
The current project is strongest when used as a narrow, evidence-first review
tool.

## What Counts As “It Works”

For the current stage, AVERA works if:

1. runtime doctor passes
2. fixture matrix passes
3. test suite passes
4. demo-refresh rebuilds the artifact chain
5. workspace pack validates
6. shell or fallback assets make the result reviewable
7. the shell presents a usable review and handoff path without CLI-only explanation

That is the real acceptance definition of the current project.

## What To Read Next

If someone needs the deeper project logic after this guide:

- [AVERA_MASTER_RELEASE_FILE.md](/Users/mac/Desktop/AVERA/docs/AVERA_MASTER_RELEASE_FILE.md)
- [AVERA_RUNTIME_STABILIZATION.md](/Users/mac/Desktop/AVERA/docs/AVERA_RUNTIME_STABILIZATION.md)
- [AVERA_PILOT_OPERATING_MODEL_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_OPERATING_MODEL_V0.md)
- [AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md](/Users/mac/Desktop/AVERA/docs/AVERA_FULL_VERSION_PREPARATION_FRAMEWORK.md)

## Final Rule

Use this order:

1. start
2. verify
3. regenerate
4. validate
5. show
6. then decide the next engineering step
