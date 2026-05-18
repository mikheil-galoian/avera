# AVERA Change Impact Report

## Verdict

- Verdict: `successful_change`
- Risk: `low`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `PT-REQ-030` (component: Emissions Management System, metric: `nox_mg_per_km`, safety: `low`): NOₓ emissions must not exceed 60 mg/km (Euro 6d type-approval limit).
- `PT-REQ-031` (component: Emissions Management System, metric: `co2_g_per_km`, safety: `low`): Fleet-average CO₂ emissions must not exceed 95 g/km (EU fleet CO₂ regulation target).

## Affected Components

- Emissions Management System

## Affected Files

- src/ems/emissions_monitor.c

## Introduced Failures

- None recorded.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `PT-REQ-030` / `nox_mg_per_km`: baseline `54.0` (pass), current `49.0` (pass), threshold `<= 60.0`.
- `PT-REQ-031` / `co2_g_per_km`: baseline `91.0` (pass), current `88.0` (pass), threshold `<= 95.0`.

## Evidence Summary

- Verdict is successful change.
- Mapped affected files: src/ems/emissions_monitor.c.

## Rules Triggered

- R7_successful_covered_change

## Confidence Factors

- + baseline_current_pair_present
- + requirement_mapped
- + affected_file_mapped

## Risk Drivers

- verdict:successful_change
- risk:low
- safety_level:low
- threshold_passed:PT-REQ-030:nox_mg_per_km
- threshold_passed:PT-REQ-031:co2_g_per_km

## Signal Summary

- None recorded.

## Recommended Next Checks

- PT-EMS-NOX-01
