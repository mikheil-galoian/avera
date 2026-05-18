from __future__ import annotations

import json
from pathlib import Path

from avera.cli import run_adapt_logs


def test_run_adapt_logs_writes_verification_json(tmp_path: Path) -> None:
    source = tmp_path / "verification_log.csv"
    target = tmp_path / "current_results.json"
    source.write_text(
        """timestamp_utc,test_id,component,status,metric,value,unit,message,environment
2026-05-01T11:00:00Z,BMS-HIL-FASTCHARGE-07,BMS Thermal Control,failed,max_cell_temp_c,52.8,C,current HIL run exceeded the maximum allowed cell temperature,HIL-rig-3
""",
        encoding="utf-8",
    )

    code = run_adapt_logs(source, target, run_id="bms-log-cli", stage="current")
    payload = json.loads(target.read_text(encoding="utf-8"))

    assert code == 0
    assert payload["runId"] == "bms-log-cli"
    assert payload["stage"] == "current"
    assert payload["tests"][0]["status"] == "failed"
