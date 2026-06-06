"""Truthful evidence-integrity helpers for the demo preview.

These are pure functions (no Streamlit) so they can be unit-tested. They give the
demo a *truthful* integrity panel: the Evidence Manifest is re-verified against
the artifacts on disk, and the audit log's hash chain is actually checked — the
demo never just claims integrity, it demonstrates it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from avera.audit import AuditLog, ChainIntegrityError
from avera.evidence import verify_evidence_manifest


def verify_audit_chain(audit_log_path: str | Path) -> dict[str, Any]:
    """Verify the hash-chained audit log on disk."""

    path = Path(audit_log_path)
    if not path.exists():
        return {"present": False, "ok": None, "record_count": 0, "error": None}
    log = AuditLog(path)
    try:
        count = log.verify_chain()
        return {"present": True, "ok": True, "record_count": count, "error": None}
    except ChainIntegrityError as exc:
        try:
            count = len(log.read_all())
        except Exception:
            count = 0
        return {"present": True, "ok": False, "record_count": count, "error": str(exc)}


def verify_manifest_on_disk(
    manifest: dict[str, Any] | None, *, base_dir: str | Path | None = None
) -> dict[str, Any]:
    """Re-verify an evidence manifest against the artifacts it binds."""

    if not isinstance(manifest, dict) or not manifest:
        return {"present": False, "ok": None, "integrity_root_ok": None, "checked_artifacts": 0, "errors": []}
    result = verify_evidence_manifest(manifest, base_dir=base_dir)
    return {
        "present": True,
        "ok": result.ok,
        "integrity_root_ok": result.integrity_root_ok,
        "checked_artifacts": result.checked_artifacts,
        "errors": list(result.errors),
    }


def integrity_panel(
    manifest: dict[str, Any] | None,
    audit_log_path: str | Path,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Return a combined, truthful integrity summary for the demo."""

    integrity_root = ""
    if isinstance(manifest, dict):
        integrity_root = str(manifest.get("integrity_root") or "")
    return {
        "integrity_root": integrity_root,
        "manifest": verify_manifest_on_disk(manifest, base_dir=base_dir),
        "audit": verify_audit_chain(audit_log_path),
    }
