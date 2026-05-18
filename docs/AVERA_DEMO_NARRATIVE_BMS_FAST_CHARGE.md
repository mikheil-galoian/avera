# AVERA Canonical Demo Narrative: BMS Fast-Charge Scenario

**Date:** 28 April 2026  
**Status:** Canonical demo script  
**Audience:** Engineering leads, validation teams, systems teams, product and partner demos

## Purpose

This document is the canonical live presentation script for the AVERA BMS
fast-charge scenario.

It is designed to present one clear story:

```text
small engineering change -> evidence shift -> requirement impact -> traceable decision
```

The goal is not to dramatize the failure. The goal is to show that AVERA makes
the release decision inspectable, conservative, and backed by evidence.

## Demo Promise

At the end of this demo, the audience should believe three things:

- AVERA can show what changed.
- AVERA can prove why the change matters.
- AVERA can turn that proof into a reviewable release decision and handoff pack.

## Canonical Scenario

The scenario is a BMS fast-charge regression tied to battery thermal control.

An engineer modifies the cooling logic in:

```text
src/bms/thermal_manager.c
```

The change appears limited in code review, but fast-charge verification now
shows a thermal threshold breach.

Canonical requirement:

```text
ID: BMS-REQ-112
Requirement: Maximum cell temperature during fast charging must not exceed 50°C.
Metric: max_cell_temp_c
Threshold: <= 50.0
Safety relevance: high
Next verification: BMS-HIL-FASTCHARGE-07
```

Canonical comparison:

```text
Baseline max_cell_temp_c: 47.1
Current  max_cell_temp_c: 52.8
Delta: +5.7
```

Canonical verdict:

```text
confirmed_regression
```

## Presenter Framing

Open with a simple statement:

`This is a fast-charge BMS change that looked small in code, but the verification evidence says it is not small in effect. AVERA's job is to make that visible before release.`

Keep the framing disciplined:

- do not pitch AVERA as replacing engineers
- do not imply perfect root cause
- do not overclaim automation
- keep returning to evidence, traceability, and decision support

## Live Presentation Script

## 1. Setup

What to show:

- the scenario name
- the changed file
- the relevant requirement set
- the baseline and current verification inputs

What to say:

`We start with a real engineering review shape: a code change, a baseline run we trust, a current run after the change, and the requirement set that defines acceptable behavior.`

`In this scenario the changed file is thermal_manager.c, inside the BMS thermal control path. The requirement we care about is BMS-REQ-112: during fast charge, maximum cell temperature must stay at or below 50°C.`

`This is exactly the kind of situation where teams do not want intuition alone. They want proof that the change stayed inside the requirement envelope, or proof that it did not.`

Setup evidence to keep visible:

```text
Changed file: src/bms/thermal_manager.c
Requirement: BMS-REQ-112
Test: BMS-SIL-FASTCHARGE-01
Baseline status: passed
Current status: failed
```

Transition line:

`Now we move from change context to evidence.`

## 2. Evidence Reveal

What to show:

- baseline vs current metric comparison
- pass/fail shift
- the threshold line for maximum cell temperature
- any supporting response-timing signal if available

What to say:

`The first thing AVERA does is compare the current run against the trusted baseline, not against guesswork.`

`The baseline passes at 47.1°C. The current run fails at 52.8°C. That puts the current behavior 2.8°C over the requirement threshold and 5.7°C worse than baseline.`

`The important point here is that AVERA is not merely saying the test failed. It is showing the numeric reason the test failed and how far behavior moved.`

Suggested on-screen evidence block:

```text
Test: BMS-SIL-FASTCHARGE-01
Baseline: passed | max_cell_temp_c = 47.1 | cooling_response_ms = 420
Current:  failed | max_cell_temp_c = 52.8 | cooling_response_ms = 610
Requirement threshold: max_cell_temp_c <= 50.0
```

Optional emphasis line:

`Even before we discuss causality, we already know this change moved the system outside the thermal requirement envelope.`

Transition line:

`The next question is whether that evidence is traceable to the engineering change and the requirement set.`

## 3. Traceability Reveal

What to show:

- changed file to component mapping
- component to requirement mapping
- requirement to verification mapping
- one compact chain on screen

