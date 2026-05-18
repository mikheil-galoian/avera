# AVERA Validation Plan

**Date:** 21 April 2026  
**Status:** Draft

## Goal

Prove that AVERA can connect an automotive-style engineering change to requirements, verification evidence, and risk without inventing conclusions.

## Validation Principle

AVERA should only produce strong conclusions when supported by measurable evidence.

Required evidence for high-confidence regression:

- baseline passed or stayed below threshold
- current failed or exceeded threshold
- affected requirement can be identified
- changed file or component maps to the affected requirement
- result can be reproduced from fixture artifacts

## First Fixture Set

Use:

```text
BMS Thermal Regression Scenario
```

Fixture should include:

- `requirements.csv`
- `baseline_results.json`
- `current_results.json`
- `component_map.json`
- optional `signal_trace.csv`
- optional `thermal_manager.diff`

## Scenario A: Successful Change

Baseline:

- test passes
- metric below threshold

Current:

- test passes
- metric still below threshold

Expected:

- `successful_change`
- low or no release risk
- no introduced failure

## Scenario B: Confirmed BMS Regression

Baseline:

- `max_cell_temp_c = 47.1`
- threshold `<= 50.0`
- test passes

Current:

- `max_cell_temp_c = 52.8`
- threshold `<= 50.0`
- test fails

Mapping:

- changed file maps to BMS Thermal Control
- BMS Thermal Control maps to `BMS-REQ-112`

Expected:

- `confirmed_regression`
- `high` confidence
- `high` or `safety_critical` risk
- recommendation to block release and run HIL scenario

## Scenario C: Preexisting Failure

Baseline:

- test already fails
- metric already exceeds threshold

Current:

- same test still fails
- no meaningful worsening

Expected:

- `preexisting_failure`
- no new regression
- report still surfaces risk, but does not blame the current change

## Scenario D: Worsened Existing Failure

Baseline:

- test fails
- metric exceeds threshold slightly

Current:

- same test fails
- metric worsens materially

Expected:

- `possible_regression` or `confirmed_regression` depending on mapping strength
- evidence should show worsening delta

## Scenario E: Environment Failure

Baseline:

- evidence unavailable because command timed out or artifact missing

Current:

- failure is caused by missing artifact, timeout, corrupt log, or unavailable test runner

Expected:

- `environment_failure` or `insufficient_evidence`
- no safety claim

## Scenario F: Requirement Coverage Gap

Baseline/current:

- change touches a mapped component
- no test or simulation evidence exists for affected requirement

Expected:

- `requirements_coverage_gap`
- medium risk
- recommendation to add or run relevant verification

## Metrics

Track:

- correct classification on controlled fixtures
- false positive rate
- false negative rate
- report explainability
- number of evidence links per conclusion
- whether a human reviewer trusts the report

## Initial Quality Targets

- `90%+` correct classification on controlled fixtures
- `0` high-confidence claims without baseline/current evidence
- each high-risk conclusion must cite at least one requirement and one verification artifact

## Human Review

Before presenting AVERA externally:

- review every fixture report manually
- verify that evidence supports the stated risk
- ensure terminology does not imply certification or automatic safety approval
- ensure AVERA distinguishes confirmed issues from possible or insufficient evidence
