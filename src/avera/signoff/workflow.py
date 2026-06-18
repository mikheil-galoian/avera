"""Sign-off state machine bound to an Evidence Manifest integrity root."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from avera.evidence.manifest import EvidenceManifest, verify_evidence_manifest

SIGNOFF_SCHEMA_VERSION = "avera.signoff.v0.1"

SIGNOFF_STATES: tuple[str, ...] = ("draft", "reviewed", "approved", "rejected")
TERMINAL_STATES: frozenset[str] = frozenset({"approved", "rejected"})

# Allowed state transitions.
VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"reviewed", "rejected"}),
    "reviewed": frozenset({"approved", "rejected"}),
    "approved": frozenset(),
    "rejected": frozenset(),
}


class SignoffError(ValueError):
    """Raised for invalid sign-off construction or transitions."""


@dataclass(frozen=True)
class SignoffEvent:
    """One entry in a sign-off's immutable history."""

    state: str
    signer_identity: str
    signer_role: str
    reason: str
    timestamp_utc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "signer_identity": self.signer_identity,
            "signer_role": self.signer_role,
            "reason": self.reason,
            "timestamp_utc": self.timestamp_utc,
        }


@dataclass(frozen=True)
class SignoffRecord:
    """A sign-off bound to a specific evidence manifest integrity root."""

    schema_version: str
    signoff_id: str
    manifest_integrity_root: str
    manifest_path: str
    workspace: str
    state: str
    created_at_utc: str
    updated_at_utc: str
    history: tuple[SignoffEvent, ...]

    @property
    def latest(self) -> SignoffEvent:
        return self.history[-1]

    @property
    def decision(self) -> str:
        """The current decision == the current state."""
        return self.state

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "signoff_id": self.signoff_id,
            "manifest_integrity_root": self.manifest_integrity_root,
            "manifest_path": self.manifest_path,
            "workspace": self.workspace,
            "state": self.state,
            "decision": self.state,
            "signer_identity": self.latest.signer_identity,
            "signer_role": self.latest.signer_role,
            "reason": self.latest.reason,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "history": [event.to_dict() for event in self.history],
        }


@dataclass(frozen=True)
class SignoffValidation:
    ok: bool
    integrity_root_match: bool
    manifest_intact: bool
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Construction & transitions
# ---------------------------------------------------------------------------

def create_signoff(
    manifest: EvidenceManifest | dict[str, Any],
    *,
    signer_identity: str,
    signer_role: str,
    reason: str = "",
    manifest_path: str | Path | None = None,
    signoff_id: str | None = None,
    timestamp: str | None = None,
) -> SignoffRecord:
    """Create a new sign-off in the ``draft`` state, bound to a manifest root."""

    data = manifest.to_dict() if isinstance(manifest, EvidenceManifest) else dict(manifest)
    integrity_root = str(data.get("integrity_root") or "")
    if not integrity_root:
        raise SignoffError("manifest has no integrity_root to bind the sign-off to")
    if not signer_identity:
        raise SignoffError("signer_identity is required")
    if not signer_role:
        raise SignoffError("signer_role is required")

    workspace = ""
    ws = data.get("workspace")
    if isinstance(ws, dict):
        workspace = str(ws.get("path") or ws.get("name") or "")

    ts = timestamp or _now()
    event = SignoffEvent(
        state="draft",
        signer_identity=signer_identity,
        signer_role=signer_role,
        reason=reason,
        timestamp_utc=ts,
    )
    return SignoffRecord(
        schema_version=SIGNOFF_SCHEMA_VERSION,
        signoff_id=signoff_id or uuid.uuid4().hex,
        manifest_integrity_root=integrity_root,
        manifest_path=str(manifest_path) if manifest_path is not None else "",
        workspace=workspace,
        state="draft",
        created_at_utc=ts,
        updated_at_utc=ts,
        history=(event,),
    )


