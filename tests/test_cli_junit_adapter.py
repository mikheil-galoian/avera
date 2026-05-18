from __future__ import annotations

import json
from pathlib import Path

from avera.cli import run_adapt_junit


def test_run_adapt_junit_writes_verification_json(tmp_path: Path) -> None:
    xml_path = tmp_path / "results.xml"
    out_path = tmp_path / "current_results.json"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="adas_suite">
  <testcase classname="adas.perception" name="pedestrian_ok" time="0.41" />
  <testcase classname="adas.perception" name="pedestrian_drop">
    <failure message="recall dropped">pedestrian recall below threshold</failure>
  </testcase>
</testsuite>
""",
        encoding="utf-8",
    )

    code = run_adapt_junit(xml_path, out_path, run_id="adas-cli", stage="hil")

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert code == 0
    assert payload["runId"] == "adas-cli"
    assert payload["stage"] == "hil"
    assert [item["status"] for item in payload["tests"]] == ["passed", "failed"]
