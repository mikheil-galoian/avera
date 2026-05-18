# AVERA Second-Domain Expansion Note

**Date:** 29 April 2026  
**Status:** Working second-domain note

## Purpose

This note defines what the first non-BMS fixture should mean for AVERA's product
story.

The second-domain milestone is not mainly about adding one more scenario.
It is about proving that AVERA is a reusable automotive evidence platform, not a
single-domain BMS demo with polished packaging.

## Current Working Second Domain

The working second domain is:

`ADAS pedestrian detection regression`

Why this matters now:

- it is already implemented in the fixture contract AVERA uses today
- it proves the current kernel is not BMS-only
- it is understandable even outside narrow BMS teams
- it shows the same proof model operating on a very different automotive
  component area

ECU control logic remains a strong future candidate for an additional domain,
but it is no longer the immediate second-domain recommendation because ADAS is
already working in the live prototype.

## Why The New Domain Matters

The new domain matters for platform positioning because it lets AVERA say
something stronger than "we can explain one BMS regression."

With the ADAS fixture in place, the product story becomes:

- AVERA preserves one evidence model across multiple automotive software domains
- the proof chain is portable even when the component, requirement set, and test
  semantics change
- the product category is an automotive engineering evidence platform, not a BMS
  point solution

That shift matters in demos, partner conversations, and future roadmap framing.
It shows that the durable asset is the evidence architecture:

`change -> requirement -> verification result -> failure evidence -> risk -> decision`

## What The Demo Should Show

The second-domain demo should prove continuity, not novelty for its own sake.

It should show:

1. the same AVERA workflow operating on a non-BMS fixture
2. a changed file or module mapped to a different engineering component area
3. requirement linkage that is specific to the new domain
4. a measurable verification delta with auditable artifacts
5. the same conservative verdict, confidence, and gate behavior seen in the BMS
   path
6. the shell and exported artifacts remaining understandable without domain
   reinvention

For the current ADAS fixture, the simplest believable story is:

- a pedestrian classifier threshold retune is introduced
- the baseline run passes
- the current run loses pedestrian recall and delays braking activation
- the changed artifact maps to ADAS Pedestrian Detection
- requirement-linked metrics are implicated
- AVERA produces a proof-backed confirmed regression verdict and next
  verification step

## Demo Message

The audience should leave with two conclusions:

- AVERA is not locked to battery evidence
- AVERA keeps the same proof discipline when it crosses into a second domain

The live presenter should be able to say, in effect:

`The domain changed, but the proof model did not.`

## Boundary

This milestone should not trigger a broad UI rewrite, a new architecture layer,
or claims that AVERA already covers the full vehicle lifecycle.

The goal is narrower:

- prove transferability of the kernel with a working ADAS scenario
- strengthen platform positioning
- keep the demo story conservative and inspectable
