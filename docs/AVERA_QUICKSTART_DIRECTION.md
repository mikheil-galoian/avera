# AVERA Quickstart Direction

**Date:** 21 April 2026  
**Status:** Draft

## Purpose

This document defines the fastest practical path from idea to working AVERA demo.

## Starting Assumption

AVERA should begin as a standalone automotive engineering product with its own proof model and demo assets.

Do not start with a dashboard.

Start with a one-command demo that produces an evidence report.

## First Demo Scenario

Use a Battery Management System scenario.

Requirement:

```text
BMS-REQ-112: Maximum cell temperature during fast charging must not exceed 50°C.
```

Baseline:

```text
test: battery_fast_charge_high_temp
status: pass
max_cell_temp: 47.1
threshold: 50.0
```

Current:

```text
test: battery_fast_charge_high_temp
status: fail
max_cell_temp: 52.8
threshold: 50.0
```

Expected AVERA result:

```text
classification: confirmed_regression
risk: high
confidence: high
affected_requirement: BMS-REQ-112
recommendation: block release and run HIL scenario BMS-HIL-07
```

## Suggested Fixture Layout

```text
avera/fixtures/bms-fast-charge/
  baseline/
    requirements.csv
    verification-results.json
    signal-trace.csv
  current/
    requirements.csv
    verification-results.json
    signal-trace.csv
  current.patch
  avera.config.json
```

Alternative future layout:

```text
avera/fixtures/bms-fast-charge/
```

## Suggested Requirement Schema

CSV columns:

```text
id,title,component,module,file_path,safety_relevance,threshold_signal,threshold_operator,threshold_value,next_checks
```

Example:

```text
BMS-REQ-112,Fast charge cell temperature limit,BMS,thermal_manager,src/bms/thermal_manager.c,high,max_cell_temp,<=,50.0,BMS-HIL-07
```

## Suggested Verification Result Schema

```json
{
  "runId": "current-bms-fast-charge",
  "stage": "current",
  "checks": [
    {
      "id": "battery_fast_charge_high_temp",
      "type": "simulation",
      "status": "fail",
      "component": "BMS",
      "module": "thermal_manager",
      "signals": {
        "max_cell_temp": 52.8
      },
      "evidence": "max_cell_temp exceeded threshold during fast-charge scenario"
    }
  ]
}
```

## First Report Shape

Markdown report sections:

- Summary
- Verdict
- Risk
- Confidence
- Affected Requirements
- Introduced Failures
- Evidence
- Recommended Next Checks
- Changed Files
- Machine-Readable Artifact Path

## First Implementation Path

Step 1:

- create fixture artifacts
- create report schema
- create one script that compares baseline/current JSON

Step 2:

- add requirements CSV parsing
- map failed checks to requirements by component/module/file path

Step 3:

- add engineering change description ingestion
- map changed files to requirements and failures

Step 4:

- add risk rules
- add confidence rules
- add Markdown output

Step 5:

- add fixture variants
- add one command to run all AVERA fixtures

## First Local Output Example

```text
AVERA Change Impact

Verdict: confirmed_regression
Risk: high
Confidence: high

Affected requirement:
- BMS-REQ-112: Fast charge cell temperature limit

Evidence:
- baseline max_cell_temp: 47.1°C
- current max_cell_temp: 52.8°C
- threshold: <= 50.0°C
- failure appeared only after current change
- changed file maps to requirement owner: src/bms/thermal_manager.c

Recommended next checks:
- BMS-HIL-07
- fast_charge_high_temp regression pack
```

## Direction After Demo

After the first demo works, decide whether AVERA should become:

- a standalone local tool
- a standalone package with fixture demos
- a future hosted/team platform

The decision should be made after there is a working report, not before.