What to say:

`AVERA now turns a failing number into an auditable chain.`

`The changed file maps to BMS Thermal Control. That component maps to BMS-REQ-112. That requirement maps to the fast-charge verification scenario BMS-SIL-FASTCHARGE-01.`

`So the audience does not have to trust a black-box verdict. They can see the path from source change to affected component, from component to requirement, and from requirement to the verification evidence that regressed.`

Canonical traceability chain:

```text
src/bms/thermal_manager.c
  -> BMS Thermal Control
  -> BMS-REQ-112
  -> BMS-SIL-FASTCHARGE-01
  -> max_cell_temp_c breach
```

Short presenter line:

`This is where AVERA stops being just a test viewer and becomes a traceable engineering evidence system.`

Transition line:

`Once the evidence and traceability are established, AVERA can make a conservative decision recommendation.`

## 4. Decision Reveal

What to show:

- verdict
- risk
- confidence
- release recommendation
- next verification step

What to say:

`Because the regression is new relative to baseline, tied to a changed file in the affected component, and supported by a direct requirement breach, AVERA classifies this as a confirmed regression.`

`The risk is high because the violated requirement is thermal and safety-relevant. The confidence is high because the evidence chain is complete: baseline comparison, current failure, requirement threshold, and changed-file traceability are all present.`

`The release recommendation is to block until follow-up verification is complete. The next named verification step is BMS-HIL-FASTCHARGE-07.`

Canonical decision panel:

```text
Verdict: confirmed_regression
Risk: high
Confidence: high
Affected component: BMS Thermal Control
Affected requirement: BMS-REQ-112
Recommendation: block release and run BMS-HIL-FASTCHARGE-07
```

Important presenter line:

`Notice what AVERA is not claiming. It is not claiming universal root cause certainty. It is claiming that the change introduced a requirement-backed regression with enough evidence to justify a release-blocking action.`

Transition line:

`The final step is making that decision portable for review, audit, and cross-team handoff.`

## 5. Export Handoff

What to show:

- Markdown report
- JSON report
- artifact manifest or bundle contents
- source inputs included in the handoff

What to say:

`Once the decision is made, AVERA packages the reasoning so another engineer, a validation lead, or a release reviewer can inspect the same evidence without rerunning the entire conversation from memory.`

`The export should include the verdict, the metric deltas, the requirement link, the changed-file mapping, and the recommended next verification step.`

`This is important because the handoff artifact is not a slide claim. It is a structured review pack.`

Recommended export contents:

- Markdown summary report
- JSON structured report
- requirements snapshot
- component mapping snapshot
- baseline and current result references
- diff reference
- signal trace reference, if present

Suggested handoff line:

`What leaves this demo is not just a conclusion. It is the evidence package behind the conclusion.`

Transition line:

`That leads to the takeaway we want the audience to remember.`

## 6. Closing Takeaway

What to say:

`The point of AVERA is not to produce more alerts. The point is to produce reviewable proof.`

`In this scenario, a small BMS change created a fast-charge thermal regression. AVERA showed the baseline-to-current shift, tied it to the requirement, mapped it to the changed file, made a conservative release decision, and packaged the result for handoff.`

`That is the product promise in one sentence: proof-backed engineering decisions before release.`

## Presenter Notes

- Keep the demo under five minutes when possible.
- Spend the most time on evidence reveal and traceability reveal.
- Do not let the export view dominate the story.
- If challenged on causality, return to the conservative claim set.
- If challenged on scope, emphasize that this is the canonical narrow scenario.

## Canonical One-Line Summary

`A small cooling-logic change pushed fast-charge thermal behavior beyond requirement, and AVERA proved it clearly enough to block release with confidence.`

## Relationship To Other Demo Docs

- [AVERA_DEMO_SCENARIO_BMS.md](/Users/mac/Desktop/AVERA/docs/AVERA_DEMO_SCENARIO_BMS.md) defines the underlying BMS scenario and fixture shape.
- [AVERA_DEMO_SHELL.md](/Users/mac/Desktop/AVERA/docs/AVERA_DEMO_SHELL.md) defines the thin productized surface for showing the scenario.

This document is the canonical presenter script layered on top of those two
references.
