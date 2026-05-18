from __future__ import annotations

import sys
import unittest
from unittest import mock

from avera import cli


class DemoRefreshCliTests(unittest.TestCase):
    def test_run_demo_refresh_orchestrates_pipeline_and_passes_derived_paths(self) -> None:
        tmp_path = cli.Path(self.id().replace(".", "_"))
        project = tmp_path / "fixture"
        report_out = tmp_path / "reports" / "fixture"
        memory = tmp_path / "reports" / "avera-memory.jsonl"
        traceability_out = tmp_path / "reports" / "avera-traceability-index.json"
        decision_out = tmp_path / "reports" / "avera-decision.json"
        trend_out = tmp_path / "reports" / "avera-trend-index.json"
        pack_out = tmp_path / "reports" / "avera-workspace-pack.json"

        calls: list[tuple[str, tuple[object, ...]]] = []

        def record(name: str, return_code: int = 0):
            def _inner(*args):
                calls.append((name, args))
                return return_code

            return _inner

        with (
            mock.patch.object(cli, "run_analyze", record("analyze")),
            mock.patch.object(cli, "run_traceability", record("traceability")),
            mock.patch.object(cli, "run_decision", record("decision")),
            mock.patch.object(cli, "run_trend", record("trend")),
            mock.patch.object(cli, "run_pack", record("pack")),
        ):
            exit_code = cli.run_demo_refresh(
                project=project,
                report_out=report_out,
                memory=memory,
                traceability_out=traceability_out,
                decision_out=decision_out,
                trend_out=trend_out,
                pack_out=pack_out,
                memory_limit=42,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            calls,
            [
                ("analyze", (project, report_out, memory)),
                (
                    "traceability",
                    (report_out / "avera-report.json", memory, traceability_out, 42),
                ),
                (
                    "decision",
                    (report_out / "avera-report.json", None, traceability_out, decision_out),
                ),
                ("trend", (memory, traceability_out, trend_out, 42)),
                (
                    "pack",
                    (
                        project,
                        report_out / "avera-report.json",
                        report_out / "avera-report.md",
                        report_out / "avera-evidence-graph.json",
                        memory,
                        traceability_out,
                        decision_out,
                        trend_out,
                        pack_out,
                    ),
                ),
            ],
        )

    def test_run_demo_refresh_stops_on_first_failing_stage(self) -> None:
        cases = [
            ("analyze", 2, ["analyze"]),
            ("traceability", 3, ["analyze", "traceability"]),
            ("decision", 4, ["analyze", "traceability", "decision"]),
            ("trend", 5, ["analyze", "traceability", "decision", "trend"]),
            ("pack", 6, ["analyze", "traceability", "decision", "trend", "pack"]),
        ]

        for failing_step, failure_code, expected_calls in cases:
            with self.subTest(failing_step=failing_step):
                tmp_path = cli.Path(f"{self.id().replace('.', '_')}_{failing_step}")
                project = tmp_path / "fixture"
                report_out = tmp_path / "reports" / "fixture"
                memory = tmp_path / "reports" / "avera-memory.jsonl"
                traceability_out = tmp_path / "reports" / "avera-traceability-index.json"
                decision_out = tmp_path / "reports" / "avera-decision.json"
                trend_out = tmp_path / "reports" / "avera-trend-index.json"
                pack_out = tmp_path / "reports" / "avera-workspace-pack.json"

                calls: list[str] = []

                def record(name: str):
                    def _inner(*_args):
                        calls.append(name)
                        return failure_code if name == failing_step else 0

                    return _inner

                with (
                    mock.patch.object(cli, "run_analyze", record("analyze")),
                    mock.patch.object(cli, "run_traceability", record("traceability")),
                    mock.patch.object(cli, "run_decision", record("decision")),
                    mock.patch.object(cli, "run_trend", record("trend")),
                    mock.patch.object(cli, "run_pack", record("pack")),
                ):
                    exit_code = cli.run_demo_refresh(
                        project=project,
                        report_out=report_out,
                        memory=memory,
                        traceability_out=traceability_out,
                        decision_out=decision_out,
                        trend_out=trend_out,
                        pack_out=pack_out,
                        memory_limit=7,
                    )

                self.assertEqual(exit_code, failure_code)
                self.assertEqual(calls, expected_calls)

    def test_main_dispatches_demo_refresh_arguments(self) -> None:
        tmp_path = cli.Path(self.id().replace(".", "_"))
        captured: dict[str, object] = {}

        def fake_run_demo_refresh(
            project,
            report_out,
            memory,
            traceability_out,
            decision_out,
            trend_out,
            pack_out,
            memory_limit,
        ) -> int:
            captured.update(
                {
                    "project": project,
                    "report_out": report_out,
                    "memory": memory,
                    "traceability_out": traceability_out,
                    "decision_out": decision_out,
                    "trend_out": trend_out,
                    "pack_out": pack_out,
                    "memory_limit": memory_limit,
                }
            )
            return 9

        argv = [
            "avera",
            "demo-refresh",
            "--project",
            str(tmp_path / "fixture"),
            "--report-out",
            str(tmp_path / "report-dir"),
            "--memory",
            str(tmp_path / "memory.jsonl"),
            "--traceability-out",
            str(tmp_path / "traceability.json"),
            "--decision-out",
            str(tmp_path / "decision.json"),
            "--trend-out",
            str(tmp_path / "trend.json"),
            "--pack-out",
            str(tmp_path / "pack.json"),
            "--memory-limit",
            "12",
        ]

        with (
            mock.patch.object(cli, "run_demo_refresh", fake_run_demo_refresh),
            mock.patch.object(sys, "argv", argv),
            self.assertRaises(SystemExit) as exc_info,
        ):
            cli.main()

        self.assertEqual(exc_info.exception.code, 9)
        self.assertEqual(
            captured,
            {
                "project": tmp_path / "fixture",
                "report_out": tmp_path / "report-dir",
                "memory": tmp_path / "memory.jsonl",
                "traceability_out": tmp_path / "traceability.json",
                "decision_out": tmp_path / "decision.json",
                "trend_out": tmp_path / "trend.json",
                "pack_out": tmp_path / "pack.json",
                "memory_limit": 12,
            },
        )
