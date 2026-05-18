# AVERA Change Impact Report

## Verdict

- Verdict: `confirmed_regression`
- Risk: `release_blocking`
- Confidence: `high`
- Confidence score: `0.95`

## Affected Requirements

- `FCC-REQ-001` (component: Flight Control Computer, metric: `actuation_latency_ms`, safety: `dal-a`): Control surface actuation latency from pilot input to surface movement shall not exceed 80 ms.
- `FCC-REQ-002` (component: Flight Control Computer, metric: `envelope_engage_ms`, safety: `dal-a`): Envelope protection system must engage within 200 ms upon detection of an overspeed exceedance.
- `FCC-REQ-003` (component: Flight Control Computer, metric: `compute_jitter_ms`, safety: `dal-b`): Control law computation jitter shall not exceed 2 ms between consecutive cycles.

## Affected Components

- Flight Control Computer

## Affected Files

- src/fcc/control_laws.c
- src/fcc/envelope_protection.c

## Introduced Failures

- `FCC-ENV-HIL-01`: baseline `passed`, current `failed`, component Flight Control Computer.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `FCC-REQ-001` / `actuation_latency_ms`: baseline `62.0` (pass), current `63.0` (pass), threshold `<= 80.0`.
- `FCC-REQ-003` / `compute_jitter_ms`: baseline `1.4` (pass), current `1.5` (pass), threshold `<= 2.0`.
- `FCC-REQ-001` / `actuation_latency_ms`: baseline `64.5` (pass), current `65.0` (pass), threshold `<= 80.0`.
- `FCC-REQ-003` / `compute_jitter_ms`: baseline `1.6` (pass), current `1.7` (pass), threshold `<= 2.0`.
- `FCC-REQ-002` / `envelope_engage_ms`: baseline `148.0` (pass), current `247.0` (fail), threshold `<= 200.0`.

## Evidence Summary

- Verdict is confirmed regression.
- FCC-ENV-HIL-01 failed only in the current run.
- envelope_engage_ms for FCC-REQ-002 was 247, outside <= 200.
- Mapped affected files: src/fcc/control_laws.c, src/fcc/envelope_protection.c.
- envelope_engage_ms materially worsened from 148.0 to 247.0.

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
- threshold_passed:FCC-REQ-001:actuation_latency_ms
- threshold_passed:FCC-REQ-003:compute_jitter_ms
- threshold_passed:FCC-REQ-001:actuation_latency_ms
- threshold_passed:FCC-REQ-003:compute_jitter_ms
- threshold_failed:FCC-REQ-002:envelope_engage_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- FCC-CTRL-HIL-01
- FCC-CTRL-HIL-01,FCC-CTRL-HIL-02
- FCC-ENV-HIL-01
