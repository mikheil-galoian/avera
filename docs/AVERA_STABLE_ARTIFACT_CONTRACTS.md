# AVERA Stable Artifact Contracts

**Project:** `AVERA`  
**Layer:** Stable artifact contracts  
**Status:** Draft core contract v0.1  
**Last updated:** 28 April 2026

## Purpose

The stable artifact contracts layer defines the durable shape of AVERA's core
derived artifacts so the kernel, CLI, and future automation can exchange them
without guessing.

This layer does not invent new evidence. It sets the minimum stable contract
for each artifact family so downstream code can validate, compare, pack, and
export results consistently.

Core role:

`derived evidence -> stable artifact contract -> reliable CLI and automation`

## Artifact Families

The first stable contract set covers these artifact families:

### Report

Human-facing and machine-readable analysis output.

Primary purpose:

- explain the verdict, risk, confidence, and comparison result
- summarize affected requirements, components, and files
- preserve evidence-backed reasoning

Canonical references:

- [Report Schema](/Users/mac/Desktop/AVERA/docs/AVERA_REPORT_SCHEMA.md)

### Graph

Deterministic evidence graph output.

Primary purpose:

- preserve proof paths and relationships
- expose node and edge provenance
- support traceable downstream review

Canonical references:

- [Project Execution Plan](/Users/mac/Desktop/AVERA/docs/AVERA_PROJECT_EXECUTION_PLAN.md)
- [Implementation Status](/Users/mac/Desktop/AVERA/docs/AVERA_IMPLEMENTATION_STATUS.md)

### Memory

Append-only engineering memory ledger.

Primary purpose:

- preserve analysis and gate history
- support repeat-issue review
- provide durable accountability records

Canonical references:

- [Engineering Memory](/Users/mac/Desktop/AVERA/docs/AVERA_ENGINEERING_MEMORY.md)

### Traceability

Derived local relationship index.

Primary purpose:

- map components to requirements, tests, failures, and history
- preserve provenance for each relationship
- support queryable evidence navigation

Canonical references:

- [Traceability Index](/Users/mac/Desktop/AVERA/docs/AVERA_TRACEABILITY_INDEX.md)

### Decision

Deterministic operational recommendation record.

Primary purpose:

- turn evidence-backed findings into an auditable action
- preserve owner routing, corrective actions, and escalation context
- keep the recommendation tied to the original evidence chain

Canonical references:

- [Decision Engine](/Users/mac/Desktop/AVERA/docs/AVERA_DECISION_ENGINE.md)

### Trend

Historical summary layer over prior runs.

Primary purpose:

- summarize run-to-run evolution
- preserve conservative history visibility
- avoid turning history into a new source of truth

Canonical references:

- [Trend Layer](/Users/mac/Desktop/AVERA/docs/AVERA_TREND_LAYER.md)

### Workspace Pack

Portable export bundle built from derived artifacts.

Primary purpose:

- package the report, graph, memory slice, traceability, decision, and manifest
- provide a stable handoff boundary for CLI and future UI use
- preserve provenance across export boundaries

Canonical references:

- [Workspace Pack](/Users/mac/Desktop/AVERA/docs/AVERA_WORKSPACE_PACK.md)

## Stability Rules

Stable artifact contracts must satisfy these rules:

1. The artifact must be derived from local workspace evidence or prior derived
   artifacts.
2. The artifact must not become a hidden new source of truth.
3. The same inputs and policy version must produce the same structure and
   meaning.
4. Missing evidence must be reported explicitly, not inferred away.
5. Provenance must remain inspectable back to source artifacts, memory records,
   or explicit transformation rules.
6. New fields may be added only when they do not break the established
   contract or when the breaking change is handled by a version bump.
7. Field removal or semantic repurposing requires an explicit compatibility
   decision.
8. Derived summaries must remain conservative when evidence is thin or mixed.

## Versioning Policy

Each artifact family should carry an explicit `schema_version`.

Recommended policy:

- use semantic versions for contract meaning, not internal implementation
- prefer additive changes for minor revisions
- reserve major revisions for breaking field changes, renamed semantics, or
  incompatible validation rules
- use patch-level revisions only for clarifications that do not change the
  contract shape

Versioning expectations:

- `schema_version` must be present in every exported artifact
- artifact-specific schemas may evolve independently
- a pack manifest should record the exact versions included in the bundle
- generated output should remain deterministic for a given version and input set

## Schema Policy

Each stable artifact should define:

- artifact identity
- schema version
- generated timestamp
- workspace or source reference
- provenance references
- canonical payload
- warnings or caveats when evidence is incomplete

Schema policy rules:

1. Required fields must be validated before the artifact is treated as complete.
2. Optional fields may appear when the workspace has relevant evidence.
3. Empty or missing sections should be represented explicitly when useful for
   review.
4. Validation should reject structurally malformed output early.
5. Validation should tolerate safe partial exports only when the artifact's
   contract allows it.

## Compatibility Rules

Compatibility is a first-class requirement for every stable artifact.

The default rules are:

- backward-compatible additive fields are allowed within a major version
- consumers should ignore unknown fields when the contract allows forward
  compatibility
- removed or renamed fields must be announced by a version bump and decision
  log entry
- schema changes that alter meaning without changing field names are breaking
  changes
- pack/export layers should preserve the original artifact version rather than
  rewriting it

Compatibility outcomes should be explicit:

- compatible
- compatible_with_warnings
- partial_export
- incompatible

## CLI Expectations

The CLI should treat these artifact contracts as validation boundaries.

Expected behavior:

- build or load each artifact from a workspace in a deterministic way
- validate the artifact against its contract before exporting or packing
- emit a clear exit status when validation fails
- preserve artifact paths, schema versions, and provenance in terminal output or
  manifest data
- avoid fabricating missing sections during export
- prefer JSON-first validation with optional Markdown or human-readable output

Recommended command expectations:

- `avera analyze` should emit report and graph artifacts that satisfy their
  contracts
- `avera validate-workspace` should reject workspaces that cannot support the
  required artifact set
- `avera gate` should read a validated report contract before producing a gate
  result
- `avera traceability index` should only emit a stable index when the source
  inputs satisfy the traceability contract
- `avera decision` should only emit a decision when traceability and memory
  inputs are valid enough to support it
- `avera trends build` should only emit a trend summary when prior artifacts are
  sufficient for conservative history reporting
- `avera pack` should package validated artifacts and preserve their versions in
  the manifest

Expected CLI output should name:

- artifact type
- schema version
- source path or workspace path
- validation warnings
- export path, when applicable

## Relationship To Other Layers

This layer sits across the core artifact families and keeps them aligned.

It is narrower than the product roadmap and broader than any single schema file.
It provides the shared rules that let AVERA compare, validate, export, and
pack artifacts without turning each command into a special case.

In practice, it supports:

- report validation
- evidence graph validation
- memory ledger validation
- traceability index validation
- decision record validation
- trend export validation
- workspace pack export validation

## Further Development

Likely next steps after v0.1:

- add per-artifact validation checklists
- define a shared validation result format
- add bundle-level contract tests for pack exports
- formalize compatibility warnings for forward-only consumers
- align artifact contract versioning with CLI help text and manifest metadata

