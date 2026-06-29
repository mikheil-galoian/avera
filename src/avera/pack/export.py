"""Build and write portable workspace packs for AVERA."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from avera.reports.json_report import write_json_report


SCHEMA_VERSION = "avera.workspace_pack.v0.1"


def build_workspace_pack(
    *,
    workspace: str | Path,
    report: dict[str, Any],
    report_path: str | Path,
    markdown_path: str | Path | None = None,
    graph: dict[str, Any] | None = None,
    graph_path: str | Path | None = None,
    memory_records: list[dict[str, Any]] | None = None,
    memory_path: str | Path | None = None,
    traceability: dict[str, Any] | None = None,
    traceability_path: str | Path | None = None,
    decision: dict[str, Any] | None = None,
    decision_path: str | Path | None = None,
    trend: dict[str, Any] | None = None,
    trend_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a portable workspace pack dictionary from existing artifacts."""

    workspace_path = Path(workspace)
    report_file = Path(report_path)
    markdown_file = Path(markdown_path) if markdown_path else None
    graph_file = Path(graph_path) if graph_path else None
    memory_file = Path(memory_path) if memory_path else None
    traceability_file = Path(traceability_path) if traceability_path else None
    decision_file = Path(decision_path) if decision_path else None
    trend_file = Path(trend_path) if trend_path else None

    memory_records = list(memory_records or [])
    memory_slice = _memory_slice(memory_records, report_file)

    artifacts = {
        "report_json": _artifact_meta(report_file),
        "report_markdown": _artifact_meta(markdown_file),
        "graph_json": _artifact_meta(graph_file),
        "memory_jsonl": _artifact_meta(memory_file),
        "traceability_json": _artifact_meta(traceability_file),
        "decision_json": _artifact_meta(decision_file),
        "trend_json": _artifact_meta(trend_file),
    }

    missing_artifacts = sorted(
        name for name, meta in artifacts.items() if meta and meta["exists"] is False
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "workspace": {
            "path": str(workspace_path),
            "name": workspace_path.name,
        },
        "summary": {
            "verdict": report.get("verdict"),
            "risk": report.get("risk"),
            "confidence": report.get("confidence"),
            "confidence_score": report.get("confidence_score"),
            "component_count": len(report.get("affected_components") or []),
            "requirement_count": len(report.get("affected_requirements") or []),
            "introduced_failure_count": len(report.get("introduced_failures") or []),
            "preexisting_failure_count": len(report.get("preexisting_failures") or []),
            "memory_slice_count": len(memory_slice),
            "missing_artifacts": missing_artifacts,
        },
        "artifacts": artifacts,
        "report": {
            "schema_version": report.get("schema_version"),
            "json_path": str(report_file),
            "markdown_path": str(markdown_file) if markdown_file else None,
            "verdict": report.get("verdict"),
            "risk": report.get("risk"),
        },
        "graph": {
            "schema_version": (graph or {}).get("schema_version"),
            "path": str(graph_file) if graph_file else None,
            "summary": (graph or {}).get("summary"),
        },
        "memory_slice": memory_slice,
        "traceability": {
            "schema_version": (traceability or {}).get("schema_version"),
            "path": str(traceability_file) if traceability_file else None,
            "summary": (traceability or {}).get("summary"),
        },
        "decision": {
            "schema_version": (decision or {}).get("schema_version"),
            "path": str(decision_file) if decision_file else None,
            "action": (decision or {}).get("action"),
            "category": (decision or {}).get("category"),
            "owner": (decision or {}).get("owner"),
        },
        "trend": {
            "schema_version": (trend or {}).get("schema_version"),
            "path": str(trend_file) if trend_file else None,
            "summary": (trend or {}).get("summary"),
        },
        "manifest": {
            "schema_version": SCHEMA_VERSION,
            # NOTE: no wall-clock timestamp here. This pack is hashed into the
            # evidence integrity_root, which must stay content-addressed — a
            # per-run timestamp would make byte-identical evidence produce a
            # different root on every run (and across machines).
            "workspace_path": str(workspace_path),
            "source_artifacts": {
                name: meta["path"]
                for name, meta in artifacts.items()
                if meta and meta.get("path")
            },
            "artifact_count": sum(1 for meta in artifacts.values() if meta and meta["exists"]),
            "missing_artifacts": missing_artifacts,
        },
    }


def write_workspace_pack(pack: dict[str, Any], path: str | Path) -> Path:
    """Write a workspace pack as deterministic JSON."""

    return write_json_report(pack, path)


def _memory_slice(memory_records: list[dict[str, Any]], report_path: Path) -> list[dict[str, Any]]:
    report_target = str(report_path)
    selected = [
        record
        for record in memory_records
        if str(record.get("report_path") or "") == report_target
    ]
    if selected:
        return sorted(
            selected,
            key=lambda record: (
                str(record.get("timestamp_utc") or ""),
                str(record.get("record_type") or ""),
            ),
            reverse=True,
        )
    return sorted(
        memory_records,
        key=lambda record: (
            str(record.get("timestamp_utc") or ""),
            str(record.get("record_type") or ""),
        ),
        reverse=True,
    )[:10]


def _artifact_meta(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    exists = path.exists()
    return {
        "path": str(path),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "sha256": _sha256(path) if exists else None,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
