# AVERA Evidence Model

**Date:** 22 April 2026  
**Status:** Draft contract v0

## Purpose

This document defines the first stable evidence model for AVERA.

AVERA conclusions must be built from explicit evidence records, not hidden assumptions.

## Evidence Chain v0

```text
engineering_change
  -> changed_file
  -> component
  -> requirement
  -> verification_test
  -> metric_observation
  -> threshold_evaluation
  -> comparison_finding
  -> risk_assessment
  -> recommendation
```

## Canonical Entities

### EngineeringChange

Fields:

- `id`
- `description`
- `changed_files`
- `source_artifact`

### Requirement

Fields:

- `id`
- `component`
- `requirement`
- `metric`
- `operator`
- `threshold`
- `safety_level`
- `next_checks`

### ComponentMapEntry

Fields:

- `file_path`
- `component`
- `requirements`
- `tests`

### VerificationRun

Fields:

- `run_id`
- `stage`
- `tests`
- `metadata`

### TestResult

Fields:

- `id`
- `status`
- `component`
- `metrics`
- `evidence`

### ThresholdEvidence

Fields:

- `requirement_id`
- `metric`
- `operator`
- `threshold`
- `baseline_value`
- `current_value`
- `baseline_passed`
- `current_passed`
- `test_id`

### SignalTrace v0.1

Signal trace evidence is an optional time-series input loaded from `signal_trace.csv`.
It is staged as evidence for future threshold and risk reasoning, but it does not
change classifier behavior in v0.1.

Required point fields:

- `timestamp_ms`
- `scenario_id`
- `test_id`
- `signal`
- `value`
- `unit`

Summary helper:

- API: `summarize_signal_trace(points)`
- Input: ordered `SignalTracePoint` objects or dict-like records with `test_id`,
  `signal`, `value`, and `unit`
- Output: deterministic list of summary records, grouped by `(test_id, signal)`
- Fields per summary record: `test_id`, `signal`, `min`, `max`, `last`, `unit`,
  `count`

Rules:

- `last` means the last observed value in input order.
- Mixed units for the same `(test_id, signal)` pair are invalid evidence and
  should raise an error.
- Summary records are sorted by `test_id`, then `signal` for stable JSON output.

### RiskAssessment

Fields:

- `verdict`
- `risk`
- `confidence`
- `affected_requirements`
- `affected_components`
- `affected_files`
- `introduced_failures`
- `preexisting_failures`
- `threshold_evidence`
- `signal_summary`
- `evidence_summary`
- `recommended_next_checks`

`signal_summary` is optional. When present, evidence graph builders should create
`signal_summary` nodes for each record and connect them to the risk assessment.
If a summary record has `test_id`, it should also connect to the matching test
failure or verification evidence node when present. If a summary record's
`signal` matches a threshold evidence `metric`, and either `test_id` is equal or
one side omits `test_id`, it should connect to that threshold evidence node.

## Evidence Graph v0

Graph output should be deterministic JSON:

```json
{
  "schema_version": "avera.evidence_graph.v0",
  "nodes": [],
  "edges": [],
  "summary": {}
}
```

Node fields:

- `id`
- `type`
- `label`
- `data`

Edge fields:

- `source`
- `target`
- `type`

Required edge types:

- `change_touches_file`
- `file_maps_to_component`
- `component_owns_requirement`
- `requirement_verified_by_test`
- `test_produced_metric`
- `metric_evaluates_requirement`
- `finding_supports_risk`
- `risk_requires_recommendation`

Current graph builder relation labels include:

- `signal_summary -> risk` as `supports`
- `signal_summary -> test_failure` as `summarizes_test`
- `signal_summary -> threshold_evidence` as `supports_threshold`

## Claim Rule

Every high-confidence or high-risk conclusion must cite at least:

- one requirement
- one baseline/current comparison
- one verification result or metric
- one risk assessment record

## Storage v0

File-based outputs:

- `reports/avera-report.json`
- `reports/avera-report.md`
- `reports/avera-evidence-graph.json`

SQLite can be introduced only after the file-based graph is stable.