def transition_signoff(
    record: SignoffRecord,
    to_state: str,
    *,
    signer_identity: str,
    signer_role: str,
    reason: str = "",
    timestamp: str | None = None,
) -> SignoffRecord:
    """Return a new sign-off record advanced to ``to_state``.

    Raises :class:`SignoffError` for invalid transitions.
    """
    if to_state not in SIGNOFF_STATES:
        raise SignoffError(f"unknown sign-off state: {to_state!r}")
    allowed = VALID_TRANSITIONS.get(record.state, frozenset())
    if to_state not in allowed:
        raise SignoffError(
            f"invalid transition: {record.state!r} -> {to_state!r}. "
            f"Allowed from {record.state!r}: {sorted(allowed) or 'none (terminal)'}"
        )
    if not signer_identity or not signer_role:
        raise SignoffError("signer_identity and signer_role are required for a transition")

    ts = timestamp or _now()
    event = SignoffEvent(
        state=to_state,
        signer_identity=signer_identity,
        signer_role=signer_role,
        reason=reason,
        timestamp_utc=ts,
    )
    return SignoffRecord(
        schema_version=record.schema_version,
        signoff_id=record.signoff_id,
        manifest_integrity_root=record.manifest_integrity_root,
        manifest_path=record.manifest_path,
        workspace=record.workspace,
        state=to_state,
        created_at_utc=record.created_at_utc,
        updated_at_utc=ts,
        history=record.history + (event,),
    )


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def write_signoff(record: SignoffRecord, path: str | Path) -> Path:
    """Write a sign-off as deterministic JSON."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)
    target.write_text(text + "\n", encoding="utf-8")
    return target


def load_signoff(path: str | Path) -> dict[str, Any]:
    """Load a sign-off JSON artifact as a dict."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Validation against the bound manifest
# ---------------------------------------------------------------------------

def validate_signoff_against_manifest(
    signoff: dict[str, Any] | SignoffRecord,
    manifest: dict[str, Any] | EvidenceManifest,
    *,
    base_dir: str | Path | None = None,
    verify_artifacts: bool = True,
) -> SignoffValidation:
    """Validate that a sign-off still applies to a manifest.

    The sign-off is valid only if:
    1. its recorded ``manifest_integrity_root`` equals the manifest's
       ``integrity_root`` (the evidence set has not changed), and
    2. (optionally) the manifest still re-verifies against the artifacts on disk.

    If the manifest changed, an existing approval must NOT carry over.
    """
    s = signoff.to_dict() if isinstance(signoff, SignoffRecord) else dict(signoff)
    m = manifest.to_dict() if isinstance(manifest, EvidenceManifest) else dict(manifest)

    errors: list[str] = []

    recorded_root = str(s.get("manifest_integrity_root") or "")
    manifest_root = str(m.get("integrity_root") or "")
    integrity_root_match = bool(recorded_root) and recorded_root == manifest_root
    if not integrity_root_match:
        errors.append(
            f"sign-off integrity root {recorded_root[:12]}… does not match manifest "
            f"{manifest_root[:12]}… — the evidence set changed; sign-off is no longer valid"
        )

    # Fail-closed: skipping artifact verification can never yield a clean pass.
    # Without re-verifying the manifest against disk we cannot trust its declared
    # integrity_root, so an unverified validation is not a valid sign-off.
    if verify_artifacts:
        result = verify_evidence_manifest(m, base_dir=base_dir)
        manifest_intact = result.ok
        if not result.ok:
            errors.extend(f"manifest verification: {e}" for e in result.errors)
    else:
        manifest_intact = False
        errors.append(
            "artifact verification skipped — manifest integrity not confirmed; "
            "sign-off cannot be validated without re-verifying the evidence"
        )

    return SignoffValidation(
        ok=not errors,
        integrity_root_match=integrity_root_match,
        manifest_intact=manifest_intact,
        errors=errors,
    )


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
