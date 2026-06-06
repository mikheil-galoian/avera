"""Formal evidence model for AVERA.

This package defines the Evidence Manifest — a single, content-addressed,
schema-versioned object that binds the existing AVERA artifact flow (report,
evidence graph, traceability index, decision, trend, workspace pack) into one
verifiable evidence set with explicit provenance and an integrity root.

The manifest does not replace any existing artifact. It is a derived, deterministic
"binding" layer that an auditor or reviewer can anchor to: one hash that changes if
any underlying artifact changes.
"""

from .audit_binding import EVIDENCE_MANIFEST_EVENT, record_manifest_in_audit_log
from .manifest import (
    EVIDENCE_MANIFEST_SCHEMA_VERSION,
    ArtifactRef,
    EvidenceManifest,
    ManifestVerification,
    build_evidence_manifest,
    verify_evidence_manifest,
    write_evidence_manifest,
)

__all__ = [
    "EVIDENCE_MANIFEST_SCHEMA_VERSION",
    "EVIDENCE_MANIFEST_EVENT",
    "ArtifactRef",
    "EvidenceManifest",
    "ManifestVerification",
    "build_evidence_manifest",
    "record_manifest_in_audit_log",
    "verify_evidence_manifest",
    "write_evidence_manifest",
]
