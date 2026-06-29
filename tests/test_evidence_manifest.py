"""Tests for the formal Evidence Manifest binding layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from avera.contracts.validator import validate_artifact
from avera.evidence import (
    EVIDENCE_MANIFEST_SCHEMA_VERSION,
    build_evidence_manifest,
    verify_evidence_manifest,
    write_evidence_manifest,
)


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


@pytest.fixture()
def evidence_set(tmp_path: Path):
    """A minimal but realistic on-disk evidence set."""
    report = {
        "schema_version": "avera.assessment.v0.2",
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "confidence_score": 0.95,
    }
    graph = {"schema_version": "evidence_graph.v0.3", "nodes": [], "edges": [], "summary": {}}
    traceability = {"schema_version": "avera.traceability_index.v0.1", "summary": {}}
    decision = {"schema_version": "avera.decision.v0.2", "action": "block"}
    trend = {"schema_version": "avera.trend_index.v0.1", "summary": {}}

    paths = {
        "report": _write(tmp_path / "avera-report.json", report),
        "graph": _write(tmp_path / "avera-evidence-graph.json", graph),
        "traceability": _write(tmp_path / "avera-traceability-index.json", traceability),
        "decision": _write(tmp_path / "avera-decision.json", decision),
        "trend": _write(tmp_path / "avera-trend-index.json", trend),
    }
    payloads = {
        "report": report,
        "graph": graph,
        "traceability": traceability,
        "decision": decision,
        "trend": trend,
    }
    artifacts = {role: (payloads[role], str(paths[role])) for role in paths}
    return tmp_path, artifacts


def test_manifest_has_expected_shape(evidence_set):
    workspace, artifacts = evidence_set
    manifest = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    data = manifest.to_dict()

    assert data["schema_version"] == EVIDENCE_MANIFEST_SCHEMA_VERSION
    assert data["integrity_root"]  # non-empty
    assert data["summary"]["verdict"] == "confirmed_regression"
    assert data["completeness"]["complete"] is True
    assert {ref["role"] for ref in data["artifacts"]} == set(artifacts)


def test_every_present_artifact_is_hashed(evidence_set):
    workspace, artifacts = evidence_set
    manifest = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    for ref in manifest.to_dict()["artifacts"]:
        assert ref["present"] is True
        assert ref["sha256"] and len(ref["sha256"]) == 64
        assert ref["schema_supported"] is True


def test_manifest_is_deterministic_modulo_timestamp(evidence_set):
    workspace, artifacts = evidence_set
    m1 = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    m2 = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    # Integrity root must be identical for identical content.
    assert m1.integrity_root == m2.integrity_root


def test_integrity_root_changes_when_an_artifact_changes(evidence_set):
    workspace, artifacts = evidence_set
    before = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts).integrity_root

    # Mutate the report file on disk.
    report_path = Path(artifacts["report"][1])
    report_path.write_text(json.dumps({"schema_version": "avera.assessment.v0.2", "verdict": "successful_change"}), encoding="utf-8")

    after = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts).integrity_root
    assert before != after


def test_verify_passes_for_untampered_set(evidence_set):
    workspace, artifacts = evidence_set
    manifest = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    result = verify_evidence_manifest(manifest.to_dict())
    assert result.ok is True
    assert result.integrity_root_ok is True
    assert result.checked_artifacts == len(artifacts)


def test_verify_detects_tampering(evidence_set):
    workspace, artifacts = evidence_set
    manifest = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    manifest_dict = manifest.to_dict()

    # Tamper with the decision artifact after the manifest was built.
    decision_path = Path(artifacts["decision"][1])
    decision_path.write_text(json.dumps({"schema_version": "avera.decision.v0.2", "action": "allow"}), encoding="utf-8")

    result = verify_evidence_manifest(manifest_dict)
    assert result.ok is False
    assert result.integrity_root_ok is False
    assert any("sha256 mismatch" in e or "integrity_root mismatch" in e for e in result.errors)


def test_partial_set_reports_incomplete(tmp_path: Path):
    report = {"schema_version": "avera.assessment.v0.2", "verdict": "insufficient_evidence"}
    # No report file on disk -> missing required role.
    artifacts = {"report": (report, None)}
    manifest = build_evidence_manifest(workspace=str(tmp_path), artifacts=artifacts)
    completeness = manifest.to_dict()["completeness"]
    assert completeness["complete"] is False
    assert "report" in completeness["missing_required"]


def test_unknown_schema_version_is_flagged(tmp_path: Path):
    report = {"schema_version": "made.up.v9", "verdict": "successful_change"}
    path = _write(tmp_path / "avera-report.json", report)
    artifacts = {"report": (report, str(path))}
    manifest = build_evidence_manifest(workspace=str(tmp_path), artifacts=artifacts)
    ref = manifest.to_dict()["artifacts"][0]
    assert ref["schema_supported"] is False
    assert ref["schema_current"] == "avera.assessment.v0.2"


def test_manifest_passes_artifact_contract(evidence_set):
    workspace, artifacts = evidence_set
    manifest = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    result = validate_artifact("evidence_manifest", manifest.to_dict())
    assert result.ok is True, result.errors


def test_written_manifest_roundtrips(evidence_set, tmp_path: Path):
    workspace, artifacts = evidence_set
    manifest = build_evidence_manifest(workspace=str(workspace), artifacts=artifacts)
    out = write_evidence_manifest(manifest, tmp_path / "out" / "avera-evidence-manifest.json")
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["integrity_root"] == manifest.integrity_root
    # A written manifest still verifies against the same artifacts.
    result = verify_evidence_manifest(loaded)
    assert result.ok is True


# ---------------------------------------------------------------------------
# Audit regression (#14): integrity_root binds the artifact basename, but not
# the machine-specific absolute directory (keeps cross-machine determinism).
# ---------------------------------------------------------------------------

def test_integrity_root_binds_basename_not_absolute_dir():
    from avera.evidence.manifest import (
        CANONICAL_ROLES,
        ArtifactRef,
        _compute_integrity_root,
    )

    role = CANONICAL_ROLES[0]

    def _ref(path: str) -> ArtifactRef:
        return ArtifactRef(
            role=role, path=path, present=True, sha256="abc123",
            schema_version="v1", schema_supported=True, schema_current="v1",
        )

    # Repointing the recorded path at a DIFFERENT file name changes the root.
    assert _compute_integrity_root([_ref("/x/report.json")]) != _compute_integrity_root(
        [_ref("/x/evil.json")]
    )
    # Same basename + content but a different absolute directory → same root
    # (the root stays machine-independent / deterministic).
    assert _compute_integrity_root([_ref("/a/report.json")]) == _compute_integrity_root(
        [_ref("/b/report.json")]
    )
