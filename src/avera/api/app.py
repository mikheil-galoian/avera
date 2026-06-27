"""AVERA REST API (LEGACY — DEPRECATED).

DEPRECATED: this is the legacy API and is not the project's entry point.
The canonical API is ``avera_api`` (``src/avera_api/main.py``): the ``avera-api``
console script maps to ``avera_api.main:main`` and the test-suite targets
``avera_api.main``. Nothing imports ``avera.api`` except itself. Prefer
``uvicorn avera_api.main:app``. This module is kept only as a compatibility
stub and is a candidate for removal.

Provides a single ``POST /analyze`` endpoint that accepts paths to an AVERA
evidence pack and returns the structured verdict, risk, confidence, and
evidence.

Historical exit-code contract (this legacy module's own ``--project`` CLI)::

    0  — successful_change or no release_blocking verdict
    1  — confirmed_regression with risk == release_blocking
    2  — analysis error (bad inputs, missing files, etc.)

Usage (server)::

    uvicorn avera.api.app:app --host 0.0.0.0 --port 8000

Usage (one-shot CLI gate)::

    avera-api --project fixtures/bms-fast-charge [--exit-code]

Request body (JSON)::

    {
        "baseline_path":          "fixtures/bms-fast-charge/baseline_results.json",
        "current_path":           "fixtures/bms-fast-charge/current_results.json",
        "requirements_path":      "fixtures/bms-fast-charge/requirements.csv",
        "component_map_path":     "fixtures/bms-fast-charge/component_map.json",
        "change_description_path":"fixtures/bms-fast-charge/change_description.txt"
    }

Response (JSON)::

    {
        "verdict":     "confirmed_regression",
        "risk":        "high",
        "confidence":  "high",
        "confidence_score": 0.95,
        "schema_version": "avera.assessment.v0.2",
        "release_blocked": false,
        "analysis_ms": 42,
        ...
    }
"""

from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# FastAPI is an optional dependency.  The module is importable without it
# (for use as a library); the `create_app()` factory will raise ImportError
# with a helpful message if fastapi is not installed.
# ---------------------------------------------------------------------------

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    FastAPI = None  # type: ignore[misc,assignment]
    BaseModel = object  # type: ignore[misc,assignment]

from avera.core import analyze


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

