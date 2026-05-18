# AVERA Narrow Pilot Intake Checklist

**Date:** 2 May 2026  
**Purpose:** Standard intake checklist before scoping a first narrow AVERA pilot

## Goal

Use this checklist to decide whether a team is a good first pilot fit and how to scope the pilot without overcommitting.

## Team And Workflow

Capture:

- team name
- owner / point of contact
- role of contact
- repeated workflow being evaluated
- domain: BMS / ADAS / ECU / other

## Artifact Family

Choose one primary artifact family:

- simulation CSV
- requirements export variant CSV
- verification log CSV
- JUnit / xUnit XML
- another structured artifact family that can be inspected

## Minimum Required Inputs

Confirm they can provide:

1. change description
2. baseline evidence
3. current evidence
4. requirements or requirement linkage
5. component mapping or a usable substitute

## Review Boundary

Confirm:

- where raw artifacts originate
- where normalization should stop
- what the human reviewer expects to see
- what decision is actually being supported

## Pilot Shape

Keep the first pilot narrow:

- one team
- one domain
- one artifact family
- one repeated review path
- local-first execution
- human decision at the end

## Success Criteria

Define before starting:

1. what decision the pilot should support
2. what output must be trusted
3. what would count as a useful traceability chain
4. what would count as too much operator friction
5. what would justify a second pilot iteration

## Risks To Flag Early

Watch for:

- artifacts are too messy or too incomplete
- no stable baseline/current comparison exists
- no real human review step exists
- team expects broad platform rollout immediately
- team wants the system to replace engineering judgment

## Green-Light Conditions

Proceed only if:

1. one artifact family is clearly in scope
2. one repeated workflow is real and painful
3. one human decision point exists
4. the team accepts a narrow local-first pilot
5. the raw-to-normalized boundary can stay explicit

## Output Of Intake

At the end of intake, we should have:

1. named pilot owner
2. chosen artifact family
3. chosen workflow
4. agreed success criteria
5. follow-up session for sample artifact review
