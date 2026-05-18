# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `release_blocking`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `PT-REQ-001` (component: Engine Control Unit, metric: `max_engine_rpm`, safety: `release_blocking`): Maximum engine speed must not exceed 7000 RPM under any operating condition or fault state.
- `PT-REQ-002` (component: Engine Control Unit, metric: `overspeed_response_ms`, safety: `release_blocking`): ECU overspeed fuel cut-off must engage within 50 ms of detecting an overspeed condition.

## Affected Components

- Engine Control Unit

## Affected Files

- src/ecu/overspeed_protection.c

## Introduced Failures

- `PT-ECU-OS-01`: baseline `passed`, current `failed`, component Engine Control Unit.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `PT-REQ-001` / `max_engine_rpm`: baseline `6850.0` (pass), current `7250.0` (fail), threshold `<= 7000.0`.
- `PT-REQ-002` / `overspeed_response_ms`: baseline `38.0` (pass), current `42.0` (pass), threshold `<= 50.0`.
- `PT-REQ-001` / `max_engine_rpm`: baseline `6720.0` (pass), current `6840.0` (pass), threshold `<= 7000.0`.
- `PT-REQ-002` / `overspeed_response_ms`: baseline `41.0` (pass), current `40.0` (pass), threshold `<= 50.0`.

## Evidence Summary

- Verdict is confirmed regression.
- PT-ECU-OS-01 failed only in the current run.
- max_engine_rpm for PT-REQ-001 was 7250, outside <= 7000.
- Mapped affected files: src/ecu/overspeed_protection.c.
- overspeed_response_ms materially worsened from 38.0 to 42.0.

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
- safety_level:release_blocking
- threshold_failed:PT-REQ-001:max_engine_rpm
- threshold_passed:PT-REQ-002:overspeed_response_ms
- threshold_passed:PT-REQ-001:max_engine_rpm
- threshold_passed:PT-REQ-002:overspeed_response_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- PT-ECU-OS-01,PT-ECU-OS-02
