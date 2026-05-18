# AVERA Workspace Pack

**Project:** `AVERA`  
**Layer:** Workspace pack / export layer  
**Status:** Draft core contract v0.1  
**Last updated:** 23 April 2026

## Purpose

The AVERA workspace pack is the portable export layer for a validated local
workspace.

Its job is to gather the evidence that already exists in the workspace and
package it into a deterministic bundle that can be reviewed, shared, archived,
or handed to a future UI without re-deriving the source truth.

This layer does not replace the report, traceability index, memory ledger, or
decision engine. It packages their outputs into a single export artifact with
clear provenance.

Core role:

`workspace -> curated export bundle`

## Bundle Intent

The pack is designed for three uses:

1. local CLI export after analysis
2. durable handoff between CLI and future UI
3. reviewable bundle for human inspection or downstream automation

It should stay conservative. If required inputs are missing, the bundle should
report that explicitly rather than inventing content.

## Export Bundle Composition

The export bundle should include these top-level artifacts:

- `report`
- `graph`
- `memory slice`
- `traceability`
- `decision`
- `manifest`

### Report

Contains the generated analysis report material.

Expected contents:

- JSON report
- Markdown report, if present
- schema version
- output paths

The report remains the human-facing explanation of the run.

### Graph

Contains the evidence graph export for the workspace or run.

Expected contents:

- evidence graph JSON
- node and edge summaries
- schema version

The graph should stay deterministic and inspectable.

### Memory Slice

Contains the relevant engineering memory records for the exported run.

Expected contents:

- analysis record
- gate record, if one exists
- decision record, if one exists
- memory ledger source references

The slice should be narrow enough to remain portable, but complete enough to
preserve the accountability trail for the bundle.

### Traceability

Contains the traceability view needed to explain how evidence connects.

Expected contents:

- traceability index or traceability slice
- provenance for component, requirement, test, and failure links
- affected entity summaries

This is the bundle's navigational layer. It should let a reviewer move from the
report back to the workspace evidence without guessing.

### Decision

Contains the decision output associated with the workspace pack.

Expected contents:

- decision category or outcome
- decision rationale
- policy signals
- traceability references
- memory references

This artifact is especially useful once the decision engine is part of the core
workflow.

### Manifest

Contains bundle metadata and integrity references.

Expected contents:

- bundle schema version
- export timestamp
- workspace identifier or path
- source artifact list
- relative bundle paths
- file checksums or hashes, when available
- export command metadata

The manifest is the entry point for downstream tooling. It should describe the
bundle without becoming a second source of truth.

## CLI Behavior

The CLI should export a workspace pack only after the workspace has been
validated enough to avoid silent corruption.

Recommended behavior:

- read a local workspace path
- verify required inputs before export
- collect report, graph, memory, traceability, decision, and manifest data
- write a deterministic bundle layout
- preserve source paths in the manifest
- refuse to infer missing evidence
- emit a clear exit status for success, partial export, or failure

Recommended command shape:

```bash
avera export workspace-pack --workspace <path> --out <path>
```

Expected CLI output:

- bundle location
- included artifact list
- missing artifact warnings, if any
- schema versions used

## Role Before UI

Before any UI layer exists, the workspace pack should be the handoff boundary
for a validated local run.

It should make it easy to:

- inspect the full proof trail from one exported bundle
- attach the same export to review workflows
- compare two runs without reconstructing the whole workspace
- hand the output to a future desktop or web UI

This keeps the CLI as the primary product surface while still defining the
portable shape that the UI will eventually consume.

## Contract Rules

- The workspace pack is derived from existing workspace artifacts.
- The pack must not become a hidden new source of truth.
- Bundle contents should be deterministic for the same input set.
- Missing or unreadable artifacts should be reported, not guessed.
- Each exported item should preserve provenance back to its source artifact or
  record.
- The manifest should remain stable across exports with the same inputs and
  export policy.

## Further Development

Likely next steps after v0.1:

- add per-artifact checksums
- support compressed archive output
- support selective export profiles
- add export diffing between bundles
- add bundle validation and inspection commands
- align the bundle manifest with future UI ingestion
- include richer source summaries for traceability and decision review

The long-term goal is a portable evidence package that makes AVERA easier to
share, review, and present without weakening the local evidence model.
