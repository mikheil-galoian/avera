"""Tests for avera.query.engine — traceability query helpers."""

from __future__ import annotations

import pytest

from avera.query.engine import (
    query_component,
    query_gate_status,
    query_requirement,
    query_risk,
    query_test,
)

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

TRACEABILITY = {
    "components": [
        {"component": "BMS Thermal Control", "requirements": ["R1", "R2"], "tests": ["T1"]},
        {"component": "ADAS Perception", "requirements": ["R3"], "tests": ["T2"]},
    ],
    "requirements": [
        {"requirement": "R1", "component": "BMS Thermal Control", "metric": "max_temp"},
        {"requirement": "R2", "component": "BMS Thermal Control", "metric": "cooling_ms"},
    ],
    "tests": [
        {"test": "T1", "component": "BMS Thermal Control", "status": "failed"},
        {"test": "T2", "component": "ADAS Perception", "status": "passed"},
    ],
    "risks": [
        {"risk": "high", "count": 2},
        {"risk": "low", "count": 1},
    ],
    "gates": [
        {"gate_status": "block", "count": 1},
        {"gate_status": "pass", "count": 3},
    ],
}

# ---------------------------------------------------------------------------
# query_component
# ---------------------------------------------------------------------------

class TestQueryComponent:
    def test_returns_matching_component(self):
        result = query_component(TRACEABILITY, "BMS Thermal Control")
        assert result is not None
        assert result["component"] == "BMS Thermal Control"
        assert "R1" in result["requirements"]

    def test_returns_none_for_unknown_component(self):
        result = query_component(TRACEABILITY, "Unknown Component")
        assert result is None

    def test_returns_none_for_empty_index(self):
        result = query_component({}, "BMS Thermal Control")
        assert result is None

    def test_finds_second_component(self):
        result = query_component(TRACEABILITY, "ADAS Perception")
        assert result is not None
        assert result["component"] == "ADAS Perception"


# ---------------------------------------------------------------------------
# query_requirement
# ---------------------------------------------------------------------------

class TestQueryRequirement:
    def test_returns_matching_requirement(self):
        result = query_requirement(TRACEABILITY, "R1")
        assert result is not None
        assert result["requirement"] == "R1"

    def test_returns_none_for_unknown_requirement(self):
        result = query_requirement(TRACEABILITY, "R999")
        assert result is None

    def test_returns_none_for_empty_index(self):
        assert query_requirement({}, "R1") is None


# ---------------------------------------------------------------------------
# query_test
# ---------------------------------------------------------------------------

class TestQueryTest:
    def test_returns_matching_test(self):
        result = query_test(TRACEABILITY, "T1")
        assert result is not None
        assert result["test"] == "T1"
        assert result["status"] == "failed"

    def test_returns_none_for_unknown_test(self):
        result = query_test(TRACEABILITY, "T999")
        assert result is None

    def test_finds_passing_test(self):
        result = query_test(TRACEABILITY, "T2")
        assert result is not None
        assert result["status"] == "passed"


# ---------------------------------------------------------------------------
# query_risk
# ---------------------------------------------------------------------------

class TestQueryRisk:
    def test_returns_matching_risk(self):
        result = query_risk(TRACEABILITY, "high")
        assert result is not None
        assert result["risk"] == "high"

    def test_returns_none_for_unknown_risk(self):
        result = query_risk(TRACEABILITY, "safety_critical")
        assert result is None

    def test_returns_low_risk_entry(self):
        result = query_risk(TRACEABILITY, "low")
        assert result is not None


# ---------------------------------------------------------------------------
# query_gate_status
# ---------------------------------------------------------------------------

class TestQueryGateStatus:
    def test_returns_matching_gate_status(self):
        result = query_gate_status(TRACEABILITY, "block")
        assert result is not None
        assert result["gate_status"] == "block"

    def test_returns_pass_status(self):
        result = query_gate_status(TRACEABILITY, "pass")
        assert result is not None

    def test_returns_none_for_unknown_status(self):
        result = query_gate_status(TRACEABILITY, "review")
        assert result is None


# ---------------------------------------------------------------------------
# Edge cases — all queries on malformed input
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_none_components_list_returns_none(self):
        result = query_component({"components": None}, "X")
        assert result is None

    def test_non_dict_item_in_list_is_skipped(self):
        index = {"components": ["not_a_dict", {"component": "X"}]}
        result = query_component(index, "X")
        assert result is not None

    def test_empty_wanted_string_returns_none(self):
        result = query_component(TRACEABILITY, "")
        assert result is None
