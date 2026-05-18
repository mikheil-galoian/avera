from __future__ import annotations

import json
from pathlib import Path

from avera.cli import run_adapt_simulation


def test_run_adapt_simulation_writes_verification_json(tmp_path: Path) -> None:
    csv_path = tmp_path / "simulation.csv"
    out_path = tmp_path / "current_results.json"
    csv_path.write_text(
        """test_id,component,status,metric,value,unit,scenario,evidence
ADAS-SIL-VRU-REGRESSION-03,ADAS Pedestrian Detection,failed,pedestrian_recall,0.903,ratio,ADAS-VRU-URBAN-CROSSING,recall below threshold
ADAS-SIL-VRU-REGRESSION-03,ADAS Pedestrian Detection,failed,brake_trigger_latency_ms,146.0,ms,ADAS-VRU-URBAN-CROSSING,latency above threshold
""",
        encoding="utf-8",
    )

    code = run_adapt_simulation(csv_path, out_path, run_id="adas-cli-sim", stage="current")

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["runId"] == "adas-cli-sim"
    assert payload["stage"] == "current"
    assert len(payload["tests"]) == 1
    assert payload["tests"][0]["status"] == "failed"
