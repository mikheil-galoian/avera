from __future__ import annotations

from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "avera" / "cli.py"


def test_demo_refresh_command_is_present_in_cli_surface() -> None:
    source = CLI_PATH.read_text(encoding="utf-8")

    assert '"demo-refresh"' in source
    assert "def run_demo_refresh(" in source
    assert "run_analyze(project, report_out, memory)" in source
    assert "run_traceability(report_path, memory, traceability_out, memory_limit)" in source
    assert "run_decision(report_path, None, traceability_out, decision_out)" in source
    assert "run_trend(memory, traceability_out, trend_out, memory_limit)" in source
    assert "run_pack(" in source
