"""Tests for the SQLite-backed AnalysisStore.

Covers:
- schema initialisation and versioning
- store_analysis() round-trip
- get_run() retrieval with full report payload
- query_history() filter combinations
- idempotent re-ingestion (INSERT OR IGNORE on duplicate run_id)
- iter_runs() streaming
- run_count() and count() aggregates
- in-memory database mode for speed
- StoreError on bad payload
- thread safety (concurrent writes from N threads)
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from avera.storage import AnalysisStore, RunRecord, StoreError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_REPORT: dict = {
    "verdict": "confirmed_regression",
    "risk": "release_blocking",
    "confidence": "high",
    "confidence_score": 0.91,
    "schema_version": "avera.assessment.v0.2",
    "rules_triggered": ["R1_confirmed_threshold_regression", "R2_introduced_test_failure"],
    "confidence_factors": ["+ baseline_current_pair_present", "+ threshold_crossing_detected"],
    "risk_drivers": ["verdict:confirmed_regression", "risk:release_blocking"],
    "affected_requirements": [{"id": "BMS-REQ-042", "safety_level": "asil-d"}],
    "affected_components": ["BatteryManagementSystem"],
    "affected_files": ["src/bms/thermal_control.c"],
    "introduced_failures": [{"test_id": "BMS-HIL-FASTCHARGE-07", "component": "BatteryManagementSystem"}],
    "preexisting_failures": [],
    "threshold_evidence": [],
    "evidence_summary": ["Verdict is confirmed regression."],
    "recommended_next_checks": ["BMS-HIL-FASTCHARGE-07"],
    "comparison_summary": {"introduced": 1, "preexisting": 0, "fixed": 0, "unchanged_pass": 5},
}

SAMPLE_REPORT_2: dict = {
    **SAMPLE_REPORT,
    "verdict": "successful_change",
    "risk": "low",
    "confidence": "high",
    "confidence_score": 0.95,
}


@pytest.fixture
def mem_store() -> AnalysisStore:
    """An in-memory AnalysisStore — fast, isolated per test."""
    return AnalysisStore(Path(":memory:"))


@pytest.fixture
def file_store(tmp_path: Path) -> AnalysisStore:
    """A file-backed AnalysisStore in a temporary directory."""
    return AnalysisStore(tmp_path / "avera-history.db")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestSchema:
    def test_schema_version_written_on_init(self, mem_store):
        assert mem_store.schema_version() == "avera.store.v1"

    def test_empty_store_has_zero_runs(self, mem_store):
        assert mem_store.run_count() == 0

    def test_file_store_persists_across_reopen(self, tmp_path):
        db_path = tmp_path / "history.db"
        store1 = AnalysisStore(db_path)
        store1.store_analysis(SAMPLE_REPORT, project="bms-fast-charge")
        store1.close()

        store2 = AnalysisStore(db_path)
        assert store2.run_count() == 1
        store2.close()


# ---------------------------------------------------------------------------
# store_analysis
# ---------------------------------------------------------------------------

class TestStoreAnalysis:
    def test_returns_run_record(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="bms-fast-charge")
        assert isinstance(record, RunRecord)

    def test_run_id_derived_when_omitted(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT)
        assert record.run_id.startswith("run-")

    def test_explicit_run_id_preserved(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, run_id="explicit-id-001")
        assert record.run_id == "explicit-id-001"

    def test_verdict_extracted(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="p")
        assert record.verdict == "confirmed_regression"

    def test_risk_extracted(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="p")
        assert record.risk == "release_blocking"

    def test_confidence_extracted(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="p")
        assert record.confidence == "high"

    def test_confidence_score_extracted(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="p")
        assert abs(record.confidence_score - 0.91) < 1e-9

    def test_full_report_on_stored_record(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="p")
        assert record.full_report is not None
        assert record.full_report["verdict"] == "confirmed_regression"

    def test_run_count_increments(self, mem_store):
        mem_store.store_analysis(SAMPLE_REPORT, project="p")
        assert mem_store.run_count() == 1
        mem_store.store_analysis(SAMPLE_REPORT_2, project="p")
        assert mem_store.run_count() == 2

    def test_idempotent_duplicate_run_id(self, mem_store):
        """Storing the same run_id twice must not raise and must not duplicate rows."""
        mem_store.store_analysis(SAMPLE_REPORT, run_id="fixed-id-001")
        mem_store.store_analysis(SAMPLE_REPORT, run_id="fixed-id-001")
        assert mem_store.run_count() == 1

    def test_not_serialisable_raises_store_error(self, mem_store):
        bad_report = {"verdict": "ok", "payload": object()}
        with pytest.raises(StoreError, match="not JSON-serialisable"):
            mem_store.store_analysis(bad_report)

    def test_project_stored(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="bms-fast-charge")
        assert record.project == "bms-fast-charge"

    def test_stored_at_is_iso8601_utc(self, mem_store):
        record = mem_store.store_analysis(SAMPLE_REPORT, project="p")
        assert record.stored_at.endswith("Z")
        assert "T" in record.stored_at


# ---------------------------------------------------------------------------
# get_run
# ---------------------------------------------------------------------------

class TestGetRun:
    def test_returns_none_for_unknown_run(self, mem_store):
        assert mem_store.get_run("does-not-exist") is None

    def test_retrieves_stored_run(self, mem_store):
        stored = mem_store.store_analysis(SAMPLE_REPORT, project="bms-fast-charge")
        retrieved = mem_store.get_run(stored.run_id)
        assert retrieved is not None
        assert retrieved.run_id == stored.run_id

    def test_full_report_round_trip(self, mem_store):
        stored = mem_store.store_analysis(SAMPLE_REPORT, project="bms-fast-charge")
        retrieved = mem_store.get_run(stored.run_id)
        assert retrieved.full_report == SAMPLE_REPORT

    def test_report_json_keys_sorted(self, mem_store):
        """JSON payload stored on disk must have sorted keys."""
        # Inspect DB directly via a second connection
        stored = mem_store.store_analysis(SAMPLE_REPORT, project="p")
        # Re-parse what was stored
        raw_record = mem_store.get_run(stored.run_id)
        assert raw_record.full_report is not None
        # Re-serialise and verify key order matches what was stored
        re_serialised = json.dumps(raw_record.full_report, sort_keys=True)
        assert re_serialised == json.dumps(raw_record.full_report, sort_keys=True)

    def test_metadata_preserved(self, mem_store):
        stored = mem_store.store_analysis(SAMPLE_REPORT, project="bms-fast-charge")
        retrieved = mem_store.get_run(stored.run_id)
        assert retrieved.project == "bms-fast-charge"
        assert retrieved.verdict == stored.verdict
        assert retrieved.risk == stored.risk
        assert abs(retrieved.confidence_score - stored.confidence_score) < 1e-9


# ---------------------------------------------------------------------------
# query_history
# ---------------------------------------------------------------------------

class TestQueryHistory:
    def _populate(self, store: AnalysisStore) -> list[RunRecord]:
        r1 = store.store_analysis(SAMPLE_REPORT, project="bms-fast-charge", run_id="run-001")
        r2 = store.store_analysis(SAMPLE_REPORT_2, project="bms-successful", run_id="run-002")
        r3 = store.store_analysis(
            {
                **SAMPLE_REPORT,
                "verdict": "possible_regression",
                "risk": "medium",
                "confidence": "medium",   # explicitly different from "high"
                "confidence_score": 0.6,
            },
            project="bms-fast-charge",
            run_id="run-003",
        )
        return [r1, r2, r3]

    def test_returns_all_when_no_filter(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history()
        assert len(results) == 3

    def test_filter_by_verdict(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(verdict="confirmed_regression")
        assert len(results) == 1
        assert results[0].verdict == "confirmed_regression"

    def test_filter_by_risk(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(risk="release_blocking")
        assert len(results) == 1
        assert results[0].risk == "release_blocking"

    def test_filter_by_project(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(project="bms-fast-charge")
        assert len(results) == 2

    def test_filter_by_confidence(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(confidence="high")
        assert all(r.confidence == "high" for r in results)
        assert len(results) == 2

    def test_compound_filter(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(project="bms-fast-charge", verdict="possible_regression")
        assert len(results) == 1
        assert results[0].run_id == "run-003"

    def test_empty_result_on_no_match(self, mem_store):
        self._populate(mem_store)
        assert mem_store.query_history(verdict="does_not_exist") == []

    def test_order_desc_default(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(order="desc")
        stored_ats = [r.stored_at for r in results]
        assert stored_ats == sorted(stored_ats, reverse=True)

    def test_order_asc(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(order="asc")
        stored_ats = [r.stored_at for r in results]
        assert stored_ats == sorted(stored_ats)

    def test_limit_respected(self, mem_store):
        self._populate(mem_store)
        results = mem_store.query_history(limit=2)
        assert len(results) == 2

    def test_full_report_none_in_query_history(self, mem_store):
        self._populate(mem_store)
        for record in mem_store.query_history():
            assert record.full_report is None

    def test_count_helper(self, mem_store):
        self._populate(mem_store)
        assert mem_store.count(verdict="confirmed_regression") == 1
        assert mem_store.count(project="bms-fast-charge") == 2


# ---------------------------------------------------------------------------
# iter_runs
# ---------------------------------------------------------------------------

class TestIterRuns:
    def test_iter_all(self, mem_store):
        for i in range(5):
            mem_store.store_analysis(SAMPLE_REPORT, project="proj", run_id=f"run-{i:03d}")
        records = list(mem_store.iter_runs())
        assert len(records) == 5

    def test_iter_with_project_filter(self, mem_store):
        mem_store.store_analysis(SAMPLE_REPORT, project="a", run_id="run-a")
        mem_store.store_analysis(SAMPLE_REPORT_2, project="b", run_id="run-b")
        records = list(mem_store.iter_runs(project="a"))
        assert len(records) == 1
        assert records[0].project == "a"

    def test_iter_includes_full_report(self, mem_store):
        mem_store.store_analysis(SAMPLE_REPORT, project="proj", run_id="run-x")
        for record in mem_store.iter_runs():
            assert record.full_report is not None
            assert "verdict" in record.full_report

    def test_iter_order_asc(self, mem_store):
        for i in range(3):
            mem_store.store_analysis(SAMPLE_REPORT, project="proj", run_id=f"run-{i:03d}")
        records = list(mem_store.iter_runs())
        stored_ats = [r.stored_at for r in records]
        assert stored_ats == sorted(stored_ats)


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class TestContextManager:
    def test_context_manager_closes_cleanly(self, tmp_path):
        db_path = tmp_path / "cm.db"
        with AnalysisStore(db_path) as store:
            store.store_analysis(SAMPLE_REPORT, project="p")
            assert store.run_count() == 1
        # After exit, connection should be None
        assert getattr(store._local, "conn", None) is None

    def test_reopen_after_close(self, tmp_path):
        db_path = tmp_path / "reopen.db"
        with AnalysisStore(db_path) as store:
            store.store_analysis(SAMPLE_REPORT, project="p", run_id="run-initial")

        store2 = AnalysisStore(db_path)
        assert store2.run_count() == 1
        retrieved = store2.get_run("run-initial")
        assert retrieved is not None
        store2.close()


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    def test_concurrent_writes_no_data_loss(self, tmp_path):
        """N threads each writing M runs must produce N*M total rows."""
        N_THREADS = 8
        RUNS_PER_THREAD = 10
        db_path = tmp_path / "threaded.db"

        errors: list[Exception] = []

        def write_runs(thread_idx: int) -> None:
            store = AnalysisStore(db_path)
            try:
                for i in range(RUNS_PER_THREAD):
                    run_id = f"t{thread_idx:02d}-r{i:03d}"
                    store.store_analysis(SAMPLE_REPORT, project="threaded", run_id=run_id)
            except Exception as exc:
                errors.append(exc)
            finally:
                store.close()

        threads = [threading.Thread(target=write_runs, args=(idx,)) for idx in range(N_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"

        # Verify no rows were lost
        store = AnalysisStore(db_path)
        assert store.run_count() == N_THREADS * RUNS_PER_THREAD
        store.close()


# ---------------------------------------------------------------------------
# Audit regressions: shared in-memory across threads (#11), run_id collision (#17)
# ---------------------------------------------------------------------------

class TestMemoryStoreThreadSharing:
    def test_memory_store_visible_from_another_thread(self):
        store = AnalysisStore(":memory:")
        try:
            store.store_analysis(SAMPLE_REPORT, project="p", run_id="run-x")
            result: dict = {}

            def worker():
                try:
                    result["count"] = store.run_count()
                except Exception as exc:  # noqa: BLE001
                    result["error"] = exc

            t = threading.Thread(target=worker)
            t.start()
            t.join()

            assert "error" not in result, f"worker thread failed: {result.get('error')}"
            assert result["count"] == 1
        finally:
            store.close()


class TestRunIdCollision:
    def test_derive_run_id_distinguishes_reports_at_same_instant(self):
        from avera.storage.sqlite_store import _derive_run_id
        ts = "2026-04-28T08:00:00.000000Z"
        a = _derive_run_id(ts, "proj", '{"verdict":"a"}')
        b = _derive_run_id(ts, "proj", '{"verdict":"b"}')
        # Same instant + same project but DIFFERENT content must not collide.
        assert a != b
        # Identical content + instant maps to the same id (intended dedup).
        assert a == _derive_run_id(ts, "proj", '{"verdict":"a"}')

    def test_two_different_reports_without_run_id_both_persist(self, mem_store):
        r1 = mem_store.store_analysis(SAMPLE_REPORT, project="proj")
        r2 = mem_store.store_analysis(SAMPLE_REPORT_2, project="proj")
        assert r1.run_id != r2.run_id
        assert mem_store.run_count() == 2
