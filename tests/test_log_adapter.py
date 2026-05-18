from __future__ import annotations

from pathlib import Path

from avera.adapters import adapt_log_csv


def test_adapt_log_csv_groups_messages_and_metrics() -> None:
    fixture = Path("/Users/mac/Desktop/AVERA/fixtures/bms-log-adapted/current_verification_log.csv")

    payload = adapt_log_csv(fixture, run_id="bms-log", stage="current")

    assert payload["runId"] == "bms-log"
    assert payload["stage"] == "current"
    assert payload["metadata"]["adapter"] == "log_csv.v0"
    assert len(payload["tests"]) == 1
    test = payload["tests"][0]
    assert test["status"] == "failed"
    assert test["metrics"]["max_cell_temp_c"] == 52.8
    assert test["metrics"]["cooling_response_ms"] == 638.0
    assert "temperature" in test["evidence"].lower()
    assert "cooling response" in test["evidence"].lower()


def test_adapt_log_csv_requires_message_column(tmp_path: Path) -> None:
    source = tmp_path / "invalid_log.csv"
    source.write_text(
        """test_id,component,status
BMS-HIL-FASTCHARGE-07,BMS Thermal Control,failed
""",
        encoding="utf-8",
    )

    try:
        adapt_log_csv(source, run_id="bms-log", stage="current")
    except ValueError as exc:
        assert "missing required columns" in str(exc)
    else:
        raise AssertionError("Expected log adapter to reject missing message column")
