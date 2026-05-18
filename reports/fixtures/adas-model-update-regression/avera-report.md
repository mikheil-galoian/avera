# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `release_blocking`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `REQ-SAFETY-012` (component: adas-perception-module, metric: `detection_rate`, safety: `d`): Pedestrian detection rate shall be >= 0.95 in all lighting conditions including night and rain
- `REQ-SAFETY-008` (component: adas-perception-module, metric: `false_positive_rate`, safety: `c`): False positive rate for vehicle detection shall be <= 0.05 on highway scenarios
- `REQ-SAFETY-015` (component: adas-perception-module, metric: `latency_p95_ms`, safety: `c`): Pedestrian detection latency shall be <= 50ms at 95th percentile
- `REQ-PERF-001` (component: adas-perception-module, metric: `map_score`, safety: `low`): Overall mAP on standard ADAS benchmark shall be >= 0.82
- `REQ-PERF-003` (component: adas-perception-module, metric: `inference_time_ms`, safety: `low`): Model inference time shall be <= 25ms on target hardware TDA4VM
- `REQ-INTEG-001` (component: adas-perception-module, metric: `output_schema_version`, safety: `low`): Perception module output format shall conform to AveraPerceptionOutput v2 schema

## Affected Components

- adas-perception-module

## Affected Files

- model/adas-perception-module

## Introduced Failures

- `SC-SAFETY-012-night-rain`: baseline `passed`, current `failed`, component adas-perception-module.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `REQ-PERF-001` / `map_score`: baseline `0.847` (pass), current `0.863` (pass), threshold `>= 0.82`.
- `REQ-PERF-003` / `inference_time_ms`: baseline `21.4` (pass), current `22.1` (pass), threshold `<= 25.0`.
- `REQ-SAFETY-008` / `false_positive_rate`: baseline `0.02` (pass), current `0.02` (pass), threshold `<= 0.05`.
- `REQ-SAFETY-012` / `detection_rate`: baseline `0.99` (pass), current `0.98` (pass), threshold `>= 0.95`.
- `REQ-SAFETY-012` / `detection_rate`: baseline `0.97` (pass), current `0.94` (fail), threshold `>= 0.95`.
- `REQ-SAFETY-015` / `latency_p95_ms`: baseline `38.2` (pass), current `41.7` (pass), threshold `<= 50.0`.

## Evidence Summary

- Verdict is confirmed regression.
- SC-SAFETY-012-night-rain failed only in the current run.
- detection_rate for REQ-SAFETY-012 was 0.94, outside >= 0.95.
- Mapped affected files: model/adas-perception-module.

## Rules Triggered

- R1_confirmed_threshold_regression
- R2_introduced_test_failure
- signal_baseline_pass_current_threshold_fail
- signal_introduced_failure_present

## Confidence Factors

- + baseline_current_pair_present
- + introduced_failure_detected
- + threshold_crossing_detected
- + requirement_mapped
- + affected_file_mapped

## Risk Drivers

- verdict:confirmed_regression
- risk:release_blocking
- safety_level:c
- safety_level:d
- safety_level:low
- threshold_passed:REQ-PERF-001:map_score
- threshold_passed:REQ-PERF-003:inference_time_ms
- threshold_passed:REQ-SAFETY-008:false_positive_rate
- threshold_passed:REQ-SAFETY-012:detection_rate
- threshold_failed:REQ-SAFETY-012:detection_rate
- threshold_passed:REQ-SAFETY-015:latency_p95_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- None recorded.
