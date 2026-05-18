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
        "analyze",
        "--project",
        str(scenario.fixture_dir),
        "--out",
        str(scenario.report_dir),
        "--memory",
        str(scenario.memory_path),
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
