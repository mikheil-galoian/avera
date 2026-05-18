# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `medium`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `PT-REQ-010` (component: Transmission Control Unit, metric: `torque_hole_ms`, safety: `medium`): Torque hole duration during any gear change must not exceed 100 ms to prevent driveline shock.
- `PT-REQ-011` (component: Transmission Control Unit, metric: `shift_completion_ms`, safety: `medium`): Full gear engagement must complete within 800 ms from shift command initiation.
- `PT-REQ-012` (component: Transmission Control Unit, metric: `gear_slip_ratio`, safety: `medium`): Gear slip ratio during shift must not exceed 0.05 to ensure mechanical integrity.

## Affected Components

- Transmission Control Unit

## Affected Files

- src/tcu/shift_controller.c

## Introduced Failures

- `PT-TCU-SQ-01`: baseline `passed`, current `failed`, component Transmission Control Unit.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `PT-REQ-010` / `torque_hole_ms`: baseline `87.0` (pass), current `143.0` (fail), threshold `<= 100.0`.
- `PT-REQ-011` / `shift_completion_ms`: baseline `720.0` (pass), current `780.0` (pass), threshold `<= 800.0`.
- `PT-REQ-012` / `gear_slip_ratio`: baseline `0.031` (pass), current `0.033` (pass), threshold `<= 0.05`.
- `PT-REQ-010` / `torque_hole_ms`: baseline `92.0` (pass), current `95.0` (pass), threshold `<= 100.0`.
- `PT-REQ-011` / `shift_completion_ms`: baseline `755.0` (pass), current `762.0` (pass), threshold `<= 800.0`.
- `PT-REQ-012` / `gear_slip_ratio`: baseline `0.028` (pass), current `0.03` (pass), threshold `<= 0.05`.

## Evidence Summary

- Verdict is confirmed regression.
- PT-TCU-SQ-01 failed only in the current run.
- torque_hole_ms for PT-REQ-010 was 143, outside <= 100.
- Mapped affected files: src/tcu/shift_controller.c.
- torque_hole_ms materially worsened from 87.0 to 143.0.

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
- risk:medium
- safety_level:medium
- threshold_failed:PT-REQ-010:torque_hole_ms
- threshold_passed:PT-REQ-011:shift_completion_ms
- threshold_passed:PT-REQ-012:gear_slip_ratio
- threshold_passed:PT-REQ-010:torque_hole_ms
- threshold_passed:PT-REQ-011:shift_completion_ms
- threshold_passed:PT-REQ-012:gear_slip_ratio

## Signal Summary

- None recorded.

## Recommended Next Checks

- PT-TCU-SQ-01,PT-TCU-SQ-02
- PT-TCU-SQ-02
