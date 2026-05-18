# AVERA Case Study: BMS Fast-Charge Regression

**Date:** 29 April 2026  
**Status:** Design-partner case study draft  
**Audience:** Engineering leads, validation teams, systems engineers, potential design partners

## Purpose

This document explains one concrete AVERA scenario from the point of view of an
engineering team reviewing a change before release.

The goal is simple:

show one believable case where AVERA turns a small-looking engineering change
into a clear, traceable, and reviewable release decision.

## The Situation

An engineer changed the BMS fast-charge cooling logic in:

```text
src/bms/thermal_manager.c
```

The intended change was modest:

- reduce unnecessary coolant pump activity during early fast charging
- preserve acceptable thermal behavior
- avoid overreacting to transient conditions

At code-review level, this kind of change can easily look contained.

The risk is that the code diff looks local while the behavioral effect is not.

## What Changed In Verification

AVERA compared the trusted baseline run against the current run after the
change.

### Baseline

```text
Test: BMS-SIL-FASTCHARGE-01
Status: passed
max_cell_temp_c: 47.1
cooling_response_ms: 420
```

### Current

```text
Test: BMS-SIL-FASTCHARGE-01
Status: failed
max_cell_temp_c: 52.8
cooling_response_ms: 610
```

### Requirement Thresholds

```text
BMS-REQ-112: max_cell_temp_c <= 50.0
BMS-REQ-118: cooling_response_ms <= 500.0
```

## What AVERA Found

AVERA classified the scenario as:

```text
Verdict: confirmed_regression
Risk: high
Confidence score: 0.95
```

Affected component:

```text
BMS Thermal Control
```

Affected file:

```text
src/bms/thermal_manager.c
```

Recommended next verification:

```text
BMS-HIL-FASTCHARGE-07
```

Release decision:

```text
Action: block
Category: containment_required
Owner: validation_and_component_owner
```

## Why AVERA Reached That Result

AVERA did not just see a failed test.

It built a proof chain:

```text
src/bms/thermal_manager.c
  -> BMS Thermal Control
  -> BMS-REQ-112 / BMS-REQ-118
  -> BMS-SIL-FASTCHARGE-01
  -> threshold breach and degraded response timing
```

The evidence was explicit:

- the baseline passed
- the current run failed
- the failure appeared only after the change
- the changed file mapped to the affected component
- the affected component mapped to the violated requirements
- both metrics worsened materially

From the generated report:

- `max_cell_temp_c` worsened from `47.1` to `52.8`
- `cooling_response_ms` worsened from `420` to `610`
- both values crossed their allowed requirement thresholds

This is why AVERA treated the result as a high-confidence confirmed regression
rather than as a noisy failure or weak suspicion.

## What Could Be Missed Without AVERA

Without AVERA, a team could still notice that the test failed.

But several things become easier to miss:

1. the failure is new relative to baseline, not just present in the current run
2. the changed file is directly connected to the affected requirement path
3. the regression is not only binary fail/pass, but numerically worse in two
   requirement-backed metrics
4. the decision is strong enough to justify a release block, not just a vague
   follow-up note

In other words:

without a traceable comparison layer, the team may still see the symptom, but
not the strength of the release decision.

## Why This Matters To An Engineering Team

This scenario is not interesting because it is dramatic.

It is interesting because it is normal.

Small control-logic changes happen constantly. Teams need to know:

- whether the behavior actually moved outside the requirement envelope
- whether the failure is new
- whether the release should pause
- what verification step should happen next
- how to hand the evidence to another reviewer without re-explaining everything

That is the role AVERA plays here.

## Handoff Value

The scenario does not end at the report.

AVERA also produces a portable workspace pack containing the run summary and
linked evidence artifacts.

Current pack status for the canonical scenario:

```text
artifact_count: 7
missing_artifacts: []
```

That means the result can be handed to:

- a validation lead
- a component owner
- a release manager
- a systems or safety reviewer

without losing the evidence chain.

## What This Case Study Proves

This case study is meant to show one narrow but important claim:

AVERA helps a team move from:

```text
small code change + failing test
```

to:

```text
traceable requirement impact + justified release decision + portable evidence handoff
```

That is the real value of the current prototype.

It is not abstract AI assistance.

It is disciplined engineering evidence.
