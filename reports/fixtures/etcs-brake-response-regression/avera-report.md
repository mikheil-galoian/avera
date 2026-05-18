# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `release_blocking`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `ETCS-REQ-001` (component: ETCS Emergency Braking, metric: `brake_application_ms`, safety: `sil4`): Emergency brake application time must not exceed 1200 ms under SIL 4 conditions
- `ETCS-REQ-002` (component: ETCS Emergency Braking, metric: `brake_confirm_ms`, safety: `sil4`): Brake confirmation signal must be received within 400 ms of command
- `ETCS-REQ-003` (component: ETCS Cab Signalling, metric: `supervision_cycle_ms`, safety: `sil3`): Speed supervision update cycle must not exceed 100 ms

## Affected Components

- ETCS Cab Signalling
- ETCS Emergency Braking

## Affected Files

- src/etcs/braking/emergency_brake_controller.c
- src/etcs/signalling/cab_signal_processor.c

## Introduced Failures

- `ETCS-HIL-BRAKE-01`: baseline `passed`, current `failed`, component ETCS Emergency Braking.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `ETCS-REQ-001` / `brake_application_ms`: baseline `1047.0` (pass), current `1387.0` (fail), threshold `<= 1200.0`.
- `ETCS-REQ-002` / `brake_confirm_ms`: baseline `312.0` (pass), current `451.0` (fail), threshold `<= 400.0`.
- `ETCS-REQ-003` / `supervision_cycle_ms`: baseline `82.0` (pass), current `86.0` (pass), threshold `<= 100.0`.

## Evidence Summary

- Verdict is confirmed regression.
- ETCS-HIL-BRAKE-01 failed only in the current run.
- brake_application_ms for ETCS-REQ-001 was 1387, outside <= 1200.
- brake_confirm_ms for ETCS-REQ-002 was 451, outside <= 400.
- Mapped affected files: src/etcs/braking/emergency_brake_controller.c, src/etcs/signalling/cab_signal_processor.c.
- brake_application_ms materially worsened from 1047.0 to 1387.0.
- brake_confirm_ms materially worsened from 312.0 to 451.0.

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
- safety_level:sil3
- safety_level:sil4
- threshold_failed:ETCS-REQ-001:brake_application_ms
- threshold_failed:ETCS-REQ-002:brake_confirm_ms
- threshold_passed:ETCS-REQ-003:supervision_cycle_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- ETCS-HIL-BRAKE-01
- ETCS-HIL-SIGNAL-03
