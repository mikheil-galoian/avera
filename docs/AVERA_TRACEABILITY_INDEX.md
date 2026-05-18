# AVERA Traceability Index

**Date:** 23 April 2026  
**Status:** Draft core contract v0.1  
**Project:** `AVERA`

## Purpose

The traceability index is AVERA's local relationship layer for answering:

- which component maps to which requirement
- which tests or failures prove that requirement is healthy or broken
- what risk history has already been associated with the component or requirement
- what gate history has been recorded for the same evidence chain

It is a derived index, not a new source of truth.

The index should be built from current workspace artifacts plus the engineering memory ledger so AVERA can navigate from a component to its evidence trail without guessing.

## Core Role

The traceability index sits between raw artifacts and the higher-level reports.

It should support the first AVERA core by making the following relationship chain explicit:

`component -> requirement -> test/failure -> risk history -> gate history`

This is the connective tissue for:

- change impact reasoning
- requirement coverage review
- failure provenance
- repeated regression detection
- gate accountability
- later UI exploration

The index should remain usable before any UI shell exists.

## Contract

The traceability index is a local, deterministic, read-optimized data structure generated from workspace artifacts and memory records.

Required properties:

- derived from local files only
- deterministic for the same inputs
- stable schema version on every export
- explicit provenance for each node and edge
- append-friendly when new runs are added
- inspectable as JSON

Recommended storage shape:

- one top-level index document per workspace
- optional per-run snapshots if the CLI needs them
- machine-readable JSON as the canonical export

## Canonical Inputs

The index should be built from these inputs when present:

- `requirements.csv`
- `component_map.json`
- baseline verification results
- current verification results
- test/failure outputs
- report artifacts
- evidence graph artifacts
- engineering memory ledger entries

Future-compatible inputs may include:

- signal traces
- simulation results
- environment status
- field or fleet evidence

## Canonical Entities

The index should normalize the following entity types:

- `component`
- `requirement`
- `test`
- `failure`
- `risk_event`
- `gate_event`
- `analysis_run`

Each entity should carry:

- `id`
- `type`
- `label`
- `source_refs`
- `workspace_path`
- `schema_version`
- `last_seen_utc`

## Node Contract

Each node in the index should describe a single traceability subject.

Required node fields:

- `node_id`
- `node_type`
- `label`
- `source_refs`
- `provenance`
- `schema_version`

Common node types:

- `component`
- `requirement`
- `test`
- `failure`
- `risk_summary`
- `gate_summary`

`source_refs` should point back to the artifacts or memory records that justified the node.

## Edge Contract

Edges should preserve the reasoning path, not just a loose association.

Required edge fields:

- `edge_id`
- `from_node_id`
- `to_node_id`
- `edge_type`
- `evidence_refs`
- `confidence`
- `schema_version`

Expected edge types:

- `maps_to`
- `verified_by`
- `failed_by`
- `contributes_to_risk`
- `recorded_by_gate`
- `supersedes`
- `reopens`

## Provenance Contract

Every traceability assertion should be traceable back to:

- a workspace artifact path
- a report artifact
- a memory ledger record
- or an explicit transformation rule

If an edge or node cannot be justified, it should not be promoted to the canonical index.

## CLI Expectations

The planned CLI surface should make the traceability index easy to rebuild locally.

Expected behavior:

- read the current workspace
- load current artifacts and the memory ledger
- build or refresh the traceability index
- write a deterministic JSON export
- report missing inputs without inventing relationships
- preserve a clear exit status for partial vs failed builds

Recommended command shape:

```bash
avera traceability index --workspace <path> --out <path>
```

Expected outputs:

- traceability index JSON
- optional summary text for the terminal
- optional path references to the source artifacts that contributed to the index

Expected failure behavior:

- missing required artifacts should be explicit
- unreadable historical records should be skipped only when the rest of the index can still be built safely
- unknown relationships should be omitted rather than inferred

## Role In The Core

Before any UI shell exists, the traceability index should serve as the queryable backbone for the core.

It should help the local engine answer:

- what does this component depend on?
- which requirements does this failure affect?
- which failures have already appeared in prior runs?
- what gates were attached to the same evidence chain?
- is this a repeat issue or a new one?

In practice, the index gives AVERA a navigable map over evidence that is richer than a flat report, but still lighter than a full graph database.

## Relationship To Other Core Layers

The traceability index should align with:

- the evidence graph, which explains the proof chain
- the engineering memory ledger, which records analysis and gate history
- the classifier, which assigns risk and verdicts
- the report generator, which presents human-readable output

The index is not meant to replace any of these layers.
It is meant to make them easier to connect and query.

## Future Development

After the first local index is stable, likely extensions are:

- incremental refresh from new runs
- richer failure grouping
- history over time per component and requirement
- stronger links to signal traces and simulation outputs
- query helpers for CLI and future UI
- component/requirement coverage summaries
- risk trend summaries per component
- gate trend summaries per workspace

The long-term goal is a durable local traceability backbone that can support dashboards later without rewriting the underlying evidence model.
