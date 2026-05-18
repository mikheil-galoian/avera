# AVERA Change Impact Report

## Verdict

- Verdict: `preexisting_failure`
- Risk: `medium`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `BMS-REQ-112` (component: BMS Thermal Control, metric: `max_cell_temp_c`, safety: `high`): Maximum cell temperature during fast charging must not exceed 50 C
- `BMS-REQ-118` (component: BMS Thermal Control, metric: `cooling_response_ms`, safety: `medium`): Cooling response delay during fast charging must not exceed 500 ms

## Affected Components

- BMS Thermal Control

## Affected Files

- src/bms/thermal_manager.c

## Introduced Failures

- None recorded.

## Preexisting Failures

- `BMS-SIL-FASTCHARGE-01`: baseline `failed`, current `failed`, component BMS Thermal Control.

## Threshold Evidence

- `BMS-REQ-112` / `max_cell_temp_c`: baseline `51.4` (fail), current `51.1` (fail), threshold `<= 50.0`.
- `BMS-REQ-118` / `cooling_response_ms`: baseline `535.0` (fail), current `528.0` (fail), threshold `<= 500.0`.

## Evidence Summary

- Verdict is preexisting failure.
- BMS-SIL-FASTCHARGE-01 failed in both baseline and current runs.
- max_cell_temp_c for BMS-REQ-112 was 51.1, outside <= 50.
- cooling_response_ms for BMS-REQ-118 was 528, outside <= 500.
- Mapped affected files: src/bms/thermal_manager.c.

## Rules Triggered

- R3_preexisting_failure
- signal_preexisting_failure_present

## Confidence Factors

- + baseline_current_pair_present
- + preexisting_failure_detected
- + requirement_mapped
- + affected_file_mapped

## Risk Drivers

- verdict:preexisting_failure
- risk:medium
- safety_level:high
- safety_level:medium
- threshold_failed:BMS-REQ-112:max_cell_temp_c
- threshold_failed:BMS-REQ-118:cooling_response_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- BMS-HIL-FASTCHARGE-07
