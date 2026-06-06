"""Tests for the demo integrity-verification and safe upload-preview helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make avera_demo importable from the demo/ subdirectory.
_demo_dir = Path(__file__).resolve().parents[1] / "demo"
if str(_demo_dir) not in sys.path:
    sys.path.insert(0, str(_demo_dir))

from avera.evidence import build_evidence_manifest, record_manifest_in_audit_log, write_evidence_manifest
from avera_demo.integrity import integrity_panel, verify_audit_chain, verify_manifest_on_disk
from avera_demo.upload import preview_uploaded_evidence


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _bound_set(tmp_path: Path):
    report = {"schema_version": "avera.assessment.v0.2", "verdict": "confirmed_regression",
              "risk": "high", "confidence": "high", "confidence_score": 0.95}
    rp = _write(tmp_path / "avera-report.json", report)
    manifest = build_evidence_manifest(workspace=str(tmp_path), artifacts={"report": (report, str(rp))})
    write_evidence_manifest(manifest, tmp_path / "avera-evidence-manifest.json")
    audit = tmp_path / "avera-audit.jsonl"
    record_manifest_in_audit_log(manifest, audit)
    return manifest, rp, audit


# ---------------------------------------------------------------------------
# Integrity verification
# ---------------------------------------------------------------------------

def test_integrity_panel_passes_for_intact_set(tmp_path: Path):
    manifest, _, audit = _bound_set(tmp_path)
    panel = integrity_panel(manifest.to_dict(), audit)
    assert panel["integrity_root"] == manifest.integrity_root
    assert panel["manifest"]["ok"] is True
    assert panel["audit"]["ok"] is True
    assert panel["audit"]["record_count"] == 1


def test_manifest_verification_fails_after_tamper(tmp_path: Path):
    manifest, report_path, audit = _bound_set(tmp_path)
    report_path.write_text(json.dumps({"schema_version": "avera.assessment.v0.2", "verdict": "x"}), encoding="utf-8")
    m = verify_manifest_on_disk(manifest.to_dict())
    assert m["ok"] is False


def test_audit_chain_verification_detects_tamper(tmp_path: Path):
    _, _, audit = _bound_set(tmp_path)
    # Corrupt the audit line.
    lines = audit.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[0])
    obj["payload"]["integrity_root"] = "0" * 64
    lines[0] = json.dumps(obj, separators=(",", ":"))
    audit.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = verify_audit_chain(audit)
    assert result["present"] is True
    assert result["ok"] is False


def test_missing_artifacts_report_not_present(tmp_path: Path):
    assert verify_audit_chain(tmp_path / "nope.jsonl")["present"] is False
    assert verify_manifest_on_disk(None)["present"] is False


# ---------------------------------------------------------------------------
# Safe upload preview
# ---------------------------------------------------------------------------

def test_upload_preview_parses_verification_json():
    payload = {"runId": "r-1", "stage": "current", "tests": [
        {"id": "T1", "status": "passed"}, {"id": "T2", "status": "failed"}]}
    result = preview_uploaded_evidence("current_results.json", json.dumps(payload).encode())
    assert result["ok"] is True
    assert result["kind"] == "verification_json"
    assert result["preview"]["test_count"] == 2
    assert result["preview"]["statuses"] == {"failed": 1, "passed": 1}


def test_upload_preview_parses_junit_xml():
    xml = b"""<?xml version="1.0"?>
    <testsuite name="suite" tests="2">
      <testcase classname="m" name="t1"/>
      <testcase classname="m" name="t2"><failure message="boom"/></testcase>
    </testsuite>"""
    result = preview_uploaded_evidence("current_results.xml", xml)
    assert result["ok"] is True
    assert result["kind"] == "junit_xml"
    assert result["preview"]["test_count"] == 2


def test_upload_preview_rejects_unsupported_type():
    result = preview_uploaded_evidence("evil.exe", b"\x00\x01")
    assert result["ok"] is False
    assert result["kind"] is None


def test_upload_preview_rejects_malformed_json():
    result = preview_uploaded_evidence("bad.json", b"{ not json")
    assert result["ok"] is False
    assert result["kind"] == "verification_json"


def test_upload_preview_rejects_malformed_xml():
    result = preview_uploaded_evidence("bad.xml", b"<testsuite><bad>")
    assert result["ok"] is False
    assert result["kind"] == "junit_xml"
