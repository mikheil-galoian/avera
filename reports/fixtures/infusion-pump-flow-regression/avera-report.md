# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `high`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `IMD-REQ-001` (component: Infusion Pump Dosage Control, metric: `flow_rate_deviation_pct`, safety: `class-c`): Flow rate deviation from programmed dose must not exceed 5.0 percent under IEC-62304 Class C
- `IMD-REQ-002` (component: Infusion Pump Dosage Control, metric: `occlusion_detect_ms`, safety: `class-c`): Occlusion detection response time must not exceed 3000 ms
- `IMD-REQ-003` (component: Infusion Pump Alarm System, metric: `alarm_trigger_ms`, safety: `class-b`): Over-infusion alarm must trigger within 500 ms of threshold breach

## Affected Components

- Infusion Pump Alarm System
- Infusion Pump Dosage Control

## Affected Files

- src/pump/alarm/over_infusion_detector.c
- src/pump/dosage/flow_rate_controller.c

## Introduced Failures

- `IMD-SIL-FLOW-01`: baseline `passed`, current `failed`, component Infusion Pump Dosage Control.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `IMD-REQ-003` / `alarm_trigger_ms`: baseline `287.0` (pass), current `294.0` (pass), threshold `<= 500.0`.
- `IMD-REQ-001` / `flow_rate_deviation_pct`: baseline `2.3` (pass), current `7.8` (fail), threshold `<= 5.0`.
- `IMD-REQ-002` / `occlusion_detect_ms`: baseline `1840.0` (pass), current `2190.0` (pass), threshold `<= 3000.0`.

## Evidence Summary

- Verdict is confirmed regression.
- IMD-SIL-FLOW-01 failed only in the current run.
- flow_rate_deviation_pct for IMD-REQ-001 was 7.8, outside <= 5.
- Mapped affected files: src/pump/alarm/over_infusion_detector.c, src/pump/dosage/flow_rate_controller.c.
- flow_rate_deviation_pct materially worsened from 2.3 to 7.8.
- occlusion_detect_ms materially worsened from 1840.0 to 2190.0.

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
- risk:high
- safety_level:class-b
- safety_level:class-c
- threshold_passed:IMD-REQ-003:alarm_trigger_ms
- threshold_failed:IMD-REQ-001:flow_rate_deviation_pct
- threshold_passed:IMD-REQ-002:occlusion_detect_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- IMD-SIL-ALARM-02
- IMD-SIL-FLOW-01
