# AVERA Sign-off Workflow

**Date:** 6 June 2026
**Status:** Draft v0.1 — implemented
**Module:** `src/avera/signoff/`
**Anchors to:** `docs/AVERA_EVIDENCE_MANIFEST.md`

## Purpose

A sign-off is a **human accountability record** bound to a specific evidence set.
AVERA never approves a release on its own — the gate is deterministic and the
copilot only assists interpretation. A sign-off records a *human* identity, role,
reason, and decision, and binds them to the Evidence Manifest's `integrity_root`.

If the evidence later changes (any bound artifact changes), an existing approval
must **not** silently carry over. The sign-off stops validating.

## State machine

```text
draft ──► reviewed ──► approved
  │            │
  └──► rejected ◄──┘
```

| From | Allowed to |
|---|---|
| `draft` | `reviewed`, `rejected` |
| `reviewed` | `approved`, `rejected` |
| `approved` | — (terminal) |
| `rejected` | — (terminal) |

Invalid transitions raise `SignoffError`.

## Record shape (`avera.signoff.v0.1`)

Every sign-off JSON artifact contains:

| Field | Meaning |
|---|---|
| `schema_version` | `avera.signoff.v0.1` |
| `signoff_id` | unique id |
| `manifest_integrity_root` | the bound evidence root |
| `manifest_path` | on-disk manifest location |
| `workspace` | analysed workspace |
| `state` / `decision` | current state |
| `signer_identity` | who signed the latest transition |
| `signer_role` | their role |
| `reason` | reason for the latest transition |
| `created_at_utc` / `updated_at_utc` | timestamps |
| `history` | immutable list of every transition (state, signer, role, reason, timestamp) |

## Binding & validation

`validate_signoff_against_manifest(signoff, manifest)` returns valid only if:

1. `signoff.manifest_integrity_root == manifest.integrity_root` (the evidence set
   has not changed), **and**
2. the manifest still re-verifies against the artifacts on disk.

If a bound artifact changes, the rebuilt manifest has a new root and the existing
sign-off no longer validates — approval cannot transfer to different evidence.

## Audit-chain binding

Each sign-off can be appended to the SHA-256 hash-chained audit log via
`record_signoff_in_audit_log(record, audit_log_path)`, which writes a
`signoff_recorded` event carrying the `integrity_root`, state, signer identity,
role, and reason. The chain makes the accountability trail tamper-evident.

## Public API

```python
from avera.signoff import (
    create_signoff,                      # -> draft, bound to manifest root
    transition_signoff,                  # draft->reviewed->approved / rejected
    write_signoff, load_signoff,         # JSON artifact persistence
    validate_signoff_against_manifest,   # re-validate against the bound evidence
    record_signoff_in_audit_log,         # append to the hash chain
)
```

## Rules (non-negotiable)

- AVERA never auto-approves; a sign-off always names a human identity and role.
- A sign-off is bound to one `integrity_root`; changed evidence invalidates it.
- The gate stays deterministic; sign-off is a separate human layer.
- The sign-off artifact and its audit events remain inspectable JSON.

## Status & next steps

Implemented: state machine, manifest binding, validation (incl. tamper
detection), JSON persistence, audit-chain binding, tests
(`tests/test_signoff_workflow.py`).

Not yet implemented:
- CLI command surface (`avera signoff create|review|approve|reject`)
- Cryptographic signing of the sign-off (identity/key material)
- Multi-signer quorum policies
