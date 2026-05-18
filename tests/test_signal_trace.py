"""Tests for avera.signals.trace — load and summarize signal traces."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path

import pytest

from avera.signals.trace import (
    SignalTracePoint,
    load_signal_trace,
    summarize_signal_trace,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEADER = "timestamp_ms,scenario_id,test_id,signal,value,unit\n"


def _csv(rows: list[str]) -> str:
    return HEADER + "\n".join(rows)


def _write_csv(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "signal_trace.csv"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# load_signal_trace
# ---------------------------------------------------------------------------

class TestLoadSignalTrace:
    def test_loads_minimal_valid_trace(self, tmp_path):
        path = _write_csv(tmp_path, _csv(["0,SCN,T1,temp_c,47.1,C"]))
        points = load_signal_trace(path)
        assert len(points) == 1
        p = points[0]
        assert p.timestamp_ms == 0.0
        assert p.scenario_id == "SCN"
        assert p.test_id == "T1"
        assert p.signal == "temp_c"
        assert p.value == pytest.approx(47.1)
        assert p.unit == "C"

    def test_loads_multiple_rows_in_order(self, tmp_path):
        path = _write_csv(tmp_path, _csv([
            "0,SCN,T1,temp_c,44.2,C",
            "5000,SCN,T1,temp_c,47.9,C",
            "10000,SCN,T1,temp_c,50.6,C",
        ]))
        points = load_signal_trace(path)
        assert len(points) == 3
        assert points[0].value == pytest.approx(44.2)
        assert points[2].value == pytest.approx(50.6)

    def test_raises_on_missing_required_column(self, tmp_path):
        path = tmp_path / "bad.csv"
        path.write_text("timestamp_ms,scenario_id,test_id,signal,unit\n0,S,T,sig,C\n")
        with pytest.raises(ValueError, match="missing fields"):
            load_signal_trace(path)

    def test_raises_on_invalid_numeric_value(self, tmp_path):
        path = _write_csv(tmp_path, _csv(["0,SCN,T1,temp_c,NOT_A_NUMBER,C"]))
        with pytest.raises(ValueError):
            load_signal_trace(path)

    def test_raises_when_file_does_not_exist(self, tmp_path):
        with pytest.raises((FileNotFoundError, OSError)):
            load_signal_trace(tmp_path / "nonexistent.csv")

    def test_loads_bms_fast_charge_fixture(self):
        bms_trace = Path("fixtures/bms-fast-charge/signal_trace.csv")
        points = load_signal_trace(bms_trace)
        assert len(points) > 0
        signals = {p.signal for p in points}
        assert "max_cell_temp_c" in signals

    def test_returns_signal_trace_point_instances(self, tmp_path):
        path = _write_csv(tmp_path, _csv(["0,SCN,T1,x,1.0,unit"]))
        points = load_signal_trace(path)
        assert all(isinstance(p, SignalTracePoint) for p in points)


# ---------------------------------------------------------------------------
# summarize_signal_trace
# ---------------------------------------------------------------------------

class TestSummarizeSignalTrace:
    def test_single_signal_summary_has_correct_fields(self):
        points = [
            SignalTracePoint(0, "S", "T1", "temp", 44.0, "C"),
            SignalTracePoint(5000, "S", "T1", "temp", 48.0, "C"),
            SignalTracePoint(10000, "S", "T1", "temp", 52.0, "C"),
        ]
        summaries = summarize_signal_trace(points)
        assert len(summaries) == 1
        s = summaries[0]
        assert s["test_id"] == "T1"
        assert s["signal"] == "temp"
        assert s["min"] == pytest.approx(44.0)
        assert s["max"] == pytest.approx(52.0)
        assert s["last"] == pytest.approx(52.0)
        assert s["count"] == 3
        assert s["unit"] == "C"

    def test_last_value_tracks_input_order(self):
        points = [
            SignalTracePoint(0, "S", "T1", "x", 10.0, "u"),
            SignalTracePoint(1, "S", "T1", "x", 5.0, "u"),
        ]
        summaries = summarize_signal_trace(points)
        assert summaries[0]["last"] == pytest.approx(5.0)

    def test_multiple_signals_produce_separate_summaries(self):
        points = [
            SignalTracePoint(0, "S", "T1", "temp", 44.0, "C"),
            SignalTracePoint(0, "S", "T1", "latency", 420.0, "ms"),
        ]
        summaries = summarize_signal_trace(points)
        signals = {s["signal"] for s in summaries}
        assert signals == {"temp", "latency"}

    def test_multiple_tests_produce_separate_summaries(self):
        points = [
            SignalTracePoint(0, "S", "T1", "temp", 44.0, "C"),
            SignalTracePoint(0, "S", "T2", "temp", 50.0, "C"),
        ]
        summaries = summarize_signal_trace(points)
        assert len(summaries) == 2

    def test_empty_input_returns_empty_list(self):
        assert summarize_signal_trace([]) == []

    def test_mixed_units_for_same_signal_raises(self):
        points = [
            SignalTracePoint(0, "S", "T1", "temp", 44.0, "C"),
            SignalTracePoint(1, "S", "T1", "temp", 48.0, "F"),
        ]
        with pytest.raises(ValueError, match="Mixed units"):
            summarize_signal_trace(points)

    def test_accepts_mapping_shaped_points(self):
        points = [
            {"test_id": "T1", "signal": "x", "value": 1.0, "unit": "u"},
        ]
        summaries = summarize_signal_trace(points)
        assert summaries[0]["count"] == 1

    def test_summaries_sorted_by_test_and_signal(self):
        points = [
            SignalTracePoint(0, "S", "T2", "b", 1.0, "u"),
            SignalTracePoint(0, "S", "T1", "a", 2.0, "u"),
        ]
        summaries = summarize_signal_trace(points)
        keys = [(s["test_id"], s["signal"]) for s in summaries]
        assert keys == sorted(keys)
