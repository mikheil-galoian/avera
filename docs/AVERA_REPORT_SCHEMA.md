# AVERA Report Schema

**Date:** 22 April 2026  
**Status:** Draft schema v0

## Purpose

The AVERA report must be stable enough for humans and future tools.

## JSON Report v0

Required top-level fields:

- `schema_version`
- `verdict`
- `risk`
- `confidence`
- `confidence_score`
- `affected_requirements`
- `affected_components`
- `affected_files`
- `introduced_failures`
- `preexisting_failures`
- `threshold_evidence`
- `evidence_summary`
- `recommended_next_checks`
- `comparison_summary`
- `rules_triggered`
- `confidence_factors`
- `risk_drivers`

Optional top-level fields:

- `signal_trace_points`
- `signal_summary`
- `evidence_graph_path`

## Markdown Report v0

Required sections:

- Verdict
- Affected Requirements
- Affected Components
- Affected Files
- Introduced Failures
- Preexisting Failures
- Threshold Evidence
- Evidence Summary
- Rules Triggered
- Confidence Factors
- Risk Drivers
- Signal Summary
- Recommended Next Checks

## Evidence Graph Report

File:

```text
avera-evidence-graph.json
```

Required fields:

- `schema_version`
- `nodes`
- `edges`
- `summary`

## Compatibility Rule

Existing report fields should not be removed without a decision log entry.
