from __future__ import annotations

from pathlib import Path

from avera.pack.export import build_workspace_pack


def test_build_workspace_pack_includes_manifest_and_artifact_paths(tmp_path) -> None:
    report_path = tmp_path / "avera-report.json"
    markdown_path = tmp_path / "avera-report.md"
    graph_path = tmp_path / "avera-evidence-graph.json"
    memory_path = tmp_path / "avera-memory.jsonl"
    traceability_path = tmp_path / "avera-traceability-index.json"
    decision_path = tmp_path / "avera-decision.json"

    for path in (
        report_path,
        markdown_path,
        graph_path,
        memory_path,
        traceability_path,
        decision_path,
    ):
        path.write_text("{}\n", encoding="utf-8")

    pack = build_workspace_pack(
        workspace=tmp_path / "fixture",
        report={
            "schema_version": "avera.assessment.v0.2",
            "verdict": "confirmed_regression",
            "risk": "high",
            "confidence": "high",
            "confidence_score": 0.95,
            "affected_components": ["BMS Thermal Control"],
            "affected_requirements": [{"id": "BMS-REQ-118"}],
            "introduced_failures": [{"test_id": "TC-FAST-01"}],
            "preexisting_failures": [],
        },
        report_path=report_path,
        markdown_path=markdown_path,
        graph={"schema_version": "evidence_graph.v0.3", "summary": {"node_count": 7}},
        graph_path=graph_path,
        memory_records=[
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-28T08:00:00Z",
                "report_path": str(report_path),
                "verdict": "confirmed_regression",
                "risk": "high",
            }
        ],
        memory_path=memory_path,
        traceability={"schema_version": "avera.traceability_index.v0.1", "summary": {"component_count": 1}},
        traceability_path=traceability_path,
        decision={"schema_version": "avera.decision.v0.1", "action": "block", "category": "containment_required", "owner": "validation"},
        decision_path=decision_path,
    )

    assert pack["schema_version"] == "avera.workspace_pack.v0.1"
    assert pack["workspace"]["name"] == "fixture"
    assert pack["summary"]["component_count"] == 1
    assert pack["summary"]["memory_slice_count"] == 1
    assert pack["manifest"]["artifact_count"] == 6
    assert pack["manifest"]["missing_artifacts"] == []
    assert pack["artifacts"]["report_json"]["path"] == str(report_path)
    assert pack["artifacts"]["decision_json"]["path"] == str(decision_path)


def test_build_workspace_pack_handles_optional_artifacts(tmp_path) -> None:
    report_path = tmp_path / "avera-report.json"
    report_path.write_text("{}\n", encoding="utf-8")

    pack = build_workspace_pack(
        workspace=tmp_path / "fixture",
        report={
            "schema_version": "avera.assessment.v0.2",
            "verdict": "successful_change",
            "risk": "low",
            "confidence": "high",
            "confidence_score": 0.91,
            "affected_components": [],
            "affected_requirements": [],
            "introduced_failures": [],
            "preexisting_failures": [],
        },
        report_path=report_path,
    )

    assert pack["manifest"]["artifact_count"] == 1
    assert pack["graph"]["path"] is None
    assert pack["decision"]["action"] is None
    assert pack["memory_slice"] == []
    assert pack["summary"]["missing_artifacts"] == []


def test_build_workspace_pack_stable_memory_slice_filtering(tmp_path) -> None:
    report_path = tmp_path / "avera-report.json"
    report_path.write_text("{}\n", encoding="utf-8")

    records = [
        {
            "record_type": "analysis",
            "timestamp_utc": "2026-04-28T08:02:00Z",
            "report_path": str(report_path),
            "verdict": "confirmed_regression",
            "risk": "high",
        },
        {
            "record_type": "gate",
            "timestamp_utc": "2026-04-28T08:03:00Z",
            "report_path": str(report_path),
            "gate_status": "block",
            "verdict": "confirmed_regression",
            "risk": "high",
        },
        {
            "record_type": "analysis",
            "timestamp_utc": "2026-04-28T08:01:00Z",
            "report_path": str(tmp_path / "other-report.json"),
            "verdict": "successful_change",
            "risk": "low",
        },
    ]

    pack = build_workspace_pack(
        workspace=tmp_path / "fixture",
        report={
            "schema_version": "avera.assessment.v0.2",
            "verdict": "confirmed_regression",
            "risk": "high",
            "confidence": "high",
            "confidence_score": 0.95,
            "affected_components": ["BMS Thermal Control"],
            "affected_requirements": [{"id": "BMS-REQ-118"}],
            "introduced_failures": [{"test_id": "TC-FAST-01"}],
            "preexisting_failures": [],
        },
        report_path=report_path,
        memory_records=records,
    )

    assert [item["record_type"] for item in pack["memory_slice"]] == ["gate", "analysis"]


def test_workspace_pack_is_deterministic_no_wallclock(tmp_path) -> None:
    # Audit regression: the pack is hashed into the evidence integrity_root, so it
    # must be content-addressed — byte-identical inputs must yield a byte-identical
    # pack. A wall-clock export timestamp would leak into the root and make two
    # identical runs produce different roots.
    report_path = tmp_path / "avera-report.json"
    report_path.write_text("{}\n", encoding="utf-8")
    report = {
        "schema_version": "avera.assessment.v0.2",
        "verdict": "successful_change",
        "risk": "low",
        "confidence": "high",
        "confidence_score": 0.9,
        "affected_components": [],
        "affected_requirements": [],
        "introduced_failures": [],
        "preexisting_failures": [],
    }

    def _build():
        return build_workspace_pack(
            workspace=tmp_path / "fixture",
            report=report,
            report_path=report_path,
        )

    pack_a = _build()
    pack_b = _build()

    assert "exported_at_utc" not in pack_a["manifest"]
    assert pack_a == pack_b
