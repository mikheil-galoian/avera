# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `release_blocking`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `FADEC-REQ-001` (component: Full Authority Digital Engine Control, metric: `overspeed_response_ms`, safety: `dal-a`): Engine overspeed protection must activate within 50 ms when N1 exceeds 105% of rated speed.
- `FADEC-REQ-002` (component: Full Authority Digital Engine Control, metric: `fuel_flow_error_pct`, safety: `dal-b`): Fuel flow computation error shall not exceed 0.5% of full-scale flow at any operating point.
- `FADEC-REQ-003` (component: Full Authority Digital Engine Control, metric: `cycle_time_ms`, safety: `dal-a`): Engine control loop cycle time shall not exceed 10 ms under maximum computational load.

## Affected Components

- Full Authority Digital Engine Control

## Affected Files

- src/fadec/fuel_control.c
- src/fadec/overspeed_protection.c

## Introduced Failures

- `FADEC-ENG-HIL-01`: baseline `passed`, current `failed`, component Full Authority Digital Engine Control.
- `FADEC-ENG-HIL-02`: baseline `passed`, current `failed`, component Full Authority Digital Engine Control.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `FADEC-REQ-001` / `overspeed_response_ms`: baseline `42.0` (pass), current `63.2` (fail), threshold `<= 50.0`.
- `FADEC-REQ-003` / `cycle_time_ms`: baseline `8.1` (pass), current `9.7` (pass), threshold `<= 10.0`.
- `FADEC-REQ-001` / `overspeed_response_ms`: baseline `44.5` (pass), current `61.8` (fail), threshold `<= 50.0`.
- `FADEC-REQ-003` / `cycle_time_ms`: baseline `8.4` (pass), current `9.5` (pass), threshold `<= 10.0`.
- `FADEC-REQ-002` / `fuel_flow_error_pct`: baseline `0.31` (pass), current `0.33` (pass), threshold `<= 0.5`.

## Evidence Summary

- Verdict is confirmed regression.
- FADEC-ENG-HIL-01 failed only in the current run.
- FADEC-ENG-HIL-02 failed only in the current run.
- overspeed_response_ms for FADEC-REQ-001 was 63.2, outside <= 50.
- overspeed_response_ms for FADEC-REQ-001 was 61.8, outside <= 50.
- Mapped affected files: src/fadec/fuel_control.c, src/fadec/overspeed_protection.c.
- cycle_time_ms materially worsened from 8.1 to 9.7.
- overspeed_response_ms materially worsened from 42.0 to 63.2.
- cycle_time_ms materially worsened from 8.4 to 9.5.
- overspeed_response_ms materially worsened from 44.5 to 61.8.

## Rules Triggered

- R1_confirmed_threshold_regression
- R2_introduced_test_failure
- signal_baseline_pass_current_threshold_fail
- signal_introduced_failure_present
- signal_material_metric_worsening

## Confidence Factors

- + baseline_current_pair_present
- + introduced_failure_detected
- + threshold_crossing_detected
- + requirement_mapped
- + affected_file_mapped

## Risk Drivers

- verdict:confirmed_regression
- risk:release_blocking
- safety_level:dal-a
- safety_level:dal-b
- threshold_failed:FADEC-REQ-001:overspeed_response_ms
- threshold_passed:FADEC-REQ-003:cycle_time_ms
- threshold_failed:FADEC-REQ-001:overspeed_response_ms
- threshold_passed:FADEC-REQ-003:cycle_time_ms
- threshold_passed:FADEC-REQ-002:fuel_flow_error_pct

## Signal Summary

- None recorded.

## Recommended Next Checks

- FADEC-ENG-HIL-01
- FADEC-ENG-HIL-01,FADEC-ENG-HIL-02
- FADEC-FUEL-SIL-01
