# AVERA Change Impact Report

## Verdict

- Verdict: `worsened_preexisting_failure`
- Risk: `high`
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

- `BMS-REQ-112` / `max_cell_temp_c`: baseline `51.2` (fail), current `56.9` (fail), threshold `<= 50.0`.
- `BMS-REQ-118` / `cooling_response_ms`: baseline `520.0` (fail), current `675.0` (fail), threshold `<= 500.0`.

## Evidence Summary

- Verdict is worsened preexisting failure.
- BMS-SIL-FASTCHARGE-01 failed in both baseline and current runs.
- max_cell_temp_c for BMS-REQ-112 was 56.9, outside <= 50.
- cooling_response_ms for BMS-REQ-118 was 675, outside <= 500.
- Mapped affected files: src/bms/thermal_manager.c.
- cooling_response_ms materially worsened from 520.0 to 675.0.
- max_cell_temp_c materially worsened from 51.2 to 56.9.

## Rules Triggered

- R4_worsened_preexisting_failure
- signal_material_metric_worsening
- signal_preexisting_failure_present

## Confidence Factors

- + baseline_current_pair_present
- + preexisting_failure_detected
- + requirement_mapped
- + affected_file_mapped

## Risk Drivers

- verdict:worsened_preexisting_failure
- risk:high
- safety_level:high
- safety_level:medium
- threshold_failed:BMS-REQ-112:max_cell_temp_c
- threshold_failed:BMS-REQ-118:cooling_response_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- BMS-HIL-FASTCHARGE-07
