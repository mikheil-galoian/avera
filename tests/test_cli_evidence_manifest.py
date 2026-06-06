"""Integration test: `avera pack` emits an Evidence Manifest as a runtime artifact."""

from __future__ import annotations

import json
from pathlib import Path

from avera import cli
from avera.contracts.validator import validate_artifact
from avera.evidence import verify_evidence_manifest


def _write(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _seed_artifacts(base: Path) -> dict[str, Path]:
    report = {
        "schema_version": "avera.assessment.v0.2",
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "confidence_score": 0.95,
        "affected_components": ["BMS Thermal Control"],
        "affected_requirements": [{"id": "BMS-REQ-112"}],
        "introduced_failures": [],
        "preexisting_failures": [],
    }
    graph = {"schema_version": "evidence_graph.v0.3", "nodes": [], "edges": [], "summary": {}}
    traceability = {"schema_version": "avera.traceability_index.v0.1", "summary": {}}
    decision = {"schema_version": "avera.decision.v0.2", "action": "block"}
    trend = {"schema_version": "avera.trend_index.v0.1", "summary": {}}
    return {
        "report": _write(base / "avera-report.json", report),
        "graph": _write(base / "avera-evidence-graph.json", graph),
        "traceability": _write(base / "avera-traceability-index.json", traceability),
        "decision": _write(base / "avera-decision.json", decision),
        "trend": _write(base / "avera-trend-index.json", trend),
    }


def test_run_pack_emits_manifest_next_to_pack_by_default(tmp_path: Path):
    paths = _seed_artifacts(tmp_path)
    pack_out = tmp_path / "avera-workspace-pack.json"

    code = cli.run_pack(
        workspace=tmp_path,
        report=paths["report"],
        markdown=None,
        graph=paths["graph"],
        memory=None,
        traceability=paths["traceability"],
        decision=paths["decision"],
        trend=paths["trend"],
        out=pack_out,
    )
    assert code == 0

    manifest_path = tmp_path / "avera-evidence-manifest.json"
    assert manifest_path.exists(), "manifest must be emitted next to the workspace pack by default"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Contract holds.
    assert validate_artifact("evidence_manifest", manifest).ok is True
    # Re-verifies against the artifacts on disk, including the workspace pack.
    result = verify_evidence_manifest(manifest)
    assert result.ok is True
    assert result.integrity_root_ok is True
    # The workspace pack itself is bound into the manifest.
    roles = {a["role"] for a in manifest["artifacts"] if a["present"]}
    assert "workspace_pack" in roles
    assert manifest["summary"]["verdict"] == "confirmed_regression"


def test_run_pack_honours_explicit_manifest_out(tmp_path: Path):
    paths = _seed_artifacts(tmp_path)
    pack_out = tmp_path / "avera-workspace-pack.json"
    manifest_out = tmp_path / "custom" / "manifest.json"

    code = cli.run_pack(
        workspace=tmp_path,
        report=paths["report"],
        markdown=None,
        graph=paths["graph"],
        memory=None,
        traceability=paths["traceability"],
        decision=paths["decision"],
        trend=paths["trend"],
        out=pack_out,
        manifest_out=manifest_out,
    )
    assert code == 0
    assert manifest_out.exists()
    assert not (tmp_path / "avera-evidence-manifest.json").exists()
