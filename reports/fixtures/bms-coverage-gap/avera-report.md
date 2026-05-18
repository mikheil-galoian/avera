# AVERA Change Impact Report

## Verdict

- Verdict: `requirements_coverage_gap`
- Risk: `medium`
- Confidence: `low`
- Confidence score: `0.36`

## Affected Requirements

- `BMS-REQ-205` (component: BMS State Of Charge Estimation, metric: `soc_drift_pct`, safety: `medium`): State of charge estimate drift over a 30 minute drive cycle must not exceed 2 percent
- `BMS-REQ-206` (component: BMS State Of Charge Estimation, metric: `current_integration_error_pct`, safety: `medium`): Pack current integration error must not exceed 1.5 percent

## Affected Components

- BMS State Of Charge Estimation

## Affected Files

- src/bms/soc_estimator.c

## Introduced Failures

- None recorded.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- None recorded.

## Evidence Summary

- Verdict is requirements coverage gap.
- Mapped affected files: src/bms/soc_estimator.c.

## Rules Triggered

- R6_requirements_coverage_gap

## Confidence Factors

- + requirement_mapped
- + affected_file_mapped
- - no_metric_requirement_coverage

## Risk Drivers

- verdict:requirements_coverage_gap
- risk:medium
- safety_level:medium

## Signal Summary

- None recorded.

## Recommended Next Checks

- BMS-SIL-SOC-DRIFT-03
