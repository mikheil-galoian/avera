"""Fixture matrix completeness guard.

Every directory under ``fixtures/`` must have a complete expected outcome in
``fixtures/expected_outcomes.json`` (verdict + risk + confidence), so the fixture
matrix can confirm behaviour for *every* fixture rather than a subset.

This is a structural guard. The actual verdict/risk/confidence values are
enforced against real analyzer output by ``scripts/run_all_fixtures.py`` and the
per-domain fixture tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"

VALID_VERDICTS = {
    "confirmed_regression",
    "successful_change",
    "preexisting_failure",
    "worsened_preexisting_failure",
    "insufficient_evidence",
    "environment_failure",
    "requirements_coverage_gap",
    "possible_regression",
}
VALID_RISK = {"unknown", "low", "medium", "high", "release_blocking", "safety_critical"}
VALID_CONFIDENCE = {"low", "medium", "high"}


def _expected() -> dict[str, dict]:
    return json.loads((FIXTURES / "expected_outcomes.json").read_text(encoding="utf-8"))


def _fixture_dirs() -> list[str]:
    return sorted(p.name for p in FIXTURES.iterdir() if p.is_dir())


def test_every_fixture_has_expected_outcome() -> None:
    expected = _expected()
    missing = [name for name in _fixture_dirs() if name not in expected]
    assert not missing, f"fixtures without an expected outcome: {missing}"


def test_no_orphan_expected_outcomes() -> None:
    expected = _expected()
    dirs = set(_fixture_dirs())
    orphans = [name for name in expected if name not in dirs]
    assert not orphans, f"expected_outcomes entries with no fixture directory: {orphans}"


@pytest.mark.parametrize("name", sorted(_expected().keys()))
def test_expected_outcome_fields_are_valid(name: str) -> None:
    entry = _expected()[name]
    assert set(entry) >= {"verdict", "risk", "confidence"}, f"{name}: missing required keys"
    assert entry["verdict"] in VALID_VERDICTS, f"{name}: bad verdict {entry['verdict']!r}"
    assert entry["risk"] in VALID_RISK, f"{name}: bad risk {entry['risk']!r}"
    assert entry["confidence"] in VALID_CONFIDENCE, f"{name}: bad confidence {entry['confidence']!r}"
