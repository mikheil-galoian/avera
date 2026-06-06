from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioPaths:
    name: str
    fixture_dir: Path
    report_dir: Path
    traceability_path: Path
    decision_path: Path
    trend_path: Path
    pack_path: Path
    manifest_path: Path
    audit_log_path: Path
    memory_path: Path


@dataclass(frozen=True)
class ArtifactEntry:
    key: str
    label: str
    path: Path
    kind: str
    required: bool = False


@dataclass(frozen=True)
class ScenarioProfile:
    domain: str
    title: str
    summary: str
    use_case: str
    primary_signal: str
    fallback_note: str
    pilot_track: str = "standard"


@dataclass(frozen=True)
class ShellSnapshot:
    scenario: ScenarioPaths
    profile: ScenarioProfile
    report: dict[str, Any] | list[Any] | None
    decision: dict[str, Any] | list[Any] | None
    traceability: dict[str, Any] | list[Any] | None
    trend: dict[str, Any] | list[Any] | None
    workspace_pack: dict[str, Any] | list[Any] | None
    evidence_manifest: dict[str, Any] | list[Any] | None
    audit_log: str | None
    baseline_rows: list[dict[str, Any]]
    current_rows: list[dict[str, Any]]
    signal_rows: list[dict[str, Any]]
    requirements_rows: list[dict[str, Any]]
    change_description: str | None
    artifacts: list[ArtifactEntry]


@dataclass(frozen=True)
class ScenarioSummary:
    verdict: str
    risk: str
    confidence: str
    confidence_score: float | None
    action: str
    artifact_count: int | None
    present_artifacts: int
    missing_artifacts: int
