# AVERA Change Impact Report

## Verdict

- Verdict: `insufficient_evidence`
- Risk: `unknown`
- Confidence: `low`
- Confidence score: `0.39`

## Affected Requirements

- `BMS-REQ-118` (component: BMS Thermal Control, metric: `cooling_response_ms`, safety: `medium`): Cooling response delay during fast charging must not exceed 500 ms

## Affected Components

- BMS Thermal Control

## Affected Files

- src/bms/thermal_manager.c

## Introduced Failures

- None recorded.

## Preexisting Failures

- None recorded.

## Threshold Evidence

- `BMS-REQ-112` / `max_cell_temp_c`: baseline `47.8` (pass), current `None` (unknown), threshold `<= 50.0`.
- `BMS-REQ-118` / `cooling_response_ms`: baseline `440.0` (pass), current `472.0` (pass), threshold `<= 500.0`.

## Evidence Summary

- Verdict is insufficient evidence.
- Mapped affected files: src/bms/thermal_manager.c.

## Rules Triggered

- R8_insufficient_evidence
- signal_unrecognized_or_inconclusive_status

## Confidence Factors

- + baseline_current_pair_present
- + requirement_mapped
- + affected_file_mapped
- - incomplete_or_inconclusive_current_evidence

## Risk Drivers

- verdict:insufficient_evidence
- risk:unknown
- safety_level:medium
- threshold_passed:BMS-REQ-118:cooling_response_ms

## Signal Summary

- None recorded.

## Recommended Next Checks

- BMS-HIL-FASTCHARGE-07
