# AVERA Workspace Contract

**Date:** 22 April 2026  
**Status:** Draft contract v0

## Purpose

An AVERA workspace is a local folder containing an engineering evidence pack.

AVERA must run without cloud services, hosted accounts, or GitHub.

## Required Files

Each fixture or local evidence pack must include:

```text
requirements.csv
component_map.json
baseline_results.json
current_results.json
change_description.txt
```

## Optional Files

Future optional files:

```text
signal_trace.csv
simulation_results.json
environment_status.json
expected_report.json
```

## requirements.csv

Required columns:

```text
id,component,requirement,metric,operator,threshold
```

Recommended columns:

```text
safety_level,next_checks,unit,domain,verification_stage
```

## component_map.json

Current shape:

```json
{
  "src/bms/thermal_manager.c": {
    "component": "BMS Thermal Control",
    "requirements": ["BMS-REQ-112"],
    "tests": ["BMS-SIL-FASTCHARGE-01"]
  }
}
```

## verification results

Both `baseline_results.json` and `current_results.json` should use:

```json
{
  "runId": "baseline-001",
  "stage": "baseline",
  "tests": [
    {
      "id": "TEST-ID",
      "component": "Component Name",
      "status": "passed",
      "metrics": {
        "metric_name": 1.23
      },
      "evidence": "Optional human-readable evidence."
    }
  ]
}
```

## change_description.txt

Plain text summary of the engineering change.

This is not proof by itself. It provides context for reports and the evidence graph.

## Output Contract

AVERA writes:

```text
reports/avera-report.json
reports/avera-report.md
reports/avera-evidence-graph.json
```

## Workspace Validation Rules

The workspace is valid when:

- all required files exist
- requirements have required fields
- verification JSON has `runId`, `stage`, and `tests`
- test metrics can be matched to at least one requirement metric for high-confidence claims
- component map links affected files to components and requirements
