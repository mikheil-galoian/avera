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
    EvidencePackRequest,
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
# Evidence pack — full canonical artifact set
# ---------------------------------------------------------------------------

@app.post(
    "/evidence-pack",
    status_code=status.HTTP_200_OK,
    summary="Generate the full canonical AVERA artifact set",
    tags=["analysis"],
    dependencies=[Depends(require_api_key)],
)
def evidence_pack(request: EvidencePackRequest) -> dict[str, Any]:
    """Run the complete deterministic pipeline for a workspace and return the
    full canonical artifact set.

    Unlike ``/analyze/path`` (assessment report only), this returns the verdict,
    the deterministic gate status, the evidence-manifest integrity root, the
    decision summary, and on-disk paths for every canonical artifact (report,
    markdown, evidence graph, traceability, decision, trend, workspace pack,
    evidence manifest, hash-chained audit log).

    HTTP 422 on a missing workspace or required files / unknown policy.
    HTTP 500 on a pipeline error.
    """
    from avera.cli import produce_canonical_artifacts
    from avera.gates import evaluate_gate, load_builtin_policy
    from avera.gates.policy_loader import PolicyError

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

    policy = None
    if request.policy:
        try:
            policy = load_builtin_policy(request.policy)
        except PolicyError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc

    tmp_dir: tempfile.TemporaryDirectory | None = None
    if request.output_path:
        output_dir = Path(request.output_path)
    else:
        tmp_dir = tempfile.TemporaryDirectory(prefix="avera_pack_")
        output_dir = Path(tmp_dir.name)

    try:
        code, paths = produce_canonical_artifacts(project, output_dir)
        if code != 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline failed with exit code {code}",
            )

        report = _read_json_file(paths["report"])
        manifest = _read_json_file(paths["manifest"])
        decision = _read_json_file(paths["decision"])
        gate = evaluate_gate(report, policy=policy)

        persisted = request.output_path is not None
        artifacts_map = {
            key: (str(value) if persisted else value.name) for key, value in paths.items()
        }
        response: dict[str, Any] = {
            "project": request.project,
            "verdict": str(report.get("verdict", "")),
            "risk": str(report.get("risk", "")),
            "confidence": str(report.get("confidence", "")),
            "confidence_score": report.get("confidence_score"),
            "gate_status": gate.status,
            "gate_policy_id": gate.report_summary.get("policy_id"),
            "release_blocked": str(report.get("risk", "")) == "release_blocking",
            "integrity_root": str(manifest.get("integrity_root", "")),
            "artifacts": artifacts_map,
            "artifacts_persisted": persisted,
            "decision": {
                "action": decision.get("action"),
                "category": decision.get("category"),
                "owner": decision.get("owner"),
                "release_recommendation": decision.get("release_recommendation"),
            },
        }
        if request.include_manifest:
            response["manifest"] = manifest
        return response
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


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
