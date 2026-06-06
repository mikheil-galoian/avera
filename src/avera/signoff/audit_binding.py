"""Append sign-off events to the hash-chained audit log.

Each sign-off transition is recorded as one immutable, hash-chained audit record
bound to the evidence manifest's ``integrity_root``. This makes the human
accountability trail tamper-evident and anchored to a specific evidence set.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from avera.audit import AuditLog, AuditRecord

from .workflow import SignoffRecord

SIGNOFF_EVENT = "signoff_recorded"


def record_signoff_in_audit_log(
    signoff: SignoffRecord | dict[str, Any],
    audit_log_path: str | Path,
) -> AuditRecord:
    """Append one immutable record capturing a sign-off state to the chain."""

    data = signoff.to_dict() if isinstance(signoff, SignoffRecord) else dict(signoff)

    workspace = str(data.get("workspace") or "")
    project = Path(workspace).name if workspace else "unknown"

    return AuditLog(audit_log_path).append(
        event=SIGNOFF_EVENT,
        project=project,
        signoff_id=data.get("signoff_id"),
        state=data.get("state"),
        decision=data.get("decision"),
        integrity_root=data.get("manifest_integrity_root"),
        manifest_path=data.get("manifest_path"),
        signer_identity=data.get("signer_identity"),
        signer_role=data.get("signer_role"),
        reason=data.get("reason"),
    )
