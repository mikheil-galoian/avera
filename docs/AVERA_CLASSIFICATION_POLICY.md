# AVERA Classification Policy

**Date:** 22 April 2026  
**Status:** Draft policy v0

## Purpose

This policy defines how AVERA should classify engineering outcomes.

AVERA must be conservative. Weak evidence should not produce strong claims.

## Verdicts

### confirmed_regression

Use when:

- baseline passed
- current failed
- or baseline threshold passed and current threshold failed
- requirement evidence is mapped

### possible_regression

Use when:

- current evidence suggests a problem
- but baseline, requirement mapping, or threshold evidence is incomplete

### preexisting_failure

Use when:

- baseline failed
- current failed
- and there is no material worsening

### worsened_preexisting_failure

Future verdict.

Use when:

- baseline already failed
- current failed
- and current metrics materially worsened

### environment_failure

Future verdict.

Use when:

- failure appears caused by timeout, corrupt artifact, missing runner, missing log, unavailable tool, or setup issue

### insufficient_evidence

Use when:

- AVERA cannot prove a stronger conclusion

### requirements_coverage_gap

Future verdict.

Use when:

- a requirement or component is affected
- but no relevant verification evidence exists

### successful_change

Future verdict.

Use when:

- baseline and current pass
- thresholds remain satisfied
- affected requirements have coverage

Current v0 behavior may use `expected_change` for this case.

## Risk Levels

- `low`: no evidence of regression or only non-critical residual issues
- `medium`: possible issue, preexisting issue, coverage gap, or missing evidence in relevant area
- `high`: confirmed regression on a high-relevance requirement
- `safety_critical`: confirmed or strongly suspected issue affecting safety-critical requirements
- `release_blocking`: confirmed issue that should block release until reviewed

## Confidence Labels

- `low`: missing baseline/current pair, missing mapping, or weak evidence
- `medium`: meaningful evidence exists but not enough for strong attribution
- `high`: baseline/current pair + requirement mapping + threshold or test failure evidence

## High Confidence Rule

High confidence requires:

- baseline/current evidence
- changed or affected component mapping
- requirement mapping
- verification or metric evidence

## Non-Claims

AVERA does not claim:

- automatic safety certification
- complete root-cause proof
- replacement of engineering review
- regulatory approval

AVERA claims:

- evidence organization
- conservative classification
- traceable risk reporting
