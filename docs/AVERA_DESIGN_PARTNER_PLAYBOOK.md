# AVERA Design Partner Playbook

**Date:** 29 April 2026  
**Status:** First external conversation playbook  
**Audience:** AVERA operator, founder, engineering lead, or product lead preparing live partner demos

## Purpose

This document turns the current AVERA prototype into a repeatable external
conversation format.

It answers five practical questions:

1. what do we show?
2. who do we show it to?
3. what do we ask them?
4. what pilot do we offer if they are interested?
5. what do we do after the meeting?

## One-Sentence Framing

Open with:

`AVERA is an evidence-first automotive engineering platform that proves what a change affected, what regressed, and what should happen before release.`

Do not start with architecture diagrams or long-term platform ambition.

## Operator Preflight

Run this checklist before a real external showing:

1. confirm the `.venv` runtime is the one being used
2. run the canonical verification path from [AVERA_VERIFICATION_GUIDE.md](/Users/mac/Desktop/AVERA/docs/AVERA_VERIFICATION_GUIDE.md)
3. open the BMS shell path first
4. keep the ADAS switch command ready
5. keep the ADAS static fallback open:
   [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)
6. keep these documents already open in separate tabs:
   - [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)
   - [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)
   - [AVERA_EXTERNAL_DEMO_FLOW.md](/Users/mac/Desktop/AVERA/docs/AVERA_EXTERNAL_DEMO_FLOW.md)

The goal is simple: never spend the first two minutes of the meeting debugging
or searching for files.

## Demo Script

Recommended meeting length:

`10-15 minutes for the first pass`

## Operator Preflight

Before the meeting:

1. run the current runtime diagnostic path
2. confirm the canonical demo artifacts are present
3. launch the BMS shell path first
4. keep the ADAS showcase fallback already open or ready to open
5. keep the one-pager and case study available in parallel

Minimum preflight set:

- [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)
- [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)
- [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)
- `./start_demo.sh`
- `.venv/bin/python scripts/runtime_doctor.py`

### Part 1: Setup

Say:

`I want to show one narrow workflow that already works today: a change, the verification evidence around it, the traceability chain, and the release decision that follows from that evidence.`

Show:

- the launcher path
- the shell
- the fact that the scenario is local and reproducible

### Part 2: BMS Primary Story

Use:

- [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)
- [AVERA_DEMO_NARRATIVE_BMS_FAST_CHARGE.md](/Users/mac/Desktop/AVERA/docs/AVERA_DEMO_NARRATIVE_BMS_FAST_CHARGE.md)

Show:

- changed file
- baseline vs current
- requirement breach
- traceability
- decision
- workspace pack

Say:

`This is the part where AVERA turns a small-looking engineering change into a reviewable proof chain.`

### Part 3: ADAS Second-Domain Proof

Use the working second domain:

`adas-pedestrian-detection-regression`

Show:

- the shell switching domains
- the changed file and requirement path
- the same verdict discipline on a different engineering area

Say:

`The domain changed, but the proof model did not.`

### Part 4: Close The Demo

Say:

`The current prototype is not trying to solve your whole vehicle lifecycle. It is trying to make one engineering review workflow provable, portable, and reusable.`

## Demo Fallback Order

If the live shell path is slow or awkward, use this order:

1. keep the live BMS shell as the primary interactive path
2. keep the BMS case study as the narrative anchor
3. use [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html) as the approved second-domain fallback
4. continue the conversation without pretending the runtime quirk is a kernel problem

The fallback is not a downgrade in product truth.

It is a presentation continuity tool that preserves the real second-domain proof
without wasting the meeting on local runtime friction.

## Demo Fallback Order

If the live path becomes awkward during the meeting, fall back in this order:

1. stay in the BMS live shell
2. use the ADAS static showcase instead of waiting on a cold restart
3. continue the conversation with the case study and pilot questions

Do not burn meeting time proving the UI can reload. Protect the flow of the
conversation first.

## Audience Map

Best first design-partner roles:

- validation lead
- systems engineer
- release or quality lead
- embedded software manager
- verification tooling owner

What each role usually cares about:

- validation lead: failure triage, traceability, repeatable review
- systems engineer: requirement linkage, impact visibility, evidence completeness
- release/quality lead: decision confidence, handoff value, release blocking logic
- embedded software manager: change impact clarity, false-positive risk, team fit
- tooling owner: artifact shape, input availability, integration feasibility later

Less useful first audience:

- generic AI strategy stakeholders with no direct ownership of verification pain

## Feedback Questions

Ask after the demo:

1. does this resemble a real engineering review shape in your environment?
2. which parts of the evidence chain feel believable, and which feel incomplete?
3. what artifacts do you actually have today: requirements, test logs, JUnit, traces, simulation outputs?
4. is baseline vs current comparison useful in your current workflow?
5. where would you distrust this system first?
6. which domain is most relevant for you: BMS, ADAS, ECU, or something else?
7. what output would be most valuable: report, traceability view, release decision, or portable pack?
8. what would have to be true for you to try a narrow pilot?

## Pilot Scope

Offer a narrow pilot, not a platform promise.

Recommended first pilot shape:

- one team
- one domain
- one artifact family
- one repeated workflow
- local-first execution
- manual review around the output

Suggested pilot examples:

- one regression review path for BMS
- one ADAS verification path for pedestrian detection
- one release-readiness checkpoint around baseline/current evidence

What not to promise yet:

- hosted SaaS
- full enterprise rollout
- full vehicle lifecycle coverage
- automatic compliance
- broad connector coverage on day one

## Follow-Up Structure

If the first conversation goes well, follow this sequence:

### 1. Same-Day Note

Send:

- one-sentence summary of what they cared about
- the one-pager
- the case study
- a short recap of which domain seemed most relevant

### 2. Internal Capture

Record:

- their role
- their domain
- their current artifacts
- their strongest pain point
- what they trusted
- what they did not trust
- what pilot boundary felt realistic

### 3. Second Meeting

Use the second meeting to narrow:

- target workflow
- available artifacts
- what counts as success
- what not to do in the pilot

### 4. Pilot Proposal

Only after the second meeting, propose:

- pilot scope
- pilot inputs
- pilot outputs
- success criteria
- duration

## Minimum Meeting Kit

For a real first design-partner conversation, the minimum viable kit is:

1. [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)
2. [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)
3. [AVERA_DESIGN_PARTNER_PACKET.md](/Users/mac/Desktop/AVERA/docs/AVERA_DESIGN_PARTNER_PACKET.md)
4. [AVERA_SECOND_DOMAIN_EXPANSION_NOTE.md](/Users/mac/Desktop/AVERA/docs/AVERA_SECOND_DOMAIN_EXPANSION_NOTE.md)
5. `./start_demo.sh`
6. the ADAS scenario switch

## What Success Looks Like

A successful first design-partner conversation does not need to end with a sale.

It should end with three concrete things:

- a clear statement of whether the workflow matches a real pain
- a concrete list of artifacts they could provide in a pilot
- a realistic next meeting or pilot boundary

That is enough to move AVERA from prototype demonstration to actual market
learning.
