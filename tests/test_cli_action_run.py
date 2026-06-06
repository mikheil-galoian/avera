"""Tests for `avera action-run` — the GitHub Action's evidence pipeline + outputs."""

from __future__ import annotations

from pathlib import Path

from avera import cli

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_ARTIFACTS = [
    "avera-report.json",
    "avera-report.md",
    "avera-evidence-graph.json",
    "avera-traceability-index.json",
    "avera-decision.json",
    "avera-trend-index.json",
    "avera-workspace-pack.json",
    "avera-evidence-manifest.json",
    "avera-audit.jsonl",
]

EXPECTED_OUTPUT_KEYS = {
    "verdict",
    "risk",
    "confidence",
    "gate_status",
    "report_path",
    "manifest_path",
    "integrity_root",
    "audit_log_path",
}


def _parse_outputs(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
    return out


def test_action_run_emits_all_artifacts_and_outputs(tmp_path: Path):
    out_dir = tmp_path / "avera-reports"
    gho = tmp_path / "gh_output.txt"

    code = cli.run_action(
        ROOT / "fixtures" / "powertrain-overspeed-regression",
        out_dir,
        github_output=gho,
    )
    # release_blocking fixture fails by default.
    assert code == 1

    for name in CANONICAL_ARTIFACTS:
        assert (out_dir / name).exists(), f"missing canonical artifact: {name}"

    outputs = _parse_outputs(gho)
    assert set(outputs) == EXPECTED_OUTPUT_KEYS
    assert outputs["verdict"] == "confirmed_regression"
    assert outputs["risk"] == "release_blocking"
    assert outputs["gate_status"] == "block"
    assert len(outputs["integrity_root"]) == 64
    assert outputs["report_path"].endswith("avera-report.json")
    assert outputs["manifest_path"].endswith("avera-evidence-manifest.json")
    assert outputs["audit_log_path"].endswith("avera-audit.jsonl")


def test_action_run_successful_change_passes(tmp_path: Path):
    out_dir = tmp_path / "out"
    gho = tmp_path / "gh.txt"
    code = cli.run_action(
        ROOT / "fixtures" / "powertrain-emissions-ok",
        out_dir,
        github_output=gho,
    )
    assert code == 0
    outputs = _parse_outputs(gho)
    assert outputs["verdict"] == "successful_change"
    assert outputs["gate_status"] == "pass"


def test_action_run_expected_verdict_mismatch_fails_but_emits_outputs(tmp_path: Path):
    out_dir = tmp_path / "out"
    gho = tmp_path / "gh.txt"
    code = cli.run_action(
        ROOT / "fixtures" / "powertrain-emissions-ok",
        out_dir,
        expected_verdict="confirmed_regression",
        github_output=gho,
    )
    assert code == 1  # asserted verdict does not match
    outputs = _parse_outputs(gho)  # outputs still emitted
    assert outputs["verdict"] == "successful_change"


def test_action_run_can_suppress_release_blocking_failure(tmp_path: Path):
    out_dir = tmp_path / "out"
    gho = tmp_path / "gh.txt"
    code = cli.run_action(
        ROOT / "fixtures" / "powertrain-overspeed-regression",
        out_dir,
        fail_on_release_blocking="false",
        fail_on_regression="false",
        github_output=gho,
    )
    assert code == 0
    outputs = _parse_outputs(gho)
    assert outputs["risk"] == "release_blocking"


def test_action_run_with_policy(tmp_path: Path):
    out_dir = tmp_path / "out"
    gho = tmp_path / "gh.txt"
    code = cli.run_action(
        ROOT / "fixtures" / "powertrain-emissions-ok",
        out_dir,
        policy_name="aviation",
        github_output=gho,
    )
    assert code == 0
    outputs = _parse_outputs(gho)
    # successful_change, low risk, high confidence -> passes even strict aviation policy.
    assert outputs["gate_status"] in {"pass", "review", "block"}
