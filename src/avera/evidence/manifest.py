"""Evidence Manifest — the formal binding layer over AVERA's artifact flow.

An Evidence Manifest is a deterministic, content-addressed object that references
every artifact produced for a single analysis run and binds them together with a
single ``integrity_root`` hash. It is the anchor an auditor or reviewer trusts:
if any underlying artifact changes by a single byte, the root changes.

Design contract
---------------
- **Deterministic.** The same artifacts on disk always produce the same manifest
  (modulo ``generated_at_utc``, which is excluded from the integrity root).
- **Content-addressed.** Each referenced artifact carries its SHA-256 file digest.
- **Schema-aware.** Each artifact's ``schema_version`` is checked against the
  central registry (``avera.contracts.versions``) — the single source of truth.
- **Provenance-complete.** Every reference points back to a concrete file path.
- **Non-authoritative.** The manifest is derived; it never replaces the artifacts
  it binds.

The manifest connects the existing flow:

    report -> graph -> traceability -> decision -> trend -> workspace_pack

Usage::

    from avera.evidence import build_evidence_manifest, write_evidence_manifest

    manifest = build_evidence_manifest(
        workspace="fixtures/bms-fast-charge",
        artifacts={
            "report":        (report_dict,        "reports/.../avera-report.json"),
            "graph":         (graph_dict,         "reports/.../avera-evidence-graph.json"),
            "traceability":  (traceability_dict,  "reports/avera-traceability-index.json"),
            "decision":      (decision_dict,      "reports/avera-decision.json"),
            "trend":         (trend_dict,         "reports/avera-trend-index.json"),
            "workspace_pack":(pack_dict,          "reports/avera-workspace-pack.json"),
        },
    )
    write_evidence_manifest(manifest, "reports/avera-evidence-manifest.json")
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from avera.contracts.versions import (
    get_current_version,
    is_supported_version,
)

EVIDENCE_MANIFEST_SCHEMA_VERSION = "avera.evidence_manifest.v0.1"

# The artifact roles the manifest knows how to bind. Order is canonical and is
# preserved in the manifest output for stable diffs.
CANONICAL_ROLES: tuple[str, ...] = (
    "report",
    "graph",
    "traceability",
    "decision",
    "trend",
    "workspace_pack",
)

# Roles required for a manifest to be considered "complete". A manifest can still
# be built from a partial set — completeness is reported, not enforced.
REQUIRED_ROLES: frozenset[str] = frozenset({"report"})

# Map a manifest role to the artifact name used in the version registry.
_ROLE_TO_REGISTRY_NAME: dict[str, str] = {
    "report": "report",
    "graph": "graph",
    "traceability": "traceability",
    "decision": "decision",
    "trend": "trend",
    "workspace_pack": "workspace_pack",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ArtifactRef:
    """A single artifact reference inside an Evidence Manifest."""

    role: str
    path: str
    present: bool
    sha256: str | None
    schema_version: str | None
    schema_supported: bool
    schema_current: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": self.path,
            "present": self.present,
            "sha256": self.sha256,
            "schema_version": self.schema_version,
            "schema_supported": self.schema_supported,
            "schema_current": self.schema_current,
        }


@dataclass(frozen=True)
class EvidenceManifest:
    """A deterministic, content-addressed binding over an AVERA evidence set."""

    schema_version: str
    workspace: dict[str, str]
    generated_at_utc: str
    artifacts: tuple[ArtifactRef, ...]
    integrity_root: str
    completeness: dict[str, Any]
    summary: dict[str, Any]
    provenance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workspace": self.workspace,
            "generated_at_utc": self.generated_at_utc,
            "artifacts": [ref.to_dict() for ref in self.artifacts],
            "integrity_root": self.integrity_root,
            "completeness": self.completeness,
            "summary": self.summary,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class ManifestVerification:
    """Result of re-verifying a manifest against artifacts on disk."""

    ok: bool
    integrity_root_ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_artifacts: int = 0


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_evidence_manifest(
    *,
    workspace: str | Path,
    artifacts: Mapping[str, tuple[dict[str, Any] | None, str | Path | None]],
    tool_version: str = "0.1.0",
    base_dir: str | Path | None = None,
) -> EvidenceManifest:
    """Build an Evidence Manifest binding the supplied artifacts.

    Parameters
    ----------
    workspace:
        Path to the analysed workspace / fixture.
    artifacts:
        Mapping of ``role -> (payload, path)``. ``payload`` is the in-memory
        artifact dict (used to read ``schema_version`` and summary fields);
        ``path`` is the on-disk location used for SHA-256 hashing. Either may be
        ``None`` (e.g. a role that was not produced, or a payload without a file).
    tool_version:
        Version string recorded in provenance.
    base_dir:
        Optional base directory that relative artifact paths are resolved against
        for hashing. Manifest still records the path exactly as supplied.

    Returns
    -------
    EvidenceManifest
    """
    workspace_path = Path(workspace)
    base = Path(base_dir) if base_dir is not None else None

    refs: list[ArtifactRef] = []
    for role in CANONICAL_ROLES:
        if role not in artifacts:
            continue
        payload, path = artifacts[role]
        refs.append(_build_ref(role, payload, path, base))

    integrity_root = _compute_integrity_root(refs)
    completeness = _completeness(refs)
    summary = _summary(artifacts.get("report", (None, None))[0])

    provenance = {
        "tool": "avera",
        "tool_version": tool_version,
        "generator": "avera.evidence.build_evidence_manifest",
        "source_artifacts": {
            ref.role: ref.path for ref in refs if ref.present
        },
    }

    return EvidenceManifest(
        schema_version=EVIDENCE_MANIFEST_SCHEMA_VERSION,
        workspace={"path": str(workspace_path), "name": workspace_path.name},
        generated_at_utc=_now(),
        artifacts=tuple(refs),
        integrity_root=integrity_root,
        completeness=completeness,
        summary=summary,
        provenance=provenance,
    )


def write_evidence_manifest(manifest: EvidenceManifest, path: str | Path) -> Path:
    """Write a manifest as deterministic, pretty-printed JSON."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)
    target.write_text(text + "\n", encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Verifier
# ---------------------------------------------------------------------------

def verify_evidence_manifest(
    manifest: dict[str, Any],
    *,
    base_dir: str | Path | None = None,
) -> ManifestVerification:
    """Re-verify a manifest dict against the artifacts currently on disk.

    Recomputes each present artifact's SHA-256, compares it to the recorded
    value, and re-derives the ``integrity_root``. Any mismatch is an error.
    """
    errors: list[str] = []
    warnings: list[str] = []
    base = Path(base_dir) if base_dir is not None else None

    artifact_entries = manifest.get("artifacts")
    if not isinstance(artifact_entries, list):
        return ManifestVerification(
            ok=False,
            integrity_root_ok=False,
            errors=["manifest 'artifacts' must be a list"],
        )

    recomputed_refs: list[ArtifactRef] = []
    checked = 0
    for entry in artifact_entries:
        if not isinstance(entry, dict):
            errors.append("artifact entry must be an object")
            continue
        role = str(entry.get("role", ""))
        path = str(entry.get("path", ""))
        recorded_hash = entry.get("sha256")
        present_recorded = bool(entry.get("present"))

        resolved = _resolve(path, base)
        exists = resolved.exists() if path else False

        if present_recorded and not exists:
            errors.append(f"{role}: artifact recorded as present is missing on disk: {path}")
        if exists:
            actual_hash = _sha256_file(resolved)
            checked += 1
            if recorded_hash and actual_hash != recorded_hash:
                errors.append(
                    f"{role}: sha256 mismatch — recorded {str(recorded_hash)[:12]}… "
                    f"actual {actual_hash[:12]}…"
                )
            recomputed_refs.append(
                ArtifactRef(
                    role=role,
                    path=path,
                    present=True,
                    sha256=actual_hash,
                    schema_version=entry.get("schema_version"),
                    schema_supported=bool(entry.get("schema_supported")),
                    schema_current=entry.get("schema_current"),
                )
            )
        else:
            recomputed_refs.append(
                ArtifactRef(
                    role=role,
                    path=path,
                    present=False,
                    sha256=None,
                    schema_version=entry.get("schema_version"),
                    schema_supported=bool(entry.get("schema_supported")),
                    schema_current=entry.get("schema_current"),
                )
            )
        if entry.get("schema_supported") is False:
            warnings.append(
                f"{role}: schema_version {entry.get('schema_version')!r} is not in the supported registry"
            )

    recomputed_root = _compute_integrity_root(recomputed_refs)
    recorded_root = str(manifest.get("integrity_root", ""))
    integrity_root_ok = recomputed_root == recorded_root
    if not integrity_root_ok:
        errors.append(
            f"integrity_root mismatch — recorded {recorded_root[:12]}… "
            f"recomputed {recomputed_root[:12]}…"
        )

    return ManifestVerification(
        ok=not errors,
        integrity_root_ok=integrity_root_ok,
        errors=errors,
        warnings=warnings,
        checked_artifacts=checked,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_ref(
    role: str,
    payload: dict[str, Any] | None,
    path: str | Path | None,
    base: Path | None,
) -> ArtifactRef:
    path_str = str(path) if path is not None else ""
    resolved = _resolve(path_str, base) if path_str else None
    exists = bool(resolved and resolved.exists())

    schema_version = None
    if isinstance(payload, dict):
        schema_version = payload.get("schema_version")
    schema_version = str(schema_version) if schema_version is not None else None

    registry_name = _ROLE_TO_REGISTRY_NAME.get(role)
    schema_current = None
    schema_supported = False
    if registry_name is not None:
        try:
            schema_current = get_current_version(registry_name)
        except KeyError:
            schema_current = None
        if schema_version is not None:
            schema_supported = is_supported_version(registry_name, schema_version)

    return ArtifactRef(
        role=role,
        path=path_str,
        present=exists,
        sha256=_sha256_file(resolved) if exists and resolved else None,
        schema_version=schema_version,
        schema_supported=schema_supported,
        schema_current=schema_current,
    )


def _compute_integrity_root(refs: list[ArtifactRef]) -> str:
    """Deterministic root hash over present artifacts.

    Excludes timestamps and absolute paths so the root is stable across machines
    for the same content. Binds (role, sha256, schema_version) for each present
    artifact, sorted by role.
    """
    binding = [
        {
            "role": ref.role,
            "sha256": ref.sha256,
            "schema_version": ref.schema_version,
        }
        for ref in refs
        if ref.present and ref.sha256
    ]
    binding.sort(key=lambda item: item["role"])
    canonical = json.dumps(binding, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _completeness(refs: list[ArtifactRef]) -> dict[str, Any]:
    present_roles = {ref.role for ref in refs if ref.present}
    declared_roles = {ref.role for ref in refs}
    missing_required = sorted(REQUIRED_ROLES - present_roles)
    return {
        "expected_roles": list(CANONICAL_ROLES),
        "present_roles": sorted(present_roles),
        "declared_roles": sorted(declared_roles),
        "present_count": len(present_roles),
        "missing_required": missing_required,
        "complete": not missing_required,
    }


def _summary(report: dict[str, Any] | None) -> dict[str, Any]:
    report = report or {}
    return {
        "verdict": report.get("verdict"),
        "risk": report.get("risk"),
        "confidence": report.get("confidence"),
        "confidence_score": report.get("confidence_score"),
    }


def _resolve(path: str, base: Path | None) -> Path:
    p = Path(path)
    if base is not None and not p.is_absolute():
        return base / p
    return p


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
