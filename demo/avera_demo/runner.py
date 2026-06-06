from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .artifacts import PROJECT_ROOT
from .models import ScenarioPaths


def run_analysis(scenario: ScenarioPaths) -> tuple[bool, str, str]:
    command = [
        sys.executable,
        "-B",
        "-m",
        "avera",
        "demo-refresh",
        "--project",
        str(scenario.fixture_dir),
        "--report-out",
        str(scenario.report_dir),
        "--memory",
        str(scenario.memory_path),
        "--traceability-out",
        str(scenario.traceability_path),
        "--decision-out",
        str(scenario.decision_path),
        "--trend-out",
        str(scenario.trend_path),
        "--pack-out",
        str(scenario.pack_path),
        "--manifest-out",
        str(scenario.manifest_path),
        "--audit-log",
        str(scenario.audit_log_path),
    ]
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(Path(PROJECT_ROOT) / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0, result.stdout, result.stderr
