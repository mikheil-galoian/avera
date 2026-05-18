"""Tests for the AVERA FastAPI REST wrapper.

Requires: pip install fastapi httpx
Tests run without a real server — FastAPI TestClient is used.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Skip the entire module if fastapi / httpx are not installed
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from avera_api.main import app  # noqa: E402

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_payload(self):
        r = client.get("/health")
        body = r.json()
        assert body["status"] == "ok"
        assert "version" in body


# ---------------------------------------------------------------------------
# /analyze/path — happy path
# ---------------------------------------------------------------------------

BMS_FIXTURE = Path("fixtures/bms-fast-charge")


@pytest.mark.skipif(
    not BMS_FIXTURE.exists(),
    reason="bms-fast-charge fixture not present",
)
class TestAnalyzePath:
    def test_returns_200(self):
        r = client.post("/analyze/path", json={"project": str(BMS_FIXTURE)})
        assert r.status_code == 200

    def test_verdict_present(self):
        r = client.post("/analyze/path", json={"project": str(BMS_FIXTURE)})
        body = r.json()
        assert "verdict" in body
        assert body["verdict"]

    def test_confirmed_regression(self):
        r = client.post("/analyze/path", json={"project": str(BMS_FIXTURE)})
        body = r.json()
        assert body["verdict"] == "confirmed_regression"

    def test_risk_field(self):
        r = client.post("/analyze/path", json={"project": str(BMS_FIXTURE)})
        body = r.json()
        assert body["risk"] in ("low", "medium", "high", "release_blocking", "unknown")

    def test_confidence_score_float(self):
        r = client.post("/analyze/path", json={"project": str(BMS_FIXTURE)})
        body = r.json()
        assert isinstance(body["confidence_score"], float)

    def test_schema_version_present(self):
        r = client.post("/analyze/path", json={"project": str(BMS_FIXTURE)})
        body = r.json()
        assert "schema_version" in body


# ---------------------------------------------------------------------------
# /analyze/path — error cases
# ---------------------------------------------------------------------------

class TestAnalyzePathErrors:
    def test_missing_directory_returns_422(self):
        r = client.post("/analyze/path", json={"project": "/nonexistent/path/to/fixture"})
        assert r.status_code == 422

    def test_empty_project_field_returns_422(self):
        r = client.post("/analyze/path", json={})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# /analyze/inline — happy path
# ---------------------------------------------------------------------------

_INLINE_PAYLOAD = {
    "requirements": [
        {
            "id": "BMS-REQ-112",
            "component": "BMS Thermal Control",
            "requirement": "Maximum cell temperature must not exceed 50 C",
            "metric": "max_cell_temp_c",
            "operator": "<=",
            "threshold": 50.0,
            "safety_level": "high",
            "next_checks": "BMS-HIL-FASTCHARGE-07",
        }
    ],
    "component_map": {
        "src/bms/thermal_manager.c": {
            "component": "BMS Thermal Control",
            "requirements": ["BMS-REQ-112"],
            "tests": ["BMS-SIL-FASTCHARGE-01"],
        }
    },
    "baseline": {
        "runId": "baseline-001",
        "stage": "sil",
        "changedFiles": [],
        "tests": [
            {
                "id": "BMS-SIL-FASTCHARGE-01",
                "component": "BMS Thermal Control",
                "status": "passed",
                "metrics": {"max_cell_temp_c": 47.1},
            }
        ],
    },
    "current": {
        "runId": "current-001",
        "stage": "sil",
        "changedFiles": ["src/bms/thermal_manager.c"],
        "tests": [
            {
                "id": "BMS-SIL-FASTCHARGE-01",
                "component": "BMS Thermal Control",
                "status": "failed",
                "metrics": {"max_cell_temp_c": 52.8},
                "evidence": "Temperature exceeded threshold after cooling logic change.",
            }
        ],
    },
    "change_description": "Cooling ramp logic update in thermal_manager.c.",
}


class TestAnalyzeInline:
    def test_returns_200(self):
        r = client.post("/analyze/inline", json=_INLINE_PAYLOAD)
        assert r.status_code == 200

    def test_verdict_confirmed_regression(self):
        r = client.post("/analyze/inline", json=_INLINE_PAYLOAD)
        body = r.json()
        assert body["verdict"] == "confirmed_regression"

    def test_risk_high(self):
        r = client.post("/analyze/inline", json=_INLINE_PAYLOAD)
        body = r.json()
        assert body["risk"] == "high"

    def test_confidence_score_range(self):
        r = client.post("/analyze/inline", json=_INLINE_PAYLOAD)
        body = r.json()
        assert 0.0 <= body["confidence_score"] <= 1.0

    def test_affected_component_present(self):
        r = client.post("/analyze/inline", json=_INLINE_PAYLOAD)
        body = r.json()
        assert "BMS Thermal Control" in body["affected_components"]

    def test_schema_version_present(self):
        r = client.post("/analyze/inline", json=_INLINE_PAYLOAD)
        body = r.json()
        assert body["schema_version"].startswith("avera.")

    def test_change_description_echoed(self):
        r = client.post("/analyze/inline", json=_INLINE_PAYLOAD)
        body = r.json()
        assert body.get("change_description") == "Cooling ramp logic update in thermal_manager.c."

    def test_successful_change_inline(self):
        payload = json.loads(json.dumps(_INLINE_PAYLOAD))
        payload["current"]["tests"][0]["status"] = "passed"
        payload["current"]["tests"][0]["metrics"] = {"max_cell_temp_c": 45.0}
        r = client.post("/analyze/inline", json=payload)
        body = r.json()
        assert body["verdict"] == "successful_change"


# ---------------------------------------------------------------------------
# /analyze/inline — error cases
# ---------------------------------------------------------------------------

class TestAnalyzeInlineErrors:
    def test_missing_body_returns_422(self):
        r = client.post("/analyze/inline", json={})
        assert r.status_code == 422

    def test_missing_requirements_returns_422(self):
        payload = {k: v for k, v in _INLINE_PAYLOAD.items() if k != "requirements"}
        r = client.post("/analyze/inline", json=payload)
        assert r.status_code == 422

    def test_missing_baseline_returns_422(self):
        payload = {k: v for k, v in _INLINE_PAYLOAD.items() if k != "baseline"}
        r = client.post("/analyze/inline", json=payload)
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# OpenAPI schema
# ---------------------------------------------------------------------------

class TestOpenAPISchema:
    def test_openapi_json_served(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200

    def test_openapi_has_analyze_paths(self):
        r = client.get("/openapi.json")
        paths = r.json()["paths"]
        assert "/analyze/path" in paths
        assert "/analyze/inline" in paths
        assert "/health" in paths


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuthentication:
    """Verify API key enforcement on protected endpoints."""

    SECRET = "test-secret-key-avera"

    def test_health_always_public(self, monkeypatch):
        """GET /health must return 200 regardless of auth state."""
        monkeypatch.setenv("AVERA_API_KEY", self.SECRET)
        r = client.get("/health")
        assert r.status_code == 200

    def test_analyze_path_blocked_without_key(self, monkeypatch):
        """POST /analyze/path returns 401 when key is set but header is missing."""
        monkeypatch.setenv("AVERA_API_KEY", self.SECRET)
        r = client.post("/analyze/path", json={"project": "fixtures/bms-fast-charge"})
        assert r.status_code == 401

    def test_analyze_inline_blocked_without_key(self, monkeypatch):
        """POST /analyze/inline returns 401 when key is set but header is missing."""
        monkeypatch.setenv("AVERA_API_KEY", self.SECRET)
        r = client.post("/analyze/inline", json={})
        assert r.status_code == 401

    def test_analyze_path_accepts_x_api_key_header(self, monkeypatch):
        """Correct key via X-API-Key header grants access (gets past auth → 422 from business logic)."""
        monkeypatch.setenv("AVERA_API_KEY", self.SECRET)
        r = client.post(
            "/analyze/path",
            json={"project": "/nonexistent"},
            headers={"X-API-Key": self.SECRET},
        )
        # Auth passed — business logic rejects nonexistent path with 422
        assert r.status_code == 422

    def test_analyze_path_accepts_bearer_token(self, monkeypatch):
        """Correct key via Authorization: Bearer header grants access."""
        monkeypatch.setenv("AVERA_API_KEY", self.SECRET)
        r = client.post(
            "/analyze/path",
            json={"project": "/nonexistent"},
            headers={"Authorization": f"Bearer {self.SECRET}"},
        )
        assert r.status_code == 422  # auth passed, path not found

    def test_wrong_key_returns_401(self, monkeypatch):
        """Wrong key returns 401."""
        monkeypatch.setenv("AVERA_API_KEY", self.SECRET)
        r = client.post(
            "/analyze/path",
            json={"project": "fixtures/bms-fast-charge"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert r.status_code == 401

    def test_401_response_has_detail(self, monkeypatch):
        """401 response body contains a human-readable detail message."""
        monkeypatch.setenv("AVERA_API_KEY", self.SECRET)
        r = client.post("/analyze/path", json={"project": "fixtures/bms-fast-charge"})
        assert "detail" in r.json()

    def test_open_mode_when_key_not_set(self, monkeypatch):
        """When AVERA_API_KEY is not set, requests pass without any key."""
        monkeypatch.delenv("AVERA_API_KEY", raising=False)
        r = client.post(
            "/analyze/path",
            json={"project": "/nonexistent"},
        )
        # No auth header, no key set → open mode → reaches business logic → 422
        assert r.status_code == 422

    def test_token_rotation_both_keys_accepted(self, monkeypatch):
        """Comma-separated AVERA_API_KEY accepts all listed tokens."""
        old_key = "old-token"
        new_key = "new-token"
        monkeypatch.setenv("AVERA_API_KEY", f"{new_key},{old_key}")

        for key in (new_key, old_key):
            r = client.post(
                "/analyze/path",
                json={"project": "/nonexistent"},
                headers={"X-API-Key": key},
            )
            assert r.status_code == 422, f"Token '{key}' should be accepted"

    def test_token_rotation_revoked_key_rejected(self, monkeypatch):
        """A token not in the list is rejected even during rotation."""
        monkeypatch.setenv("AVERA_API_KEY", "new-token,old-token")
        r = client.post(
            "/analyze/path",
            json={"project": "fixtures/bms-fast-charge"},
            headers={"X-API-Key": "revoked-token"},
        )
        assert r.status_code == 401
