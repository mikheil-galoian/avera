"""Tests for the sign-off workflow bound to evidence manifest integrity roots."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from avera.audit import AuditLog
from avera.evidence import build_evidence_manifest
from avera.signoff import (
    SIGNOFF_EVENT,
    SignoffError,
    create_signoff,
    load_signoff,
    record_signoff_in_audit_log,
    transition_signoff,
    validate_signoff_against_manifest,
    write_signoff,
)


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _manifest(tmp_path: Path, verdict="confirmed_regression"):
    report = {
        "schema_version": "avera.assessment.v0.2",
        "verdict": verdict,
        "risk": "high",
        "confidence": "high",
        "confidence_score": 0.95,
    }
    rp = _write(tmp_path / "avera-report.json", report)
    return build_evidence_manifest(
        workspace=str(tmp_path),
        artifacts={"report": (report, str(rp))},
    ), rp


# ---------------------------------------------------------------------------
# Construction and state machine
# ---------------------------------------------------------------------------

def test_create_signoff_starts_in_draft_bound_to_root(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    s = create_signoff(
        manifest,
        signer_identity="eng@acme.com",
        signer_role="validation_lead",
        reason="initial review",
        manifest_path="avera-evidence-manifest.json",
    )
    assert s.state == "draft"
    assert s.manifest_integrity_root == manifest.integrity_root
    assert s.to_dict()["signer_identity"] == "eng@acme.com"
    assert s.to_dict()["signer_role"] == "validation_lead"


def test_valid_transition_path_draft_reviewed_approved(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")
    s = transition_signoff(s, "reviewed", signer_identity="b@x", signer_role="reviewer")
    assert s.state == "reviewed"
    s = transition_signoff(s, "approved", signer_identity="c@x", signer_role="release_manager", reason="ok")
    assert s.state == "approved"
    assert s.decision == "approved"
    assert len(s.history) == 3


def test_invalid_transition_draft_to_approved_raises(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")
    with pytest.raises(SignoffError):
        transition_signoff(s, "approved", signer_identity="a@x", signer_role="eng")


def test_terminal_state_cannot_transition(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")
    s = transition_signoff(s, "rejected", signer_identity="b@x", signer_role="reviewer", reason="bad")
    assert s.state == "rejected"
    with pytest.raises(SignoffError):
        transition_signoff(s, "approved", signer_identity="b@x", signer_role="reviewer")


def test_missing_signer_identity_raises(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    with pytest.raises(SignoffError):
        create_signoff(manifest, signer_identity="", signer_role="eng")


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_write_and_load_roundtrip(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")
    out = write_signoff(s, tmp_path / "signoff.json")
    assert out.exists()
    loaded = load_signoff(out)
    assert loaded["manifest_integrity_root"] == manifest.integrity_root
    assert loaded["state"] == "draft"


# ---------------------------------------------------------------------------
# Validation against the bound manifest (the core guarantee)
# ---------------------------------------------------------------------------

def test_signoff_validates_against_unchanged_manifest(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")
    s = transition_signoff(s, "reviewed", signer_identity="b@x", signer_role="rev")
    s = transition_signoff(s, "approved", signer_identity="c@x", signer_role="rm")

    result = validate_signoff_against_manifest(s, manifest)
    assert result.ok is True
    assert result.integrity_root_match is True
    assert result.manifest_intact is True


def test_signoff_no_longer_validates_when_manifest_changes(tmp_path: Path):
    """If a bound artifact changes, the rebuilt manifest has a new root and the
    existing approval must NOT carry over."""
    manifest, report_path = _manifest(tmp_path, verdict="confirmed_regression")
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")
    s = transition_signoff(s, "reviewed", signer_identity="b@x", signer_role="rev")
    s = transition_signoff(s, "approved", signer_identity="c@x", signer_role="rm")

    # Tamper: change the report on disk and rebuild the manifest.
    report_path.write_text(
        json.dumps({"schema_version": "avera.assessment.v0.2", "verdict": "successful_change"}),
        encoding="utf-8",
    )
    changed_manifest = build_evidence_manifest(
        workspace=str(tmp_path),
        artifacts={"report": ({"schema_version": "avera.assessment.v0.2", "verdict": "successful_change"}, str(report_path))},
    )

    assert changed_manifest.integrity_root != manifest.integrity_root
    result = validate_signoff_against_manifest(s, changed_manifest)
    assert result.ok is False
    assert result.integrity_root_match is False


def test_signoff_detects_artifact_tamper_even_with_same_recorded_root(tmp_path: Path):
    """If the manifest dict still claims the old root but the artifact on disk
    changed, manifest verification fails and the sign-off is invalid."""
    manifest, report_path = _manifest(tmp_path)
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")

    manifest_dict = manifest.to_dict()  # keeps the original recorded root
    report_path.write_text(json.dumps({"schema_version": "avera.assessment.v0.2", "verdict": "x"}), encoding="utf-8")

    result = validate_signoff_against_manifest(s, manifest_dict)
    assert result.ok is False
    assert result.manifest_intact is False


# ---------------------------------------------------------------------------
# Audit-chain binding
# ---------------------------------------------------------------------------

def test_signoff_appends_to_hash_chained_audit_log(tmp_path: Path):
    manifest, _ = _manifest(tmp_path)
    s = create_signoff(manifest, signer_identity="a@x", signer_role="eng")
    s = transition_signoff(s, "reviewed", signer_identity="b@x", signer_role="rev")

    log_path = tmp_path / "avera-audit.jsonl"
    rec1 = record_signoff_in_audit_log(create_signoff(manifest, signer_identity="a@x", signer_role="eng"), log_path)
    rec2 = record_signoff_in_audit_log(s, log_path)

    assert rec1.event == SIGNOFF_EVENT
    assert rec2.payload["integrity_root"] == manifest.integrity_root
    assert rec2.payload["state"] == "reviewed"
    assert rec2.prev_hash == rec1.self_hash

    log = AuditLog(log_path)
    assert log.verify_chain() == 2
