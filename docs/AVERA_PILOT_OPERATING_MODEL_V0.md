# AVERA Pilot Operating Model v0

**Date:** 30 April 2026  
**Status:** Initial pilot-use operating model  
**Purpose:** Define how AVERA should be used in its first narrow real-world pilot workflow

## Why This Document Exists

AVERA is no longer only a concept, demo narrative, or internal prototype.

The kernel is already strong enough to support a first narrow pilot path.

That means the project now needs an operating model that answers practical
questions:

- what inputs are supported?
- what outputs are supported?
- what runtime path is supported?
- what is the operator sequence?
- what exactly is the first pilot workflow?
- what limitations must be stated up front?

This document defines that first operating boundary.

## Pilot Boundary

The first AVERA pilot should be:

- local-first
- operator-driven
- evidence-first
- review-oriented
- narrow in scope

It should not yet be:

- a hosted platform rollout
- an always-on enterprise integration
- a general AI assistant
- a compliance automation product

## Supported Inputs v0

The first pilot should accept:

1. change description
2. baseline verification results
3. current verification results
4. requirements export
5. component mapping
6. optional signal trace

Current practical artifact families:

- structured JSON verification results
- CSV requirements export
- JSON component map
- plain-text change description
- CSV signal trace

## Supported Outputs v0

The first pilot should produce:

1. assessment report
2. evidence graph
3. gate result
4. traceability index
5. decision artifact
6. trend artifact
7. workspace pack

Those outputs are the first stable review package.

## Supported Runtime v0

The supported runtime path for the first pilot is:

1. repository `.venv`
2. `scripts/runtime_doctor.py`
3. `./start_demo.sh` for demo/shell work
4. CLI commands for source-of-truth execution

Current runtime rule:

- the CLI remains the truth boundary
- the shell remains a thin review surface
- the static ADAS showcase is an approved continuity fallback during external review

## Operator Sequence v0

The operator path for a first pilot should be:

1. run runtime preflight
2. validate the workspace
3. run analysis
4. build traceability
5. evaluate decision
6. build trend
7. build workspace pack
8. review outputs in shell or artifacts
9. hand off the portable bundle for human review

Recommended command sequence:

```bash
.venv/bin/python scripts/runtime_doctor.py
PYTHONPATH=src python3 -B -m avera validate-workspace <workspace>
PYTHONPATH=src python3 -B -m avera analyze --project <workspace> --out <report_dir>
PYTHONPATH=src python3 -B -m avera traceability --report <report_json> --memory <memory_jsonl> --out <traceability_json>
PYTHONPATH=src python3 -B -m avera decision --report <report_json> --gate <gate_json_or_status> --traceability <traceability_json> --out <decision_json>
PYTHONPATH=src python3 -B -m avera trend --memory <memory_jsonl> --traceability <traceability_json> --out <trend_json>
PYTHONPATH=src python3 -B -m avera pack --workspace <workspace> --report <report_json> --graph <graph_json> --memory <memory_jsonl> --traceability <traceability_json> --decision <decision_json> --trend <trend_json> --out <pack_json>
```

## First Pilot Workflow

The first recommended pilot workflow is:

`change review with baseline-vs-current evidence and human release triage`

That workflow should look like this:

1. a team has a known engineering change
2. baseline and current verification results are available
3. AVERA compares them
4. AVERA maps affected files, requirements, tests, and failures
5. AVERA emits a conservative verdict
6. a human reviewer uses the decision, traceability, and pack artifacts to decide what happens next

## Recommended Pilot Scope

Keep the first pilot deliberately narrow:

- one team
- one domain
- one artifact family
- one repeated review path
- local operator execution
- human decision at the end

Examples:

- BMS regression review path
- ADAS pedestrian detection review path
- release-readiness checkpoint for one embedded subsystem

## Readiness Gate Before Pilot Start

The first pilot should not begin until all of these are true:

1. runtime preflight passes from the documented path
2. canonical verification commands run cleanly
3. artifact contract validation is green
4. at least one domain story is stable in live shell review
5. at least one second-domain proof is available through live or fallback presentation
6. known runtime quirks are documented
7. operator sequence is documented end-to-end

## Review Surface Policy

For the first pilot:

- the shell is used for reading and presenting outputs
- the CLI is used for generating outputs
- static showcase assets are acceptable as continuity material

This keeps the product architecture honest:

- generation in the kernel
- navigation in the shell
- fallback in presentation assets

## Known Limitations v0

The first pilot should explicitly admit:

- runtime is local-first, not hosted
- artifact adapters are still limited
- input formats are still curated, not broad enterprise ingestion
- shell is a review layer, not yet a mature application
- final engineering and release decisions remain human decisions

## What Counts As Pilot Success

A first pilot is successful if it proves:

1. the workflow matches a real engineering pain
2. the supported artifacts are realistic enough to be useful
3. the proof chain is trusted more than ad hoc triage alone
4. the human reviewer can act on the output
5. the next pilot iteration has a clear scope

## What Comes After This

Once this operating model is stable, the next layers are:

1. shell hardening
2. realistic artifact adapters
3. wider domain matrix
4. stronger pilot package
5. broader external use
