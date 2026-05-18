import json
from types import SimpleNamespace

from avera.memory.ledger import (
    MemoryRecord,
    append_analysis_record,
    append_gate_record,
    load_memory_records,
    summarize_memory,
)


def test_append_analysis_record_writes_normalized_memory_entry(tmp_path, monkeypatch) -> None:
    memory_path = tmp_path / "memory.log"
    monkeypatch.setattr("avera.memory.ledger._now", lambda: "2026-04-23T10:11:12Z")

    record = append_analysis_record(
        memory_path,
        project=tmp_path / "project",
        out=tmp_path / "out",
        report_path=tmp_path / "reports" / "analysis.json",
        graph_path=tmp_path / "reports" / "graph.json",
        report={
            "verdict": "confirmed_regression",
            "risk": "high",
            "confidence": "0.75",
            "confidence_score": "0.75",
            "affected_components": ["BMS Thermal Control", "BMS Thermal Control", "BMS Power"],
            "affected_requirements": [
                {"id": "BMS-REQ-118"},
                {"id": "BMS-REQ-112"},
                {"id": "BMS-REQ-112"},
            ],
            "comparison_summary": {"baseline": 3, "current": 5},
        },
    )

    assert isinstance(record, MemoryRecord)
    assert record.schema_version == "avera.memory_record.v0.1"
    assert record.record_type == "analysis"
    assert record.timestamp_utc == "2026-04-23T10:11:12Z"
    assert record.project_path == str(tmp_path / "project")
    assert record.output_dir == str(tmp_path / "out")
    assert record.report_path == str(tmp_path / "reports" / "analysis.json")
    assert record.evidence_graph_path == str(tmp_path / "reports" / "graph.json")
    assert record.verdict == "confirmed_regression"
    assert record.risk == "high"
    assert record.confidence == "0.75"
    assert record.confidence_score == 0.75
    assert record.affected_components == ["BMS Power", "BMS Thermal Control"]
    assert record.affected_requirements == ["BMS-REQ-112", "BMS-REQ-118"]
    assert record.summary == {"baseline": 3, "current": 5}

    persisted = json.loads(memory_path.read_text(encoding="utf-8").strip())
    assert persisted == {
        "affected_components": ["BMS Power", "BMS Thermal Control"],
        "affected_requirements": ["BMS-REQ-112", "BMS-REQ-118"],
        "confidence": "0.75",
        "confidence_score": 0.75,
        "evidence_graph_path": str(tmp_path / "reports" / "graph.json"),
        "gate_exit_code": None,
        "gate_status": None,
        "output_dir": str(tmp_path / "out"),
        "project_path": str(tmp_path / "project"),
        "reasons": [],
        "record_type": "analysis",
        "report_path": str(tmp_path / "reports" / "analysis.json"),
        "risk": "high",
        "schema_version": "avera.memory_record.v0.1",
        "summary": {"baseline": 3, "current": 5},
        "timestamp_utc": "2026-04-23T10:11:12Z",
        "verdict": "confirmed_regression",
    }


def test_append_gate_record_and_load_records_newest_first(tmp_path, monkeypatch) -> None:
    memory_path = tmp_path / "memory.log"
    monkeypatch.setattr("avera.memory.ledger._now", lambda: "2026-04-23T10:11:12Z")

    append_analysis_record(
        memory_path,
        project=tmp_path / "project",
        out=tmp_path / "out",
        report_path=tmp_path / "reports" / "analysis.json",
        graph_path=tmp_path / "reports" / "graph.json",
        report={"verdict": "confirmed_regression", "risk": "high", "confidence": "high"},
    )

    decision = SimpleNamespace(
        status="blocked",
        exit_code=2,
        reasons=["missing evidence", "policy check failed", "missing evidence"],
        report_summary={
            "verdict": "confirmed_regression",
            "risk": "high",
            "confidence": "high",
            "confidence_score": 0.92,
        },
    )
    append_gate_record(memory_path, report_path=tmp_path / "reports" / "gate.json", decision=decision)

    memory_path.write_text(
        memory_path.read_text(encoding="utf-8") + "\nnot-json\n",
        encoding="utf-8",
    )

    records = load_memory_records(memory_path)
    assert [record["record_type"] for record in records] == ["gate", "analysis"]
    assert records[0]["gate_status"] == "blocked"
    assert records[0]["gate_exit_code"] == 2
    assert records[0]["reasons"] == ["missing evidence", "policy check failed"]
    assert records[0]["summary"] == {
        "confidence": "high",
        "confidence_score": 0.92,
        "risk": "high",
        "verdict": "confirmed_regression",
    }
    assert records[1]["record_type"] == "analysis"

    limited = load_memory_records(memory_path, limit=1)
    assert len(limited) == 1
    assert limited[0]["record_type"] == "gate"


def test_summarize_memory_counts_record_shapes(tmp_path, monkeypatch) -> None:
    memory_path = tmp_path / "memory.log"
    monkeypatch.setattr("avera.memory.ledger._now", lambda: "2026-04-23T10:11:12Z")

    append_analysis_record(
        memory_path,
        project=tmp_path / "project-a",
        out=tmp_path / "out-a",
        report_path=tmp_path / "reports" / "analysis-a.json",
        graph_path=tmp_path / "reports" / "graph-a.json",
        report={"verdict": "confirmed_regression", "risk": "high", "confidence": "high"},
    )
    append_analysis_record(
        memory_path,
        project=tmp_path / "project-b",
        out=tmp_path / "out-b",
        report_path=tmp_path / "reports" / "analysis-b.json",
        graph_path=tmp_path / "reports" / "graph-b.json",
        report={"verdict": "environment_failure", "risk": "unknown", "confidence": "low"},
    )
    append_gate_record(
        memory_path,
        report_path=tmp_path / "reports" / "gate.json",
        decision=SimpleNamespace(
            status="allowed",
            exit_code=0,
            reasons=[],
            report_summary={"verdict": "successful_change", "risk": "low", "confidence": "high"},
        ),
    )

    summary = summarize_memory(load_memory_records(memory_path))

    assert summary == {
        "total_records": 3,
        "by_type": {"analysis": 2, "gate": 1},
        "by_verdict": {
            "confirmed_regression": 1,
            "environment_failure": 1,
            "successful_change": 1,
        },
        "by_risk": {"high": 1, "low": 1, "unknown": 1},
        "by_gate_status": {"allowed": 1, "none": 2},
    }
