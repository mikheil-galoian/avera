# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `high`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `BMS-REQ-112` (component: BMS Thermal Control, metric: `max_cell_temp_c`, safety: `high`): Maximum cell temperature during fast charging must not exceed 50 C
- `BMS-REQ-118` (component: BMS Thermal Control, metric: `cooling_response_ms`, safety: `medium`): Cooling response delay during fast charging must not exceed 500 ms
- `BMS-REQ-205` (component: BMS Cell Balancing, metric: `cell_delta_mv`, safety: `medium`): Cell voltage imbalance after balancing must not exceed 35 mV
- `BMS-REQ-301` (component: BMS Contactor Control, metric: `contactor_close_ms`, safety: `low`): Main contactor close time must not exceed 120 ms

## Affected Components

- BMS Cell Balancing
- BMS Contactor Control
- BMS Thermal Control

## Affected Files

- src/bms/cell_balancer.c
- src/bms/contactor_control.c
- src/bms/thermal_manager.c

## Introduced Failures

- `BMS-SIL-FASTCHARGE-01`: baseline `passed`, current `failed`, component BMS Thermal Control.

## Preexisting Failures

- `BMS-SIL-BALANCE-02`: baseline `failed`, current `failed`, component BMS Cell Balancing.

## Threshold Evidence

- `BMS-REQ-205` / `cell_delta_mv`: baseline `42.0` (fail), current `41.0` (fail), threshold `<= 35.0`.
- `BMS-REQ-301` / `contactor_close_ms`: baseline `94.0` (pass), current `92.0` (pass), threshold `<= 120.0`.
- `BMS-REQ-112` / `max_cell_temp_c`: baseline `47.3` (pass), current `53.4` (fail), threshold `<= 50.0`.
- `BMS-REQ-118` / `cooling_response_ms`: baseline `430.0` (pass), current `640.0` (fail), threshold `<= 500.0`.

## Evidence Summary

- Verdict is confirmed regression.
- BMS-SIL-FASTCHARGE-01 failed only in the current run.
- BMS-SIL-BALANCE-02 failed in both baseline and current runs.
- cell_delta_mv for BMS-REQ-205 was 41, outside <= 35.
- max_cell_temp_c for BMS-REQ-112 was 53.4, outside <= 50.
- cooling_response_ms for BMS-REQ-118 was 640, outside <= 500.
- Mapped affected files: src/bms/cell_balancer.c, src/bms/contactor_control.c, src/bms/thermal_manager.c.

## Rules Triggered

- R1_confirmed_threshold_regression
- R2_introduced_test_failure
- signal_baseline_pass_current_threshold_fail
- signal_introduced_failure_present
- signal_preexisting_failure_present

## Confidence Factors

- + baseline_current_pair_present
- + introduced_failure_detected
- + preexisting_failure_detected
- + threshold_crossing_detected
- + requirement_mapped
- + affected_file_mapped

## Risk Drivers

- verdict:confirmed_regression
- risk:high
- safety_level:high
- safety_level:low
- safety_level:medium
- threshold_failed:BMS-REQ-205:cell_delta_mv
- threshold_passed:BMS-REQ-301:contactor_close_ms
- threshold_failed:BMS-REQ-112:max_cell_temp_c
- threshold_failed:BMS-REQ-118:cooling_response_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- BMS-HIL-FASTCHARGE-07
- BMS-SIL-BALANCE-02
- BMS-SIL-CONTACTOR-01
