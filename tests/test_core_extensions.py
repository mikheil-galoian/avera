"""Tests for the four AVERA core extension modules:
   audit/log, registry/thresholds, coverage/checker, feedback/store.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


# ============================================================
# audit/log — immutable hash-chained audit log
# ============================================================

class TestAuditLog:
    def _log(self, tmp_path: Path):
        from avera.audit.log import AuditLog
        return AuditLog(tmp_path / "audit.jsonl")

    def test_append_and_read(self, tmp_path):
        log = self._log(tmp_path)
        log.append(event="analysis_started", project="bms", run_id="r-001")
        log.append(event="verdict_issued",   project="bms", run_id="r-001",
                   verdict="confirmed_regression", risk="high")
        records = log.read_all()
        assert len(records) == 2
        assert records[0].event == "analysis_started"
        assert records[1].verdict == "confirmed_regression"

    def test_seq_monotonic(self, tmp_path):
        log = self._log(tmp_path)
        for i in range(5):
            log.append(event=f"ev{i}", project="p")
        seqs = [r.seq for r in log.read_all()]
        assert seqs == list(range(5))

    def test_chain_valid_on_clean_log(self, tmp_path):
        log = self._log(tmp_path)
        log.append(event="a", project="p")
        log.append(event="b", project="p")
        log.append(event="c", project="p")
        assert log.verify_chain() == 3

    def test_empty_log_verifies_zero(self, tmp_path):
        log = self._log(tmp_path)
        assert log.verify_chain() == 0

    def test_tamper_detected(self, tmp_path):
        from avera.audit.log import ChainIntegrityError
        log = self._log(tmp_path)
        log.append(event="verdict_issued", project="bms", verdict="confirmed_regression")
        log.append(event="follow_up",      project="bms")
        # Tamper record 0
        p = tmp_path / "audit.jsonl"
        text = p.read_text()
        p.write_text(text.replace("confirmed_regression", "successful_change"))
        with pytest.raises(ChainIntegrityError):
            log.verify_chain()

    def test_calibration_stats_accuracy(self, tmp_path):
        log = self._log(tmp_path)
        log.append(event="verdict_issued",  project="bms", run_id="r-1",
                   verdict="confirmed_regression")
        log.append(event="verdict_issued",  project="bms", run_id="r-2",
                   verdict="confirmed_regression")
        log.append(event="human_feedback",  project="bms", run_id="r-1",
                   human_confirmed=True)
        log.append(event="human_feedback",  project="bms", run_id="r-2",
                   human_confirmed=False)
        stats = log.calibration_stats("bms")
        assert stats["confirmed"] == 1
        assert stats["overruled"] == 1
        assert stats["accuracy"] == 0.5

    def test_read_project_filters(self, tmp_path):
        log = self._log(tmp_path)
        log.append(event="x", project="bms")
        log.append(event="x", project="adas")
        log.append(event="x", project="bms")
        assert len(log.read_project("bms")) == 2
        assert len(log.read_project("adas")) == 1


# ============================================================
# registry/thresholds — governed safety threshold store
# ============================================================

class TestThresholdRegistry:
    def _entry(self, req_id="BMS-001", value=75.0, valid_from="2026-01-01",
               safety_level="asil-d", source="ISO 26262"):
        from avera.registry.thresholds import ThresholdEntry
        return ThresholdEntry(
            req_id=req_id, metric="max_cell_temp_c", operator="<=",
            value=value, safety_level=safety_level,
            source_standard=source, owner="team@acme.com",
            valid_from=valid_from, rationale="test",
        )

    def test_register_and_resolve_latest(self, tmp_path):
        from avera.registry.thresholds import ThresholdRegistry
        reg = ThresholdRegistry()
        reg.register(self._entry(value=75.0, valid_from="2026-01-01"))
        reg.register(self._entry(value=72.0, valid_from="2026-04-01"))
        assert reg.resolve("BMS-001").value == 72.0

    def test_resolve_on_specific_date(self, tmp_path):
        from avera.registry.thresholds import ThresholdRegistry
        reg = ThresholdRegistry()
        reg.register(self._entry(value=75.0, valid_from="2026-01-01"))
        reg.register(self._entry(value=72.0, valid_from="2026-04-01"))
        assert reg.resolve("BMS-001", "2026-02-15").value == 75.0
        assert reg.resolve("BMS-001", "2026-05-01").value == 72.0

    def test_resolve_unknown_returns_none(self):
        from avera.registry.thresholds import ThresholdRegistry
        assert ThresholdRegistry().resolve("NONEXISTENT") is None

    def test_violation_check_lte(self):
        e = self._entry(value=72.0)
        assert e.is_violated_by(73.0) is True
        assert e.is_violated_by(72.0) is False
        assert e.is_violated_by(71.0) is False

    def test_conflict_on_duplicate_valid_from(self):
        from avera.registry.thresholds import ThresholdRegistry, ThresholdConflictError
        reg = ThresholdRegistry()
        reg.register(self._entry(value=75.0, valid_from="2026-01-01"))
        with pytest.raises(ThresholdConflictError):
            reg.register(self._entry(value=70.0, valid_from="2026-01-01"))

    def test_persist_and_reload(self, tmp_path):
        from avera.registry.thresholds import ThresholdRegistry
        p = tmp_path / "reg.json"
        reg = ThresholdRegistry()
        reg.register(self._entry(value=75.0, valid_from="2026-01-01"))
        reg.save(p)
        reg2 = ThresholdRegistry.load(p)
        assert reg2.resolve("BMS-001").value == 75.0

    def test_verify_no_gaps(self):
        from avera.registry.thresholds import ThresholdRegistry
        reg = ThresholdRegistry()
        reg.register(self._entry(req_id="R-001"))
        gaps = reg.verify_no_gaps(["R-001", "R-002"])
        assert gaps == ["R-002"]

    def test_history_sorted(self):
        from avera.registry.thresholds import ThresholdRegistry
        reg = ThresholdRegistry()
        reg.register(self._entry(value=75.0, valid_from="2026-01-01"))
        reg.register(self._entry(value=72.0, valid_from="2026-04-01"))
        h = reg.history("BMS-001")
        assert h[0].value == 75.0
        assert h[1].value == 72.0


# ============================================================
# coverage/checker — requirement coverage proof
# ============================================================

class TestCoverageChecker:
    _REQS = [
        {"id": "R-001", "safety_level": "asil-d"},
        {"id": "R-002", "safety_level": "asil-b"},
        {"id": "R-003", "safety_level": "asil-c"},
        {"id": "R-004", "safety_level": "unknown"},
    ]

    def test_full_coverage(self):
        from avera.coverage.checker import CoverageChecker
        cmap = {"T-01": ["R-001", "R-002", "R-003", "R-004"]}
        report = CoverageChecker(self._REQS, cmap).check()
        assert report.coverage_pct == 100.0
        assert report.uncovered_count == 0
        assert report.max_gap_risk == "low"

    def test_partial_coverage_pct(self):
        from avera.coverage.checker import CoverageChecker
        cmap = {"T-01": ["R-001", "R-002"]}
        report = CoverageChecker(self._REQS, cmap).check()
        assert report.coverage_pct == 50.0
        assert set(report.uncovered_req_ids) == {"R-003", "R-004"}

    def test_asil_c_uncovered_escalates_to_release_blocking(self):
        from avera.coverage.checker import CoverageChecker
        cmap = {"T-01": ["R-001", "R-002", "R-004"]}
        report = CoverageChecker(self._REQS, cmap).check()
        assert report.max_gap_risk == "release_blocking"

    def test_asil_b_uncovered_escalates_to_medium(self):
        from avera.coverage.checker import CoverageChecker
        reqs = [{"id": "R-001", "safety_level": "asil-b"}]
        report = CoverageChecker(reqs, {}).check()
        assert report.gaps[0].escalated_risk == "medium"

    def test_unknown_safety_uncovered_stays_low(self):
        from avera.coverage.checker import CoverageChecker
        reqs = [{"id": "R-001", "safety_level": "unknown"}]
        report = CoverageChecker(reqs, {}).check()
        assert report.gaps[0].escalated_risk == "low"

    def test_zero_requirements_returns_100_pct(self):
        from avera.coverage.checker import CoverageChecker
        report = CoverageChecker([], {}).check()
        assert report.coverage_pct == 100.0

    def test_schema_version_present(self):
        from avera.coverage.checker import CoverageChecker
        report = CoverageChecker(self._REQS, {}).check()
        assert report.as_dict()["schema_version"] == "avera.coverage.v1.0"

    def test_sil4_uncovered_release_blocking(self):
        from avera.coverage.checker import CoverageChecker
        reqs = [{"id": "ETCS-001", "safety_level": "sil4"}]
        report = CoverageChecker(reqs, {}).check()
        assert report.gaps[0].escalated_risk == "release_blocking"

    def test_class_c_uncovered_release_blocking(self):
        from avera.coverage.checker import CoverageChecker
        reqs = [{"id": "IMD-001", "safety_level": "class-c"}]
        report = CoverageChecker(reqs, {}).check()
        assert report.gaps[0].escalated_risk == "release_blocking"


# ============================================================
# feedback/store — human verdict calibration loop
# ============================================================

class TestFeedbackStore:
    def _store(self, tmp_path: Path):
        from avera.feedback.store import FeedbackStore
        return FeedbackStore(tmp_path / "feedback.db")

    def test_store_and_retrieve_verdict(self, tmp_path):
        fb = self._store(tmp_path)
        fb.store_verdict(run_id="r-001", project="bms",
                         verdict="confirmed_regression", risk="high",
                         confidence_score=0.95)
        rec = fb.get_record("r-001")
        assert rec is not None
        assert rec.engine_verdict == "confirmed_regression"
        assert rec.confidence_score == pytest.approx(0.95)

    def test_record_feedback_confirmed(self, tmp_path):
        fb = self._store(tmp_path)
        fb.store_verdict(run_id="r-001", project="bms",
                         verdict="confirmed_regression", risk="high")
        fb.record_feedback(run_id="r-001", confirmed=True, reviewer="eng@acme.com")
        rec = fb.get_record("r-001")
        assert rec.confirmed is True

    def test_record_feedback_overruled(self, tmp_path):
        fb = self._store(tmp_path)
        fb.store_verdict(run_id="r-001", project="bms",
                         verdict="confirmed_regression", risk="high")
        fb.record_feedback(run_id="r-001", confirmed=False,
                           human_verdict="successful_change",
                           notes="Non-deterministic test artefact.")
        rec = fb.get_record("r-001")
        assert rec.confirmed is False

    def test_calibration_accuracy(self, tmp_path):
        fb = self._store(tmp_path)
        for i in range(4):
            fb.store_verdict(run_id=f"r-{i}", project="bms",
                             verdict="confirmed_regression", risk="high")
            fb.record_feedback(run_id=f"r-{i}", confirmed=(i < 3))
        stats = fb.calibration_stats()
        assert stats.accuracy == pytest.approx(0.75)

    def test_pending_verdicts(self, tmp_path):
        fb = self._store(tmp_path)
        fb.store_verdict(run_id="r-001", project="bms",
                         verdict="confirmed_regression", risk="high")
        fb.store_verdict(run_id="r-002", project="bms",
                         verdict="confirmed_regression", risk="high")
        fb.record_feedback(run_id="r-001", confirmed=True)
        pending = fb.list_pending()
        assert len(pending) == 1
        assert pending[0].run_id == "r-002"

    def test_drift_warning_triggers(self, tmp_path):
        fb = self._store(tmp_path)
        for i in range(10):
            fb.store_verdict(run_id=f"r-{i}", project="bms",
                             verdict="confirmed_regression", risk="high")
            fb.record_feedback(run_id=f"r-{i}", confirmed=(i < 5))  # 50% accuracy
        assert fb.drift_warning(window=10, threshold=0.80) is True

    def test_drift_warning_no_trigger_when_accurate(self, tmp_path):
        fb = self._store(tmp_path)
        for i in range(5):
            fb.store_verdict(run_id=f"r-{i}", project="bms",
                             verdict="confirmed_regression", risk="high")
            fb.record_feedback(run_id=f"r-{i}", confirmed=True)  # 100% accuracy
        assert fb.drift_warning(window=10, threshold=0.80) is False

    def test_calibration_scoped_to_project(self, tmp_path):
        fb = self._store(tmp_path)
        fb.store_verdict(run_id="r-bms", project="bms",
                         verdict="confirmed_regression", risk="high")
        fb.store_verdict(run_id="r-adas", project="adas",
                         verdict="successful_change", risk="low")
        fb.record_feedback(run_id="r-bms",  confirmed=True)
        fb.record_feedback(run_id="r-adas", confirmed=False)
        bms_stats = fb.calibration_stats("bms")
        assert bms_stats.accuracy == 1.0
        assert bms_stats.total_verdicts == 1

    def test_idempotent_store_verdict(self, tmp_path):
        fb = self._store(tmp_path)
        fb.store_verdict(run_id="r-001", project="bms",
                         verdict="confirmed_regression", risk="high")
        fb.store_verdict(run_id="r-001", project="bms",  # duplicate
                         verdict="confirmed_regression", risk="high")
        stats = fb.calibration_stats()
        assert stats.total_verdicts == 1
