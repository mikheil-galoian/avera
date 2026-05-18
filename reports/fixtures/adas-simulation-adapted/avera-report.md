# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `high`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `ADAS-REQ-204` (component: ADAS Pedestrian Detection, metric: `pedestrian_recall`, safety: `high`): Pedestrian recall in urban daylight regression suite must not fall below 0.95
- `ADAS-REQ-219` (component: ADAS Pedestrian Detection, metric: `brake_trigger_latency_ms`, safety: `high`): Maximum emergency braking trigger latency for pedestrian crossing scenarios must not exceed 120 ms

## Affected Components

- ADAS Pedestrian Detection

## Affected Files

- src/adas/perception/pedestrian_classifier.cpp

## Introduced Failures

- `ADAS-SIL-VRU-REGRESSION-03`: baseline `passed`, current `failed`, component ADAS Pedestrian Detection.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `ADAS-REQ-204` / `pedestrian_recall`: baseline `0.972` (pass), current `0.903` (fail), threshold `>= 0.95`.
- `ADAS-REQ-219` / `brake_trigger_latency_ms`: baseline `104.0` (pass), current `146.0` (fail), threshold `<= 120.0`.

## Evidence Summary

- Verdict is confirmed regression.
- ADAS-SIL-VRU-REGRESSION-03 failed only in the current run.
- pedestrian_recall for ADAS-REQ-204 was 0.903, outside >= 0.95.
- brake_trigger_latency_ms for ADAS-REQ-219 was 146, outside <= 120.
- Mapped affected files: src/adas/perception/pedestrian_classifier.cpp.
- brake_trigger_latency_ms materially worsened from 104.0 to 146.0.

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
- safety_level:high
- threshold_failed:ADAS-REQ-204:pedestrian_recall
- threshold_failed:ADAS-REQ-219:brake_trigger_latency_ms

## Signal Summary

- `ADAS-SIL-VRU-REGRESSION-03` / `brake_trigger_latency_ms`: min `104.0`, max `146.0`, last `146.0` ms, points `4`.
- `ADAS-SIL-VRU-REGRESSION-03` / `pedestrian_recall`: min `0.903`, max `0.972`, last `0.903` ratio, points `4`.

## Recommended Next Checks

- ADAS-HIL-VRU-12