if _FASTAPI_AVAILABLE:
    class AnalyzeRequest(BaseModel):
        baseline_path: str = Field(..., description="Path to baseline_results.json")
        current_path: str = Field(..., description="Path to current_results.json")
        requirements_path: str = Field(..., description="Path to requirements.csv")
        component_map_path: str = Field(..., description="Path to component_map.json")
        change_description_path: str | None = Field(
            None, description="Optional path to change_description.txt"
        )
        project: str = Field("default", description="Project name for audit log")

    class HealthResponse(BaseModel):
        status: str
        version: str

    class AnalyzeResponse(BaseModel):
        verdict: str
        risk: str
        confidence: str
        confidence_score: float | None
        release_blocked: bool
        analysis_ms: int
        schema_version: str
        project: str
        payload: dict[str, Any]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_app() -> "FastAPI":
    """Construct and return the FastAPI application instance.

    .. deprecated::
        Legacy API. Use the canonical ``avera_api`` package instead
        (``uvicorn avera_api.main:app``).
    """
    warnings.warn(
        "avera.api is the legacy AVERA API and is a candidate for removal; "
        "use the canonical avera_api package (uvicorn avera_api.main:app).",
        DeprecationWarning,
        stacklevel=2,
    )
    if not _FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is required to run the AVERA API. "
            "Install it with: pip install 'avera[api]' or pip install fastapi uvicorn"
        )

    app = FastAPI(
        title="AVERA Analysis API",
        description=(
            "AI-powered change verification for safety-critical systems. "
            "POST /analyze to run an evidence-backed risk assessment."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ── Routes ──────────────────────────────────────────────────────────

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "service": "AVERA Analysis API",
            "analyze": "POST /analyze",
            "docs": "/docs",
        }

    @app.post("/analyze", tags=["analysis"])
    async def analyze_endpoint(req: AnalyzeRequest) -> dict[str, Any]:
        """Run AVERA analysis on the supplied evidence pack.

        Returns the full assessment report including verdict, risk level,
        confidence score, affected components, and threshold evidence.

        Raises HTTP 422 on missing or unreadable input files.
        Raises HTTP 500 on analysis engine errors.
        """
        # Validate paths exist
        paths_to_check = [
            ("baseline_path", req.baseline_path),
            ("current_path", req.current_path),
            ("requirements_path", req.requirements_path),
            ("component_map_path", req.component_map_path),
        ]
        for field_name, path_str in paths_to_check:
            if not Path(path_str).exists():
                raise HTTPException(
                    status_code=422,
                    detail=f"File not found for {field_name!r}: {path_str!r}",
                )

        t0 = time.monotonic()
        try:
            report = analyze(
                baseline_path=req.baseline_path,
                current_path=req.current_path,
                requirements_path=req.requirements_path,
                component_map_path=req.component_map_path,
                change_description_path=req.change_description_path,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Analysis error: {exc}") from exc

        elapsed_ms = int((time.monotonic() - t0) * 1000)

        verdict = str(report.get("verdict", ""))
        risk    = str(report.get("risk", ""))
        release_blocked = (risk == "release_blocking")

        return {
            "verdict": verdict,
            "risk": risk,
            "confidence": str(report.get("confidence", "")),
            "confidence_score": report.get("confidence_score"),
            "release_blocked": release_blocked,
            "analysis_ms": elapsed_ms,
            "schema_version": str(report.get("schema_version", "")),
            "project": req.project,
            "payload": report,
        }

    return app


# ---------------------------------------------------------------------------
# Application singleton (for ``uvicorn avera.api.app:app``)
# ---------------------------------------------------------------------------

app = create_app() if _FASTAPI_AVAILABLE else None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# CLI gate entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI gate: run analysis and exit with code based on risk level.

    Exit codes:
        0  — no release_blocking verdict
        1  — release_blocking
        2  — input/analysis error
    """
    import argparse, json

    parser = argparse.ArgumentParser(
        prog="avera-api",
        description="AVERA one-shot analysis gate (CI/CD integration).",
    )
    parser.add_argument("--project", required=True, help="Path to fixture/project directory")
    parser.add_argument("--baseline",     default=None, help="Override baseline_results.json path")
    parser.add_argument("--current",      default=None, help="Override current_results.json path")
    parser.add_argument("--requirements", default=None, help="Override requirements.csv path")
    parser.add_argument("--component-map",default=None, help="Override component_map.json path")
    parser.add_argument("--json",  action="store_true", help="Print full JSON report to stdout")
    args = parser.parse_args()

    base = Path(args.project)
    bp = Path(args.baseline)     if args.baseline     else base / "baseline_results.json"
    cp = Path(args.current)      if args.current      else base / "current_results.json"
    rp = Path(args.requirements) if args.requirements else base / "requirements.csv"
    mp = Path(args.component_map)if args.component_map else base / "component_map.json"
    dp = base / "change_description.txt"

    for label, p in [("baseline", bp), ("current", cp), ("requirements", rp), ("component_map", mp)]:
        if not p.exists():
            print(f"[avera-api] ERROR: {label} file not found: {p}", file=sys.stderr)
            sys.exit(2)

    try:
        report = analyze(
            baseline_path=bp,
            current_path=cp,
            requirements_path=rp,
            component_map_path=mp,
            change_description_path=dp if dp.exists() else None,
        )
    except Exception as exc:
        print(f"[avera-api] ANALYSIS ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    verdict = report.get("verdict", "unknown")
    risk    = report.get("risk", "unknown")
    conf    = report.get("confidence_score", "?")

    print(f"[avera-api] verdict={verdict}  risk={risk}  confidence={conf}")

    if args.json:
        print(json.dumps(report, indent=2, default=str))

    sys.exit(1 if risk == "release_blocking" else 0)


if __name__ == "__main__":
    main()
