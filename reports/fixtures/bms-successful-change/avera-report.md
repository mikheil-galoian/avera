# AVERA Change Impact Report

## Verdict

- Verdict: `successful_change`
- Risk: `low`
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

- None recorded.

## Threshold Evidence

- `BMS-REQ-112` / `max_cell_temp_c`: baseline `48.6` (pass), current `46.2` (pass), threshold `<= 50.0`.
- `BMS-REQ-118` / `cooling_response_ms`: baseline `455.0` (pass), current `390.0` (pass), threshold `<= 500.0`.

## Evidence Summary

- Verdict is successful change.
- Mapped affected files: src/bms/thermal_manager.c.

## Rules Triggered

- R7_successful_covered_change

## Confidence Factors

- + baseline_current_pair_present
- + requirement_mapped
- + affected_file_mapped

## Risk Drivers

- verdict:successful_change
- risk:low
- safety_level:high
- safety_level:medium
- threshold_passed:BMS-REQ-112:max_cell_temp_c
- threshold_passed:BMS-REQ-118:cooling_response_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- BMS-HIL-FASTCHARGE-07
