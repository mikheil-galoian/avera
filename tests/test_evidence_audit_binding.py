"""Tests for binding the Evidence Manifest into the hash-chained audit log."""

from __future__ import annotations

import json
from pathlib import Path

from avera import cli
from avera.audit import AuditLog
from avera.evidence import (
    EVIDENCE_MANIFEST_EVENT,
    build_evidence_manifest,
    record_manifest_in_audit_log,
)


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _manifest(tmp_path: Path):
    report = {
        "schema_version": "avera.assessment.v0.2",
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "confidence_score": 0.95,
    }
    rp = _write(tmp_path / "avera-report.json", report)
    return build_evidence_manifest(
        workspace=str(tmp_path),
        artifacts={"report": (report, str(rp))},
    )


def test_record_binds_integrity_root_into_chain(tmp_path: Path):
    manifest = _manifest(tmp_path)
    log_path = tmp_path / "avera-audit.jsonl"

    record = record_manifest_in_audit_log(manifest, log_path)

    assert record.event == EVIDENCE_MANIFEST_EVENT
    assert record.payload["integrity_root"] == manifest.integrity_root
    assert record.payload["manifest_schema_version"] == manifest.schema_version
    assert record.payload["verdict"] == "confirmed_regression"

    # The chain verifies.
    log = AuditLog(log_path)
    assert log.verify_chain() == 1


def test_chain_detects_tampering_with_recorded_root(tmp_path: Path):
    manifest = _manifest(tmp_path)
    log_path = tmp_path / "avera-audit.jsonl"
    record_manifest_in_audit_log(manifest, log_path)

    # Tamper with the recorded integrity root inside the audit line.
    lines = log_path.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[0])
    obj["payload"]["integrity_root"] = "0" * 64
    lines[0] = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    log = AuditLog(log_path)
    try:
        log.verify_chain()
        tampering_detected = False
    except Exception:
        tampering_detected = True
    assert tampering_detected, "tampering with the bound root must break the hash chain"


def test_multiple_runs_append_and_chain_stays_valid(tmp_path: Path):
    manifest = _manifest(tmp_path)
    log_path = tmp_path / "avera-audit.jsonl"

    r1 = record_manifest_in_audit_log(manifest, log_path)
    r2 = record_manifest_in_audit_log(manifest, log_path)

    assert r2.prev_hash == r1.self_hash  # chain links run-to-run
    log = AuditLog(log_path)
    assert log.verify_chain() == 2


def test_run_pack_writes_and_chains_audit_record(tmp_path: Path):
    report = {
        "schema_version": "avera.assessment.v0.2",
        "verdict": "successful_change",
        "risk": "low",
        "confidence": "high",
        "confidence_score": 0.9,
    }
    graph = {"schema_version": "evidence_graph.v0.3", "nodes": [], "edges": [], "summary": {}}
    rp = _write(tmp_path / "avera-report.json", report)
    gp = _write(tmp_path / "avera-evidence-graph.json", graph)
    pack_out = tmp_path / "avera-workspace-pack.json"

    code = cli.run_pack(
        workspace=tmp_path,
        report=rp,
        markdown=None,
        graph=gp,
        memory=None,
        traceability=None,
        decision=None,
        trend=None,
        out=pack_out,
    )
    assert code == 0

    audit_path = tmp_path / "avera-audit.jsonl"
    assert audit_path.exists(), "run_pack must bind the manifest into an audit log"

    log = AuditLog(audit_path)
    records = log.read_all()
    assert len(records) == 1
    assert records[0].event == EVIDENCE_MANIFEST_EVENT

    manifest = json.loads((tmp_path / "avera-evidence-manifest.json").read_text(encoding="utf-8"))
    assert records[0].payload["integrity_root"] == manifest["integrity_root"]
    assert log.verify_chain() == 1
