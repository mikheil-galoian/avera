# AVERA Evidence Manifest

**Date:** 5 June 2026
**Status:** Draft v0.1 — first implemented slice of the serious-program layer
**Module:** `src/avera/evidence/`
**Companion:** `docs/AVERA_EVIDENCE_MODEL.md` (conceptual evidence chain & entities)

## Why this exists

`AVERA_EVIDENCE_MODEL.md` defines the *conceptual* evidence chain (change →
requirement → test → metric → threshold → risk → recommendation) and the per-run
artifacts.

This document defines the *binding* layer on top of that flow: a single, formal,
content-addressed object — the **Evidence Manifest** — that ties one analysis
run's artifacts together with one verifiable integrity root.

For regulated domains (automotive, medical, aviation, railway) the manifest is the
object an auditor or reviewer anchors to: one hash that changes if any underlying
artifact changes by a single byte.

## What the manifest binds

AVERA already produces report, evidence graph, traceability index, decision,
trend, and workspace pack. Each is individually validated, and the workspace pack
already hashes each file. The manifest binds the **whole set** together.

```text
report ─┐
graph ──┤
trace ──┼──>  Evidence Manifest  ──>  integrity_root (single SHA-256)
decision┤
trend ──┤
pack ───┘
```

The manifest does **not** replace any artifact. It is derived and
non-authoritative.

## Top-level shape

| Field | Meaning |
|---|---|
| `schema_version` | `avera.evidence_manifest.v0.1` |
| `workspace` | analysed workspace path + name |
| `generated_at_utc` | manifest creation time (excluded from integrity root) |
| `artifacts` | per-role references (see below) |
| `integrity_root` | deterministic SHA-256 binding all present artifacts |
| `completeness` | which roles are present/missing; `complete` flag |
| `summary` | verdict / risk / confidence pulled from the report |
| `provenance` | tool, tool version, generator, source artifact paths |

### Per-artifact reference

Each entry in `artifacts` carries:

- `role` — `report` \| `graph` \| `traceability` \| `decision` \| `trend` \| `workspace_pack`
- `path` — on-disk location (provenance)
- `present` — whether the file exists on disk
- `sha256` — content digest of the file (content addressing)
- `schema_version` — the artifact's declared schema version
- `schema_supported` — whether that version is in the central registry
- `schema_current` — the registry's current version for that role

## Integrity root

`integrity_root` is a SHA-256 over canonical JSON of the sorted set of
`{role, sha256, schema_version}` for every **present** artifact.

- **Deterministic** — same content always yields the same root.
- **Machine-independent** — timestamps and absolute paths are excluded, so the
  root is stable across machines for the same content.
- **Tamper-evident** — changing any bound artifact changes the root.

`verify_evidence_manifest()` recomputes every present artifact's hash and
re-derives the root; any mismatch is reported as an error.

## Schema-version single source of truth

The manifest reads `avera.contracts.versions` to decide whether each artifact's
`schema_version` is supported and what the current version is.

As part of this slice the registry was **reconciled with reality**. Previously it
declared aspirational strings (e.g. `report: "1.0"`) that no code emitted, and it
was imported nowhere. It now matches the actually-emitted versions:

| Artifact | Registry now | Emitted by |
|---|---|---|
| `report` | `avera.assessment.v0.2` | `classify/risk_classifier.py` |
| `graph` | `evidence_graph.v0.3` | `graph/builder.py` |
| `decision` | `avera.decision.v0.2` | `decisions/engine.py` |
| `trend` | `avera.trend_index.v0.1` | `trends/index.py` |
| `traceability` | `avera.traceability_index.v0.1` | `traceability/index.py` |
| `workspace_pack` | `avera.workspace_pack.v0.1` | `pack/export.py` |
| `memory_record` | `avera.memory_record.v0.1` | `memory/ledger.py` |
| `evidence_manifest` | `avera.evidence_manifest.v0.1` | `evidence/manifest.py` |

The registry is now wired into the evidence layer, so it is no longer dead code.

## Public API

```python
from avera.evidence import (
    build_evidence_manifest,   # build from in-memory payloads + on-disk paths
    write_evidence_manifest,   # write deterministic JSON
    verify_evidence_manifest,  # re-verify against artifacts on disk
)
```

## Validation

`avera.contracts.validator.validate_artifact("evidence_manifest", payload)`
checks required fields and field types, consistent with the other stable
artifacts.

## Status and next steps

Implemented:

- Evidence Manifest model, builder, writer, verifier (`src/avera/evidence/`)
- Schema-version registry reconciliation + `evidence_manifest` registration
- Contract validator support
- **Emitted on every standard run** — `avera pack` and `avera demo-refresh` write
  `avera-evidence-manifest.json` (flag `--manifest-out`)
- **Bound into the hash-chained audit log** — `run_pack` appends an
  `evidence_manifest_emitted` record carrying the `integrity_root` (flag
  `--audit-log`)
- **Anchors human sign-off** — see `docs/AVERA_SIGNOFF_WORKFLOW.md`; a sign-off is
  bound to the manifest `integrity_root` and stops validating if the evidence
  changes
- Test suites: `tests/test_evidence_manifest.py`,
  `tests/test_evidence_audit_binding.py`, `tests/test_cli_evidence_manifest.py`

Not yet implemented (next steps, in order):

1. Embed the manifest inside the workspace pack body
2. Cryptographic signing of the root (identity / key material) for the secure
   local-first operating model
