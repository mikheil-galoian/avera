"""Tests for the deployed API's /evidence-pack endpoint (avera_api.main).

Skipped automatically when fastapi / httpx are not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from avera_api.main import app  # noqa: E402

client = TestClient(app)

BMS = Path("fixtures/bms-fast-charge")

CANONICAL_KEYS = {
    "report", "markdown", "graph", "traceability", "decision",
    "trend", "workspace_pack", "manifest", "audit_log", "memory",
}


@pytest.mark.skipif(not BMS.exists(), reason="bms-fast-charge fixture not present")
class TestEvidencePackHappyPath:
    def test_returns_200(self):
        r = client.post("/evidence-pack", json={"project": str(BMS)})
        assert r.status_code == 200

    def test_response_shape(self):
        r = client.post("/evidence-pack", json={"project": str(BMS)})
        body = r.json()
        for key in ("verdict", "risk", "confidence", "gate_status", "integrity_root", "artifacts", "decision"):
            assert key in body, f"missing field: {key}"
        assert body["verdict"] == "confirmed_regression"
        assert body["gate_status"] in {"pass", "review", "block"}
        assert len(body["integrity_root"]) == 64
        assert set(body["artifacts"]) == CANONICAL_KEYS
        assert body["manifest"]["integrity_root"] == body["integrity_root"]

    def test_policy_changes_gate_status_field_present(self):
        r = client.post("/evidence-pack", json={"project": str(BMS), "policy": "aviation"})
        assert r.status_code == 200
        assert r.json()["gate_policy_id"] == "aviation.v1"

    def test_include_manifest_false_omits_body(self):
        r = client.post("/evidence-pack", json={"project": str(BMS), "include_manifest": False})
        assert r.status_code == 200
        assert "manifest" not in r.json()


class TestEvidencePackErrors:
    def test_missing_project_dir_returns_422(self):
        r = client.post("/evidence-pack", json={"project": "does/not/exist"})
        assert r.status_code == 422

    def test_unknown_policy_returns_422(self):
        if not BMS.exists():
            pytest.skip("fixture not present")
        r = client.post("/evidence-pack", json={"project": str(BMS), "policy": "nonsense"})
        assert r.status_code == 422

    def test_analyze_path_still_works_backward_compatible(self):
        if not BMS.exists():
            pytest.skip("fixture not present")
        r = client.post("/analyze/path", json={"project": str(BMS)})
        assert r.status_code == 200
        assert "verdict" in r.json()
