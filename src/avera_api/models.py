"""Pydantic request / response models for the AVERA REST API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AnalyzePathRequest(BaseModel):
    """Analyze a workspace that already exists on the server's filesystem."""

    project: str = Field(
        ...,
        description="Absolute path to an AVERA workspace folder containing "
                    "requirements.csv, component_map.json, baseline_results.json, "
                    "current_results.json.",
        examples=["fixtures/bms-fast-charge"],
    )


class TestResult(BaseModel):
    """A single verification test result."""

    id: str
    component: str
    status: str  # passed | failed | error | inconclusive
    metrics: dict[str, float] = Field(default_factory=dict)
    evidence: str | None = None


class VerificationRun(BaseModel):
    """A full verification run (baseline or current)."""

    runId: str
    stage: str = "verification"
    changedFiles: list[str] = Field(default_factory=list)
    tests: list[TestResult]


class RequirementRow(BaseModel):
    """One row of the requirements catalogue."""

    id: str
    component: str
    requirement: str
    metric: str
    operator: str
    threshold: float
    safety_level: str
    next_checks: str = ""


class ComponentEntry(BaseModel):
    """One entry in the component map (keyed by source file path)."""

    component: str
    requirements: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)


class AnalyzeInlineRequest(BaseModel):
    """Analyze evidence supplied inline — no filesystem access required."""

    requirements: list[RequirementRow]
    component_map: dict[str, ComponentEntry]
    baseline: VerificationRun
    current: VerificationRun
    change_description: str | None = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    """The full AVERA analysis report."""

    schema_version: str
    verdict: str
    risk: str
    confidence: str
    confidence_score: float
    affected_component: str | None
    affected_components: list[str]
    affected_requirements: list[str]
    changed_files: list[str]
    recommendations: list[str]
    evidence: dict[str, Any]
    evidence_summary: list[str] | None = None
    comparison_summary: dict[str, Any] | None = None
    rules_triggered: list[str] = Field(default_factory=list)
    confidence_factors: list[str] = Field(default_factory=list)
    risk_drivers: list[str] = Field(default_factory=list)
    change_description: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
