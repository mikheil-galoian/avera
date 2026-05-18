# AVERA External Demo Flow

**Date:** 29 April 2026  
**Audience:** First design-partner conversation  
**Format:** 10-12 minute live walkthrough

## Goal

Show one narrow workflow that already works today and prove two things:

1. AVERA turns a change into a reviewable evidence chain.
2. The evidence model survives a domain change from BMS to ADAS.

## Operator Setup

Before the meeting:

1. run the fixture matrix
2. run the canonical `demo-refresh`
3. validate the workspace pack contract
4. launch `./start_demo.sh`
5. keep the ADAS switch ready:

```bash
DEMO_SCENARIO=adas-pedestrian-detection-regression ./start_demo.sh
```

Keep these documents open:

- [AVERA_ONE_PAGER.md](/Users/mac/Desktop/AVERA/docs/AVERA_ONE_PAGER.md)
- [AVERA_CASE_STUDY_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_CASE_STUDY_BMS.md)
- [AVERA_DESIGN_PARTNER_PLAYBOOK.md](/Users/mac/Desktop/AVERA/docs/AVERA_DESIGN_PARTNER_PLAYBOOK.md)
- [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)
- [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)

If the ADAS live shell is slow to cold-start, switch to the static ADAS
showcase and keep the meeting moving. Treat that as an approved presentation
fallback, not as a failed demo.

## Minute-by-Minute Flow

### 0:00-1:00 - Frame The Problem

Say:

`AVERA is an evidence-first engineering review layer. It shows what changed, what failed, what requirements are affected, and what should happen before release.`

Do not open with architecture or roadmap.

## 1:00-5:00 - BMS Primary Story

Use the canonical BMS fast-charge scenario.

Show in the shell:

- scenario name
- verdict
- risk
- confidence
- decision
- requirement impact

Then show:

- Evidence tab
- threshold breach
- baseline vs current
- signal trace

Then show:

- Traceability tab
- component -> requirement -> test/failure chain
- owner routing

Then show:

- Workspace tab
- workspace pack summary

Say:

`This is the point where a small engineering change becomes a portable proof chain instead of a hand-waved triage story.`

## 5:00-7:00 - ADAS Second-Domain Proof

Switch to:

`adas-pedestrian-detection-regression`

Show:

- same shell
- same evidence structure
- different domain
- changed file
- affected requirements
- same verdict discipline

If the live ADAS shell path is slow on cold-start, use:

- [AVERA_ADAS_SHOWCASE.html](/Users/mac/Desktop/AVERA/docs/AVERA_ADAS_SHOWCASE.html)

That is an approved fallback, not a workaround to hide product weakness.
It is a clean presentation path derived from the same verified ADAS artifacts.

Say:

`The domain changed, but the proof model did not.`

## 7:00-8:30 - Adapted Evidence Extension

If the conversation shifts from demo to pilot realism, extend with:

- `adas-simulation-adapted`
- `bms-requirements-adapted`

Say:

`These paths show the same review engine working on normalized external artifacts, not only on hand-authored local fixture inputs.`

## 8:30-10:00 - Why This Matters

Tie the product back to a real engineering workflow:

- release review
- failure triage
- requirement impact review
- evidence handoff between teams

Say:

`The current prototype is intentionally narrow. It is not trying to replace engineering judgment. It is trying to make one review workflow provable and repeatable.`

## 10:00-12:00 - Feedback And Pilot Close

Ask:

1. does this resemble a real review path in your team?
2. which artifacts do you already have in practice?
3. where would you distrust the output first?
4. which domain would be the best first pilot for you?
5. what would have to be true for a narrow pilot to be worthwhile?

Close with:

`If this is relevant, the next step is not a platform rollout. The next step is one narrow pilot around one workflow and one artifact family.`

## Non-Negotiables During The Demo

- stay inside one working workflow
- do not promise hosted SaaS
- do not promise full lifecycle coverage
- do not overclaim automation
- keep the conversation anchored in evidence, traceability, and release decisions
- prefer a smooth proof narrative over fighting a runtime quirk live

## Success Criteria

The meeting is successful if it produces:

- one real pain point
- one realistic artifact set
- one candidate pilot boundary
- one clear follow-up conversation
