# AVERA Demo Scenario: BMS Thermal Regression

**Date:** 21 April 2026  
**Status:** Draft

## Purpose

This demo should show AVERA's core value in one understandable automotive scenario.

It should prove:

```text
change -> requirement -> verification result -> signal evidence -> risk
```

## Story

An engineer changes the battery cooling logic.

The code change appears small, but after the change, the fast charging simulation shows that maximum cell temperature exceeds the allowed requirement threshold.

AVERA compares baseline vs current evidence, maps the issue to the affected BMS requirement, connects it to the changed file, and recommends release-blocking follow-up verification.

## Requirement

```text
ID: BMS-REQ-112
Component: BMS Thermal Control
Requirement: Maximum cell temperature during fast charging must not exceed 50°C.
Metric: max_cell_temp_c
Operator: <=
Threshold: 50.0
Safety relevance: high
Suggested next check: BMS-HIL-FASTCHARGE-07
```

## Baseline Result

```text
Test: BMS-SIL-FASTCHARGE-01
Status: passed
max_cell_temp_c: 47.1
cooling_response_ms: 420
```

## Current Result

```text
Test: BMS-SIL-FASTCHARGE-01
Status: failed
max_cell_temp_c: 52.8
cooling_response_ms: 610
```

## Changed File

```text
src/bms/thermal_manager.c
```

Mapping:

```text
src/bms/thermal_manager.c
  -> BMS Thermal Control
  -> BMS-REQ-112
  -> BMS-SIL-FASTCHARGE-01
```

## Expected AVERA Output

```text
Verdict: confirmed_regression
Risk: high
Confidence: high
Affected component: BMS Thermal Control
Affected requirement: BMS-REQ-112
Evidence: max_cell_temp_c increased from 47.1°C to 52.8°C
Threshold: <= 50.0°C
Recommendation: block release and run BMS-HIL-FASTCHARGE-07
```

## Fixture Files

Suggested location:

```text
avera/fixtures/bms-fast-charge/
```

Suggested files:

```text
requirements.csv
component_map.json
baseline_results.json
current_results.json
signal_trace_baseline.csv
signal_trace_current.csv
thermal_manager.diff
expected-report.md
```

## Requirements CSV Example

```csv
id,component,requirement,metric,operator,threshold,safety_level,next_checks
BMS-REQ-112,BMS Thermal Control,Max cell temperature during fast charge,max_cell_temp_c,<=,50.0,high,BMS-HIL-FASTCHARGE-07
BMS-REQ-118,BMS Thermal Control,Cooling response delay,cooling_response_ms,<=,500.0,medium,BMS-HIL-FASTCHARGE-07
```

## Component Map Example

```json
{
  "src/bms/thermal_manager.c": {
    "component": "BMS Thermal Control",
    "requirements": ["BMS-REQ-112", "BMS-REQ-118"],
    "tests": ["BMS-SIL-FASTCHARGE-01"]
  }
}
```

## Baseline Results Example

```json
{
  "runId": "baseline-bms-001",
  "stage": "baseline",
  "tests": [
    {
      "id": "BMS-SIL-FASTCHARGE-01",
      "component": "BMS Thermal Control",
      "status": "passed",
      "metrics": {
        "max_cell_temp_c": 47.1,
        "cooling_response_ms": 420
      }
    }
  ]
}
```

## Current Results Example

```json
{
  "runId": "current-bms-001",
  "stage": "current",
  "tests": [
    {
      "id": "BMS-SIL-FASTCHARGE-01",
      "component": "BMS Thermal Control",
      "status": "failed",
      "metrics": {
        "max_cell_temp_c": 52.8,
        "cooling_response_ms": 610
      },
      "evidence": "Maximum cell temperature exceeded fast-charge threshold."
    }
  ]
}
```

## Demo Command Target

Future command:

```bash
avera analyze \
  --baseline avera/fixtures/bms-fast-charge/baseline_results.json \
  --current avera/fixtures/bms-fast-charge/current_results.json \
  --requirements avera/fixtures/bms-fast-charge/requirements.csv \
  --component-map avera/fixtures/bms-fast-charge/component_map.json \
  --diff avera/fixtures/bms-fast-charge/thermal_manager.diff
```

## Demo Success Criteria

The demo is successful if it produces:

- a high-confidence regression classification
- an affected requirement
- numeric threshold evidence
- changed-file mapping evidence
- next verification recommendation
- Markdown and JSON reports
