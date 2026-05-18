"""Run AVERA over every local fixture and write reports per scenario."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from avera.cli import run_analyze
from avera.validation import validate_report, validate_workspace

FIXTURES = ROOT / "fixtures"
REPORTS = ROOT / "reports" / "fixtures"

EXPECTED = json.loads((FIXTURES / "expected_outcomes.json").read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []
    for fixture in sorted(path for path in FIXTURES.iterdir() if path.is_dir()):
        validation = validate_workspace(fixture)
        if not validation.ok:
            failures.extend(f"{fixture.name}: {error}" for error in validation.errors)
            continue

        out = REPORTS / fixture.name
        result_code = run_analyze(fixture, out)
        if result_code != 0:
            failures.append(f"{fixture.name}: analyze failed with {result_code}")
            continue

        report_path = out / "avera-report.json"
        graph_path = out / "avera-evidence-graph.json"
        if not report_path.exists():
            failures.append(f"{fixture.name}: missing report JSON")
            continue
        if not graph_path.exists():
            failures.append(f"{fixture.name}: missing evidence graph JSON")
            continue

        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{fixture.name}: invalid report JSON: {exc}")
            continue
        report_validation = validate_report(report)
        if not report_validation.ok:
            failures.extend(
                f"{fixture.name}: report validation: {error}"
                for error in report_validation.errors
            )
        expected = EXPECTED.get(fixture.name)
        if expected:
            for key, expected_value in expected.items():
                actual = report.get(key)
                if actual != expected_value:
                    failures.append(
                        f"{fixture.name}: {key}={actual!r}, expected {expected_value!r}"
                    )

    if failures:
        print("AVERA fixture run failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("AVERA fixture matrix passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
