"""Bind an Evidence Manifest into the hash-chained audit log.

This is the seam where the **derived** evidence layer (the manifest and its
``integrity_root``) meets the **immutable** accountability layer (the SHA-256
hash-chained audit log). Recording the integrity root in the chain turns
"an analysis was run" into "this exact, verifiable evidence set was produced",
which is the anchor a regulated sign-off later references.

The manifest stays derived and non-authoritative; the audit log stays immutable.
This module only writes one append-only record linking the two.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from avera.audit import AuditLog, AuditRecord

from .manifest import EvidenceManifest

EVIDENCE_MANIFEST_EVENT = "evidence_manifest_emitted"


def record_manifest_in_audit_log(
    manifest: EvidenceManifest | dict[str, Any],
    audit_log_path: str | Path,
    *,
    manifest_path: str | Path | None = None,
) -> AuditRecord:
    """Append one immutable record binding a manifest's integrity root to the chain.

    Parameters
    ----------
    manifest:
        An ``EvidenceManifest`` or its ``to_dict()`` payload.
    audit_log_path:
        Path to the append-only, hash-chained audit log (JSONL).
    manifest_path:
        Optional on-disk location of the manifest, recorded for provenance.

    Returns
    -------
    AuditRecord
        The appended, hash-chained record.
    """
    data = manifest.to_dict() if isinstance(manifest, EvidenceManifest) else dict(manifest)

    workspace = data.get("workspace") or {}
    project = str(workspace.get("name") or workspace.get("path") or "unknown")
    summary = data.get("summary") or {}
    completeness = data.get("completeness") or {}

    log = AuditLog(audit_log_path)
    return log.append(
        event=EVIDENCE_MANIFEST_EVENT,
        project=project,
        integrity_root=data.get("integrity_root"),
        manifest_schema_version=data.get("schema_version"),
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        verdict=summary.get("verdict"),
        risk=summary.get("risk"),
        confidence=summary.get("confidence"),
        confidence_score=summary.get("confidence_score"),
        complete=completeness.get("complete"),
        present_roles=completeness.get("present_roles"),
    )
