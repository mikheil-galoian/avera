# AVERA Pilot Safety Checklist

**Date:** 2 May 2026  
**Status:** Active guardrail document for first external pilots  
**Purpose:** Define the narrowest safe pilot shape for AVERA before any real external run

## What This Document Is

This is the working safety boundary for AVERA pilots.

It exists to prevent the first real pilot from turning into:

- a vague platform sale
- an oversized integration promise
- an uncontrolled data request
- a false expectation that AVERA directly validates a whole vehicle

This checklist should be used before any pilot is proposed, scoped, or started.

## Core Pilot Rule

The first AVERA pilot must stay:

- local-first
- narrow
- human-reviewed
- artifact-led
- reversible

If any proposed pilot no longer fits those five conditions, it is no longer a safe first pilot.

## Safe Pilot Shape

The default safe AVERA pilot is:

1. one team
2. one named owner
3. one repeated review workflow
4. one artifact family
5. one local review path
6. one human decision point
7. one feedback loop

Recommended first target:

- `Verification / Validation team`

Recommended first owner:

- `Validation Lead`

Recommended first artifact family:

- `verification log CSV`

Fallback first artifact family:

- `JUnit / xUnit XML`

## What AVERA Is Allowed To Claim

Safe claims:

- AVERA can normalize selected engineering artifacts into a stable review path
- AVERA can help connect change, evidence, traceability, and review output
- AVERA can support a human release or validation decision with clearer evidence
- AVERA can be tested first on one narrow workflow without changing the wider toolchain

## What AVERA Must Not Claim

Unsafe claims:

- AVERA validates the whole vehicle automatically
- AVERA replaces the engineering team
- AVERA replaces certification or compliance processes
- AVERA guarantees correctness of the vehicle or subsystem
- AVERA must integrate into every existing system before the pilot has value
- AVERA is already a broad enterprise rollout product

## Safe Pilot Offer Language

Use language like this:

`We are proposing one narrow local-first pilot around one artifact family your team already uses. The goal is to see whether AVERA makes one review workflow clearer and more trustworthy, not to replace your broader engineering or release process.`

Avoid language like this:

- full platform rollout
- full vehicle coverage
- automated safety approval
- universal integration
- broad deployment commitment

## Required Preconditions

Do not start a pilot unless all of these are true:

1. a real owner is named
2. one workflow is selected
3. one artifact family is selected
4. one sample export can be shared
5. the team accepts a narrow local-first evaluation
6. the final decision remains with a human reviewer

## Minimum Input Set

The minimum safe input set is:

1. change description
2. baseline evidence
3. current evidence
4. requirement linkage if available
5. component mapping or a workable substitute

Only request the smallest set needed for one review path.

Do not expand the request to unrelated systems, historical archives, or broad internal data access during the first pilot.

## Data Handling Rule

For the first pilot:

- request only one representative sample export
- prefer derived exports over direct system access
- avoid asking for broad repository or infrastructure access
- keep the pilot runnable from a local workspace
- treat all received artifacts as pilot-scoped only

The safe default is:

`sample export first, integration later if earned`

## Human-in-the-Loop Rule

The first pilot must preserve human review authority.

That means:

- AVERA may recommend
- AVERA may summarize
- AVERA may connect evidence
- AVERA may identify likely risk

But:

- the engineer decides
- the team decides
- the release owner decides

## Success Criteria

The first safe pilot is successful if it proves:

1. one real artifact can be normalized cleanly
2. the resulting review path is understandable
3. the traceability chain is useful
4. the owner says the output improves clarity or trust
5. the workflow can be discussed as a repeatable narrow use case

## Stop Conditions

Pause or stop the pilot if:

1. no real owner exists
2. the target workflow keeps expanding
3. more than one artifact family becomes mandatory before first proof
4. the team expects hosted deployment before first evaluation
5. the team expects AVERA to certify or approve outcomes automatically
6. data access demands become broader than the pilot needs
7. no human decision point can be identified

## Red Flags

Treat these as scope-risk signals:

- "Can you do this for the whole vehicle right away?"
- "Can you integrate with all our systems before we try it?"
- "Can you take responsibility for correctness?"
- "Can you cover several teams in the first pass?"
- "Can you also solve requirements, simulation, logs, dashboards, and release approval together?"

If these appear, narrow the pilot again before proceeding.

## Recommended Pilot Sequence

Use this order:

1. send the first-contact message
2. confirm a relevant owner
3. confirm one workflow
4. request one sample export
5. normalize the artifact locally
6. run one review path
7. gather structured feedback
8. decide whether a second pilot step is justified

## Safe Outcome Framing

At the end of the first pilot, the only required decision is:

- continue
- narrow further
- stop

The first pilot is not required to prove:

- full product-market fit
- full deployment readiness
- organization-wide rollout
- broad technical integration

## Companion Documents

Use this checklist with:

1. [AVERA_PILOT_EXECUTION_PREP_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_EXECUTION_PREP_V0.md)
2. [AVERA_REAL_PILOT_RUN_01.md](/Users/mac/Desktop/AVERA/docs/AVERA_REAL_PILOT_RUN_01.md)
3. [AVERA_PILOT_MOTION_LAUNCH_KIT_V0.md](/Users/mac/Desktop/AVERA/docs/AVERA_PILOT_MOTION_LAUNCH_KIT_V0.md)
4. [AVERA_SAMPLE_EXPORT_REQUEST_TEMPLATE.md](/Users/mac/Desktop/AVERA/docs/AVERA_SAMPLE_EXPORT_REQUEST_TEMPLATE.md)
5. [AVERA_NARROW_PILOT_INTAKE_CHECKLIST.md](/Users/mac/Desktop/AVERA/docs/AVERA_NARROW_PILOT_INTAKE_CHECKLIST.md)
