# AVERA Design Partner Packet

**Date:** 29 April 2026  
**Status:** External-facing packet map for the current prototype  
**Audience:** Potential design partners, engineering leads, validation managers, systems teams

## Purpose

This document defines the current external-facing AVERA packet for early design
partner conversations.

The goal is not to overwhelm a prospective partner with architecture.

The goal is to make one thing easy:

show the current prototype in a believable order, with just enough supporting
material to prove that AVERA is real, portable, and worth discussing.

## Packet Structure

The packet should currently be presented in this sequence:

1. one-sentence product framing
2. one-pager
3. live demo path
4. BMS case study
5. ADAS second-domain proof
6. scaling and future direction

That order matters.

It moves from:

```text
what this is
  -> how to see it
  -> why it matters
  -> why it generalizes
  -> why it can grow
```

## 1. Product Framing

Use this first:

`AVERA is an evidence-first automotive engineering platform that proves what a change affected, what regressed, and what should happen before release.`

This framing should stay short. The conversation should move quickly into the
demo and case material.

## 2. One-Pager

Primary document:

- [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)

Use it to establish:

- category
- target users
- core problem
- differentiated value
- current product shape
- why now

If someone only reads one lightweight document before a meeting, it should be
the one-pager.

## 3. Live Demo Path

Primary launch path:

- [start_demo.sh](/Users/mac/Desktop/AVERA/start_demo.sh)

Primary shell:

- [demo/README.md](/Users/mac/Desktop/AVERA/demo/README.md)

The live demo should prove:

- the system starts quickly
- the shell is not a mockup
- evidence artifacts already exist
- the workflow is readable by an engineering audience

Recommended live sequence:

1. launch BMS by default
2. show report, evidence, traceability, and decision
3. switch to ADAS to prove cross-domain portability

## 4. BMS Case Study

Primary case-study document:

- [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)

Supporting scenario and narrative:

- [AVERA_DEMO_SCENARIO_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_DEMO_SCENARIO_BMS.md)
- [AVERA_DEMO_NARRATIVE_BMS_FAST_CHARGE.md](/Users/mac/Desktop/AVERA/docs/AVERA_DEMO_NARRATIVE_BMS_FAST_CHARGE.md)

This is the strongest current proof of value because it shows:

- a small-looking change
- a measurable regression
- requirement linkage
- a high-confidence blocking decision
- portable handoff artifacts

## 5. ADAS Second-Domain Proof

Primary second-domain reference:

- [AVERA_SECOND_DOMAIN_EXPANSION_NOTE.md](/Users/mac/Desktop/AVERA/docs/AVERA_SECOND_DOMAIN_EXPANSION_NOTE.md)
- [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)

Current working second domain:

```text
adas-pedestrian-detection-regression
```

Use it to prove:

- AVERA is not locked to BMS
- the proof model survives a domain change
- the launcher and shell can already point to a second domain path
- the external meeting can still show a clean ADAS proof artifact even if the local Streamlit runtime is slow to cold-start

The message should be:

`The domain changed, but the proof model did not.`

## 6. Scaling And Future Direction

Primary strategy documents:

- [AVERA_MARKET_POSITIONING.md](/Users/mac/Desktop/AVERA/docs/AVERA_MARKET_POSITIONING.md)
- [AVERA_SCALING_FRAMEWORK.md](/Users/mac/Desktop/AVERA/docs/AVERA_SCALING_FRAMEWORK.md)
- [AVERA_ROADMAP.md](/Users/mac/Desktop/AVERA/docs/AVERA_ROADMAP.md)

These should only come after the partner believes the current prototype is
useful.

At that point, use them to explain:

- where the current kernel is already solid
- how domain generality will grow
- why the long-term asset is the proof model and engineering memory layer

## What To Avoid

Do not lead with:

- broad architecture diagrams
- long-term SaaS ambitions
- compliance expansion first
- generic AI positioning

Do not force a partner to read the whole document tree before they understand
the product.

## Minimum Viable Packet

If time is short, the minimum viable external packet is:

1. [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)
2. [start_demo.sh](/Users/mac/Desktop/AVERA/start_demo.sh)
3. [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)
4. live ADAS scenario switch

That is enough for a real first design-partner conversation.

## Current Packet Readiness

As of 29 April 2026, the current packet already has:

- a launch path
- a working BMS scenario
- a working ADAS scenario
- a case study
- a one-pager
- market positioning
- a scaling framework

That means the current project no longer lacks materials.

The current work is about tightening consistency, reliability, and delivery.
