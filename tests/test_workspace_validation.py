"""Tests for avera.validation.workspace — validate_workspace()."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from avera.validation.workspace import validate_workspace, REQUIRED_FILES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQ_HEADER = "id,component,requirement,metric,operator,threshold,safety_level,next_checks\n"
REQ_ROW = "R1,BMS,Max temp must not exceed 50C,max_temp,<=,50.0,high,BMS-HIL-007\n"

BASELINE_JSON = json.dumps({
    "runId": "baseline-001",
    "stage": "baseline",
    "tests": [{"id": "T1", "status": "passed", "metrics": {}}],
})

CURRENT_JSON = json.dumps({
    "runId": "current-001",
    "stage": "current",
    "tests": [{"id": "T1", "status": "failed", "metrics": {}}],
})

COMPONENT_MAP = json.dumps({"src/bms.c": {"component": "BMS", "requirements": ["R1"]}})
CHANGE_DESC = "Changed BMS thermal manager logic."


def _make_workspace(tmp_path: Path, overrides: dict | None = None) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir()
    files = {
        "requirements.csv": REQ_HEADER + REQ_ROW,
        "baseline_results.json": BASELINE_JSON,
        "current_results.json": CURRENT_JSON,
        "component_map.json": COMPONENT_MAP,
        "change_description.txt": CHANGE_DESC,
    }
    if overrides:
        files.update(overrides)
    for name, content in files.items():
        if content is None:
            continue  # skip to simulate missing file
        (ws / name).write_text(content, encoding="utf-8")
    return ws


# ---------------------------------------------------------------------------
# Valid workspace
# ---------------------------------------------------------------------------

class TestValidWorkspace:
    def test_valid_workspace_passes(self, tmp_path):
        ws = _make_workspace(tmp_path)
        result = validate_workspace(ws)
        assert result.ok is True
        assert result.errors == []

    def test_valid_workspace_has_correct_path(self, tmp_path):
        ws = _make_workspace(tmp_path)
        result = validate_workspace(ws)
        assert result.path == str(ws)

    def test_bms_fast_charge_fixture_is_valid(self):
        result = validate_workspace(Path("fixtures/bms-fast-charge"))
        assert result.ok is True

    def test_adas_fixture_is_valid(self):
        result = validate_workspace(Path("fixtures/adas-pedestrian-detection-regression"))
        assert result.ok is True


# ---------------------------------------------------------------------------
# Missing files
# ---------------------------------------------------------------------------

class TestMissingFiles:
    @pytest.mark.parametrize("missing_file", REQUIRED_FILES)
    def test_missing_required_file_fails(self, tmp_path, missing_file):
        ws = _make_workspace(tmp_path, overrides={missing_file: None})
        (ws / missing_file).unlink(missing_ok=True)
        result = validate_workspace(ws)
        assert result.ok is False
        assert any(missing_file in e for e in result.errors)


# ---------------------------------------------------------------------------
# Invalid requirements.csv
# ---------------------------------------------------------------------------

class TestInvalidRequirements:
    def test_missing_required_column_fails(self, tmp_path):
        bad_csv = "id,component,requirement\nR1,BMS,Some req\n"
        ws = _make_workspace(tmp_path, overrides={"requirements.csv": bad_csv})
        result = validate_workspace(ws)
        assert result.ok is False
        assert any("missing columns" in e.lower() or "requirements.csv" in e for e in result.errors)

    def test_empty_requirements_csv_fails(self, tmp_path):
        ws = _make_workspace(tmp_path, overrides={"requirements.csv": REQ_HEADER})
        result = validate_workspace(ws)
        assert result.ok is False


# ---------------------------------------------------------------------------
# Invalid JSON files
# ---------------------------------------------------------------------------

class TestInvalidJson:
    def test_invalid_json_in_baseline_fails(self, tmp_path):
        ws = _make_workspace(tmp_path, overrides={"baseline_results.json": "NOT JSON"})
        result = validate_workspace(ws)
        assert result.ok is False

    def test_invalid_json_in_current_fails(self, tmp_path):
        ws = _make_workspace(tmp_path, overrides={"current_results.json": "{bad json"})
        result = validate_workspace(ws)
        assert result.ok is False

    def test_invalid_json_in_component_map_fails(self, tmp_path):
        ws = _make_workspace(tmp_path, overrides={"component_map.json": "[]"})
        result = validate_workspace(ws)
        assert result.ok is False


# ---------------------------------------------------------------------------
# Missing verification fields
# ---------------------------------------------------------------------------

class TestMissingVerificationFields:
    def test_baseline_missing_run_id_fails(self, tmp_path):
        bad = json.dumps({"stage": "baseline", "tests": [{"id": "T1", "status": "passed"}]})
        ws = _make_workspace(tmp_path, overrides={"baseline_results.json": bad})
        result = validate_workspace(ws)
        assert result.ok is False

    def test_current_missing_tests_field_fails(self, tmp_path):
        bad = json.dumps({"runId": "c1", "stage": "current"})
        ws = _make_workspace(tmp_path, overrides={"current_results.json": bad})
        result = validate_workspace(ws)
        assert result.ok is False

    def test_empty_tests_array_fails(self, tmp_path):
        bad = json.dumps({"runId": "b1", "stage": "baseline", "tests": []})
        ws = _make_workspace(tmp_path, overrides={"baseline_results.json": bad})
        result = validate_workspace(ws)
        assert result.ok is False


# ---------------------------------------------------------------------------
# Non-existent workspace
# ---------------------------------------------------------------------------

class TestNonExistentWorkspace:
    def test_nonexistent_path_fails(self, tmp_path):
        result = validate_workspace(tmp_path / "does_not_exist")
        assert result.ok is False
        assert len(result.errors) >= 1

    def test_file_instead_of_directory_fails(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        result = validate_workspace(f)
        assert result.ok is False


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

class TestWarnings:
    def test_empty_change_description_produces_warning(self, tmp_path):
        ws = _make_workspace(tmp_path, overrides={"change_description.txt": "   "})
        result = validate_workspace(ws)
        assert result.ok is True
        assert len(result.warnings) >= 1
