# AVERA Change Impact Report

## Verdict

- Verdict: `environment_failure`
- Risk: `unknown`
- Confidence: `low`
- Confidence score: `0.45`

## Affected Requirements

- `BMS-REQ-112` (component: BMS Thermal Control, metric: `max_cell_temp_c`, safety: `high`): Maximum cell temperature during fast charging must not exceed 50 C
- `BMS-REQ-118` (component: BMS Thermal Control, metric: `cooling_response_ms`, safety: `medium`): Cooling response delay during fast charging must not exceed 500 ms

## Affected Components

- BMS Thermal Control

## Affected Files

- src/bms/thermal_manager.c

## Introduced Failures

- `BMS-HIL-FASTCHARGE-07`: baseline `passed`, current `error`, component BMS Thermal Control.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `BMS-REQ-112` / `max_cell_temp_c`: baseline `47.5` (pass), current `None` (unknown), threshold `<= 50.0`.
- `BMS-REQ-118` / `cooling_response_ms`: baseline `430.0` (pass), current `None` (unknown), threshold `<= 500.0`.

## Evidence Summary

- Verdict is environment failure.
- BMS-HIL-FASTCHARGE-07 failed only in the current run.
- Mapped affected files: src/bms/thermal_manager.c.
- BMS-HIL-FASTCHARGE-07 matched environment failure pattern: unavailable_runner.

## Rules Triggered

- R5_environment_failure
- signal_environment_failure_pattern
- signal_introduced_failure_present

## Confidence Factors

- + baseline_current_pair_present
- + introduced_failure_detected
- + requirement_mapped
- + affected_file_mapped
- + environment_failure_pattern_matched

## Risk Drivers

- verdict:environment_failure
- risk:unknown
- safety_level:high
- safety_level:medium

## Signal Summary

- None recorded.

## Recommended Next Checks

- BMS-HIL-FASTCHARGE-07
