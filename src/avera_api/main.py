"""AVERA FastAPI application.

Exposes two endpoints:

    GET  /health          — liveness probe
    POST /analyze         — run full AVERA analysis, return JSON report

Two analysis modes are supported via separate sub-routes:

    POST /analyze/path    — workspace folder exists on the server filesystem
    POST /analyze/inline  — evidence is supplied inline in the request body
"""

from __future__ import annotations

import csv
import io
import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from avera_api import __version__
from avera_api.auth import require_api_key
from avera_api.models import (
    AnalyzeInlineRequest,
    AnalyzePathRequest,
    AnalyzeResponse,
    HealthResponse,
)

app = FastAPI(
    title="AVERA API",
    description=(
        "AI Change Verification Infrastructure for Safety-Critical Systems. "
        "Analyse automotive engineering evidence and receive structured risk reports."
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    tags=["ops"],
)
def health() -> HealthResponse:
    """Return service health and version."""
    return HealthResponse(status="ok", version=__version__)


# ---------------------------------------------------------------------------
# Analyze — path mode
# ---------------------------------------------------------------------------

@app.post(
    "/analyze/path",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze workspace by filesystem path",
    tags=["analysis"],
    dependencies=[Depends(require_api_key)],
)
def analyze_path(request: AnalyzePathRequest) -> AnalyzeResponse:
    """Run AVERA analysis on a workspace folder that exists on the server.

    The folder must contain:
    - ``requirements.csv``
    - ``component_map.json``
    - ``baseline_results.json``
    - ``current_results.json``
    """
    project = Path(request.project)
    if not project.is_dir():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Project path not found or not a directory: {request.project}",
        )

    missing = [
        f
        for f in ("requirements.csv", "component_map.json", "baseline_results.json", "current_results.json")
        if not (project / f).exists()
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required workspace files: {missing}",
        )

    report = _run_analyze_path(project)
    return AnalyzeResponse(**report)


# ---------------------------------------------------------------------------
# Analyze — inline mode
# ---------------------------------------------------------------------------

@app.post(
    "/analyze/inline",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze evidence supplied inline",
    tags=["analysis"],
    dependencies=[Depends(require_api_key)],
)
def analyze_inline(request: AnalyzeInlineRequest) -> AnalyzeResponse:
    """Run AVERA analysis on evidence supplied directly in the request body.

    No filesystem access is required — useful for CI pipelines and remote
    integrations that cannot share a filesystem with the server.
    """
    with tempfile.TemporaryDirectory(prefix="avera_api_") as tmpdir:
        workspace = Path(tmpdir)

        # Write requirements.csv
        req_lines = [
            "id,component,requirement,metric,operator,threshold,safety_level,next_checks"
        ]
        for r in request.requirements:
            req_lines.append(
                f"{r.id},{r.component},{r.requirement},{r.metric},"
                f"{r.operator},{r.threshold},{r.safety_level},{r.next_checks}"
            )
        (workspace / "requirements.csv").write_text("\n".join(req_lines) + "\n", encoding="utf-8")

        # Write component_map.json
        cmap = {
            path: {"component": e.component, "requirements": e.requirements, "tests": e.tests}
            for path, e in request.component_map.items()
        }
        (workspace / "component_map.json").write_text(
            json.dumps(cmap, indent=2), encoding="utf-8"
        )

        # Write baseline_results.json
        (workspace / "baseline_results.json").write_text(
            json.dumps(request.baseline.model_dump(), indent=2), encoding="utf-8"
        )

        # Write current_results.json
        (workspace / "current_results.json").write_text(
            json.dumps(request.current.model_dump(), indent=2), encoding="utf-8"
        )

        # Optional change_description.txt
        if request.change_description:
            (workspace / "change_description.txt").write_text(
                request.change_description, encoding="utf-8"
            )

        report = _run_analyze_path(workspace)

    return AnalyzeResponse(**report)


# ---------------------------------------------------------------------------
# Shared analysis helper
# ---------------------------------------------------------------------------

def _run_analyze_path(project: Path) -> dict[str, Any]:
    """Call avera.core.analyze() and return the report dict."""
    from avera.core import analyze

    try:
        report = analyze(
            baseline_path=project / "baseline_results.json",
            current_path=project / "current_results.json",
            requirements_path=project / "requirements.csv",
            component_map_path=project / "component_map.json",
            change_description_path=project / "change_description.txt",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        ) from exc

    # Ensure all AnalyzeResponse fields exist with defaults
    report.setdefault("affected_component", None)
    report.setdefault("affected_components", [])
    report.setdefault("affected_requirements", [])
    report.setdefault("changed_files", [])
    report.setdefault("recommendations", [])
    report.setdefault("evidence", {})
    report.setdefault("rules_triggered", [])
    report.setdefault("confidence_factors", [])
    report.setdefault("risk_drivers", [])

    return report
