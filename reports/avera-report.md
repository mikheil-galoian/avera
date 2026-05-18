# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `high`
- Confidence: `high`

## Affected Requirements

- `BMS-REQ-112` (component: BMS Thermal Control, metric: `max_cell_temp_c`, safety: `high`): Maximum cell temperature during fast charging must not exceed 50 C
- `BMS-REQ-118` (component: BMS Thermal Control, metric: `cooling_response_ms`, safety: `medium`): Cooling response delay during fast charging must not exceed 500 ms

## Affected Components

- BMS Thermal Control

## Affected Files

- src/bms/thermal_manager.c

## Introduced Failures

- `BMS-SIL-FASTCHARGE-01`: baseline `passed`, current `failed`, component BMS Thermal Control.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `BMS-REQ-112` / `max_cell_temp_c`: baseline `47.1` (pass), current `52.8` (fail), threshold `<= 50.0`.
- `BMS-REQ-118` / `cooling_response_ms`: baseline `420.0` (pass), current `610.0` (fail), threshold `<= 500.0`.

## Evidence Summary

- Verdict is confirmed regression.
- BMS-SIL-FASTCHARGE-01 failed only in the current run.
- max_cell_temp_c for BMS-REQ-112 was 52.8, outside <= 50.
- cooling_response_ms for BMS-REQ-118 was 610, outside <= 500.
- Mapped affected files: src/bms/thermal_manager.c.

## Recommended Next Checks

- BMS-HIL-FASTCHARGE-07
