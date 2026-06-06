"""Command-line entrypoints for the local AVERA prototype."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from avera.adapters import adapt_junit_xml, adapt_log_csv, adapt_requirements_csv, adapt_simulation_csv
from avera.adapters.requirements import write_adapted_requirements
from avera.gates import evaluate_gate, list_builtin_policies, load_builtin_policy, load_policy
from avera.graph import build_evidence_graph
from avera.classify.risk_classifier import classify_risk
from avera.compare.baseline_comparator import compare_runs
from avera.contracts import validate_artifact, validate_bundle
from avera.decisions import evaluate_decision
from avera.evidence import (
    build_evidence_manifest,
    record_manifest_in_audit_log,
    write_evidence_manifest,
)
from avera.ingestion.component_map import load_component_map
from avera.ingestion.requirements import load_requirements
from avera.ingestion.verification_results import load_verification_results
from avera.memory import (
    append_analysis_record,
    append_gate_record,
    load_memory_records,
    summarize_memory,
)
from avera.pack import build_workspace_pack, write_workspace_pack
from avera.query import (
    query_component,
    query_gate_status,
    query_requirement,
    query_risk,
    query_test,
)
from avera.reports.json_report import assessment_to_dict, write_json_report
from avera.reports.markdown import write_markdown_report
from avera.signals import load_signal_trace, summarize_signal_trace
from avera.traceability import build_traceability_index
from avera.trends import build_trend_index
from avera.validation import validate_report, validate_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="avera",
        description="Analyze automotive engineering evidence and produce risk reports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze",
        help="Analyze a local AVERA project folder.",
    )
    analyze.add_argument(
        "--project",
        type=Path,
        required=True,
        help="Folder containing requirements, component map, and verification artifacts.",
    )
    analyze.add_argument(
        "--out",
        type=Path,
        default=Path("reports"),
        help="Output directory for generated reports.",
    )
    analyze.add_argument(
        "--memory",
        type=Path,
        default=Path("reports/avera-memory.jsonl"),
        help="Append analysis history to this JSONL memory ledger.",
    )

    adapt_junit = subparsers.add_parser(
        "adapt-junit",
        help="Convert JUnit / xUnit XML into an AVERA verification-results JSON artifact.",
    )
    adapt_junit.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the JUnit / xUnit XML file.",
    )
    adapt_junit.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for the generated verification JSON.",
    )
    adapt_junit.add_argument(
        "--run-id",
        required=True,
        help="Run identifier to embed in the generated AVERA verification JSON.",
    )
    adapt_junit.add_argument(
        "--stage",
        default="verification",
        help="Stage label to embed in the generated AVERA verification JSON.",
    )

    adapt_simulation = subparsers.add_parser(
        "adapt-simulation",
        help="Convert simulation-results CSV into an AVERA verification-results JSON artifact.",
    )
    adapt_simulation.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the simulation-results CSV file.",
    )
    adapt_simulation.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for the generated verification JSON.",
    )
    adapt_simulation.add_argument(
        "--run-id",
        required=True,
        help="Run identifier to embed in the generated AVERA verification JSON.",
    )
    adapt_simulation.add_argument(
        "--stage",
        default="simulation",
        help="Stage label to embed in the generated AVERA verification JSON.",
    )

    adapt_requirements = subparsers.add_parser(
        "adapt-requirements",
        help="Convert a richer requirements export CSV into the stable AVERA requirements.csv shape.",
    )
    adapt_requirements.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the richer requirements export CSV file.",
    )
    adapt_requirements.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for the generated AVERA requirements.csv file.",
    )

    adapt_logs = subparsers.add_parser(
        "adapt-logs",
        help="Convert richer verification log CSV into an AVERA verification-results JSON artifact.",
    )
    adapt_logs.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the verification log CSV file.",
    )
    adapt_logs.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output path for the generated verification JSON.",
    )
    adapt_logs.add_argument(
        "--run-id",
        required=True,
        help="Run identifier to embed in the generated AVERA verification JSON.",
    )
    adapt_logs.add_argument(
        "--stage",
        default="verification",
        help="Stage label to embed in the generated AVERA verification JSON.",
    )

    validate = subparsers.add_parser(
        "validate-workspace",
        help="Validate a local AVERA evidence workspace.",
    )
    validate.add_argument(
        "project",
        type=Path,
        help="Folder containing an AVERA evidence pack.",
    )

    run_fixtures = subparsers.add_parser(
        "run-fixtures",
        help="Run all local fixture evidence packs.",
    )
    run_fixtures.add_argument(
        "--fixtures",
        type=Path,
        default=Path("fixtures"),
        help="Directory containing AVERA fixture folders.",
    )
    run_fixtures.add_argument(
        "--out",
        type=Path,
        default=Path("reports/fixtures"),
        help="Output directory for fixture reports.",
    )
    run_fixtures.add_argument(
        "--memory",
        type=Path,
        default=Path("reports/avera-memory.jsonl"),
        help="Append fixture analysis history to this JSONL memory ledger.",
    )

    gate = subparsers.add_parser(
        "gate",
        help="Evaluate a generated AVERA JSON report against a release gate policy.",
    )
    gate.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to avera-report.json.",
    )
    gate.add_argument(
        "--max-risk",
        default=None,
        choices=("unknown", "low", "medium", "high", "release_blocking", "safety_critical"),
        help=(
            "Highest risk level allowed before the gate blocks. "
            "Overrides the policy when set. Default: policy value (general = medium)."
        ),
    )
    gate.add_argument(
        "--min-confidence-score",
        type=float,
        default=None,
        help=(
            "Minimum confidence score before the gate requires review. "
            "Overrides the policy when set. Default: policy value (general = 0.5)."
        ),
    )
    gate.add_argument(
        "--policy",
        default=None,
        choices=tuple(list_builtin_policies()),
        help="Built-in domain gate policy to apply (e.g. automotive, aviation, medical).",
    )
    gate.add_argument(
        "--policy-file",
        type=Path,
        default=None,
        help="Path to a custom gate policy JSON file. Takes precedence over --policy.",
    )
    gate.add_argument(
        "--memory",
        type=Path,
        default=Path("reports/avera-memory.jsonl"),
        help="Append gate decisions to this JSONL memory ledger.",
    )

    memory = subparsers.add_parser(
        "memory",
        help="Show local AVERA engineering memory summary.",
    )
    memory.add_argument(
        "--path",
        type=Path,
        default=Path("reports/avera-memory.jsonl"),
        help="Path to the JSONL memory ledger.",
    )
    memory.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of newest memory records to show.",
    )

    traceability = subparsers.add_parser(
        "traceability",
        help="Build a component-first traceability index from report and memory.",
    )
    traceability.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to avera-report.json.",
    )
    traceability.add_argument(
        "--memory",
        type=Path,
        default=Path("reports/avera-memory.jsonl"),
        help="Path to the JSONL memory ledger.",
    )
    traceability.add_argument(
        "--out",
        type=Path,
        default=Path("reports/avera-traceability-index.json"),
        help="Output path for the generated traceability index.",
    )
    traceability.add_argument(
        "--memory-limit",
        type=int,
        default=100,
        help="Number of newest memory records to include.",
    )

    decision = subparsers.add_parser(
        "decision",
        help="Build an engineering decision from report, gate, and traceability.",
    )
    decision.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to avera-report.json.",
    )
    decision.add_argument(
        "--gate",
        type=Path,
        default=None,
        help="Optional path to a gate decision JSON file.",
    )
    decision.add_argument(
        "--traceability",
        type=Path,
        default=None,
        help="Optional path to a traceability index JSON file.",
    )
    decision.add_argument(
        "--out",
        type=Path,
        default=Path("reports/avera-decision.json"),
        help="Output path for the generated decision JSON.",
    )

    pack = subparsers.add_parser(
        "pack",
        help="Build a portable workspace pack from existing AVERA artifacts.",
    )
    pack.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Workspace folder for the pack.",
    )
    pack.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to avera-report.json.",
    )
    pack.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="Optional path to avera-report.md.",
    )
    pack.add_argument(
        "--graph",
        type=Path,
        default=None,
        help="Optional path to avera-evidence-graph.json.",
    )
    pack.add_argument(
        "--memory",
        type=Path,
        default=None,
        help="Optional path to avera-memory.jsonl.",
    )
    pack.add_argument(
        "--traceability",
        type=Path,
        default=None,
        help="Optional path to avera-traceability-index.json.",
    )
    pack.add_argument(
        "--decision",
        type=Path,
        default=None,
        help="Optional path to avera-decision.json.",
    )
    pack.add_argument(
        "--trend",
        type=Path,
        default=None,
        help="Optional path to avera-trend-index.json.",
    )
    pack.add_argument(
        "--out",
        type=Path,
        default=Path("reports/avera-workspace-pack.json"),
        help="Output path for the workspace pack JSON.",
    )
    pack.add_argument(
        "--manifest-out",
        type=Path,
        default=None,
        help=(
            "Output path for the evidence manifest JSON. "
            "Defaults to avera-evidence-manifest.json next to --out."
        ),
    )
    pack.add_argument(
        "--audit-log",
        type=Path,
        default=None,
        help=(
            "Path to the append-only, hash-chained audit log (JSONL). "
            "The manifest integrity root is recorded here. "
            "Defaults to avera-audit.jsonl next to --out."
        ),
    )

    query = subparsers.add_parser(
        "query",
        help="Run a local query against a traceability index.",
    )
    query.add_argument(
        "--traceability",
        type=Path,
        required=True,
        help="Path to avera-traceability-index.json.",
    )
    query.add_argument(
        "--kind",
        required=True,
        choices=("component", "requirement", "test", "risk", "gate"),
        help="Query type.",
    )
    query.add_argument(
        "--value",
        required=True,
        help="Lookup value for the query.",
    )

    trend = subparsers.add_parser(
        "trend",
        help="Build a trend index from memory and optional traceability.",
    )
    trend.add_argument(
        "--memory",
        type=Path,
        required=True,
        help="Path to avera-memory.jsonl.",
    )
    trend.add_argument(
        "--traceability",
        type=Path,
        default=None,
        help="Optional path to avera-traceability-index.json.",
    )
    trend.add_argument(
        "--out",
        type=Path,
        default=Path("reports/avera-trend-index.json"),
        help="Output path for the generated trend index.",
    )
    trend.add_argument(
        "--memory-limit",
        type=int,
        default=500,
        help="Number of newest memory records to include in trend analysis.",
    )

    contract = subparsers.add_parser(
        "validate-artifact",
        help="Validate a stable AVERA artifact contract.",
    )
    contract.add_argument(
        "--artifact",
        required=True,
        choices=("report", "graph", "decision", "trend", "workspace_pack", "evidence_manifest"),
        help="Artifact contract to validate.",
    )
    contract.add_argument(
        "--path",
        type=Path,
        required=True,
        help="Path to the artifact JSON file.",
    )
    contract.add_argument(
        "--bundle",
        action="store_true",
        help="Validate workspace pack as a bundle with nested artifacts.",
    )

    demo_refresh = subparsers.add_parser(
        "demo-refresh",
        help="Refresh the full local AVERA demo artifact chain for one scenario.",
    )
    demo_refresh.add_argument(
        "--project",
        type=Path,
        required=True,
        help="Fixture or workspace folder to analyze.",
    )
    demo_refresh.add_argument(
        "--report-out",
        type=Path,
        default=Path("reports/fixtures/bms-fast-charge"),
        help="Output directory for report, markdown, and evidence graph.",
    )
    demo_refresh.add_argument(
        "--memory",
        type=Path,
        default=Path("reports/avera-memory.jsonl"),
        help="Path to the shared memory ledger.",
    )
    demo_refresh.add_argument(
        "--traceability-out",
        type=Path,
        default=Path("reports/avera-traceability-index.json"),
        help="Output path for the traceability index.",
    )
    demo_refresh.add_argument(
        "--decision-out",
        type=Path,
        default=Path("reports/avera-decision.json"),
        help="Output path for the decision artifact.",
    )
    demo_refresh.add_argument(
        "--trend-out",
        type=Path,
        default=Path("reports/avera-trend-index.json"),
        help="Output path for the trend artifact.",
    )
    demo_refresh.add_argument(
        "--pack-out",
        type=Path,
        default=Path("reports/avera-workspace-pack.json"),
        help="Output path for the workspace pack.",
    )
    demo_refresh.add_argument(
        "--memory-limit",
        type=int,
        default=500,
        help="Number of newest memory records to include in traceability and trend.",
    )

    return parser


def run_analyze(project: Path, out: Path, memory: Path | None = None) -> int:
    validation = validate_workspace(project)
    if not validation.ok:
        print("AVERA workspace validation failed")
        for error in validation.errors:
            print(f"- {error}")
        return 2

    change_description = _read_optional_text(project / "change_description.txt")
    requirements = load_requirements(project / "requirements.csv")
    component_map = load_component_map(project / "component_map.json")
    baseline = load_verification_results(project / "baseline_results.json")
    current = load_verification_results(project / "current_results.json")

    comparison = compare_runs(baseline=baseline, current=current)
    assessment = classify_risk(
        comparison=comparison,
        requirements=requirements,
        component_map=component_map,
    )

    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "avera-report.json"
    markdown_path = out / "avera-report.md"
    graph_path = out / "avera-evidence-graph.json"

    report_payload = assessment_to_dict(assessment)
    _attach_signal_summary(project, report_payload)

    write_json_report(report_payload, json_path)
    write_markdown_report(report_payload, markdown_path)
    write_json_report(
        build_evidence_graph(report_payload, change_description=change_description),
        graph_path,
    )

    report_validation = validate_report(json.loads(json_path.read_text(encoding="utf-8")))
    if not report_validation.ok:
        print("AVERA report validation failed")
        for error in report_validation.errors:
            print(f"- {error}")
        return 2

    if memory is not None:
        append_analysis_record(
            memory,
            project=project,
            out=out,
            report_path=json_path,
            graph_path=graph_path,
            report=report_payload,
        )

    print("AVERA Change Impact")
    print(f"Verdict: {assessment.verdict}")
    print(f"Risk: {assessment.risk}")
    print(f"Confidence: {assessment.confidence}")
    print(f"Confidence score: {assessment.confidence_score:.2f}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    print(f"Evidence graph: {graph_path}")

    return 0


def run_validate_workspace(project: Path) -> int:
    validation = validate_workspace(project)
    print("AVERA Workspace Validation")
    print(f"Workspace: {validation.path}")
    print(f"OK: {validation.ok}")
    if validation.errors:
        print("Errors:")
        for error in validation.errors:
            print(f"- {error}")
    if validation.warnings:
        print("Warnings:")
        for warning in validation.warnings:
            print(f"- {warning}")
    return 0 if validation.ok else 2


def run_adapt_junit(input_path: Path, out: Path, run_id: str, stage: str) -> int:
    payload = adapt_junit_xml(input_path, run_id=run_id, stage=stage)
    write_json_report(payload, out)

    print("AVERA JUnit Adapter")
    print(f"Input: {input_path}")
    print(f"Output: {out}")
    print(f"Run ID: {payload['runId']}")
    print(f"Stage: {payload['stage']}")
    print(f"Tests: {len(payload['tests'])}")
    return 0


def run_adapt_simulation(input_path: Path, out: Path, run_id: str, stage: str) -> int:
    payload = adapt_simulation_csv(input_path, run_id=run_id, stage=stage)
    write_json_report(payload, out)

    print("AVERA Simulation Adapter")
    print(f"Input: {input_path}")
    print(f"Output: {out}")
    print(f"Run ID: {payload['runId']}")
    print(f"Stage: {payload['stage']}")
    print(f"Tests: {len(payload['tests'])}")
    return 0


def run_adapt_requirements(input_path: Path, out: Path) -> int:
    rows = adapt_requirements_csv(input_path)
    write_adapted_requirements(out, rows)

    print("AVERA Requirements Adapter")
    print(f"Input: {input_path}")
    print(f"Output: {out}")
    print(f"Rows: {len(rows)}")
    return 0


def run_adapt_logs(input_path: Path, out: Path, run_id: str, stage: str) -> int:
    payload = adapt_log_csv(input_path, run_id=run_id, stage=stage)
    write_json_report(payload, out)

    print("AVERA Log Adapter")
    print(f"Input: {input_path}")
    print(f"Output: {out}")
    print(f"Run ID: {payload['runId']}")
    print(f"Stage: {payload['stage']}")
    print(f"Tests: {len(payload['tests'])}")
    return 0


def run_fixtures(fixtures: Path, out: Path, memory: Path | None = None) -> int:
    expected_path = fixtures / "expected_outcomes.json"
    expected = {}
    if expected_path.exists():
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

    failures: list[str] = []
    for fixture in sorted(path for path in fixtures.iterdir() if path.is_dir()):
        target = out / fixture.name
        code = run_analyze(fixture, target, memory)
        if code != 0:
            failures.append(f"{fixture.name}: analyze failed with code {code}")
            continue
        try:
            report = json.loads((target / "avera-report.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{fixture.name}: invalid report JSON: {exc}")
            continue
        fixture_expected = expected.get(fixture.name)
        if fixture_expected:
            for key, expected_value in fixture_expected.items():
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


def run_gate(
    report: Path,
    max_risk: str | None = None,
    min_confidence_score: float | None = None,
    memory: Path | None = None,
    policy_name: str | None = None,
    policy_file: Path | None = None,
) -> int:
    payload = json.loads(report.read_text(encoding="utf-8"))

    policy = None
    if policy_file is not None:
        policy = load_policy(policy_file)
    elif policy_name is not None:
        policy = load_builtin_policy(policy_name)

    decision = evaluate_gate(
        payload,
        max_allowed_risk=max_risk,
        min_confidence_score=min_confidence_score,
        policy=policy,
    )

    print("AVERA Gate Decision")
    print(f"Policy: {decision.report_summary['policy_id']}")
    print(f"Status: {decision.status}")
    print(f"Verdict: {decision.report_summary['verdict']}")
    print(f"Risk: {decision.report_summary['risk']}")
    print(f"Confidence score: {decision.report_summary['confidence_score']:.2f}")
    print("Reasons:")
    for reason in decision.reasons:
        print(f"- {reason}")
    if memory is not None:
        append_gate_record(memory, report_path=report, decision=decision)
    return decision.exit_code


def run_memory(path: Path, limit: int) -> int:
    records = load_memory_records(path, limit=max(0, limit))
    summary = summarize_memory(records)

    print("AVERA Engineering Memory")
    print(f"Ledger: {path}")
    print(f"Records shown: {summary['total_records']}")
    print(f"By type: {summary['by_type']}")
    print(f"By verdict: {summary['by_verdict']}")
    print(f"By risk: {summary['by_risk']}")
    print(f"By gate status: {summary['by_gate_status']}")

    if records:
        print("Newest records:")
        for record in records:
            label = record.get("record_type", "unknown")
            verdict = record.get("verdict") or "unknown"
            risk = record.get("risk") or "unknown"
            gate_status = record.get("gate_status")
            suffix = f", gate {gate_status}" if gate_status else ""
            print(f"- {record.get('timestamp_utc')}: {label}, {verdict}, {risk}{suffix}")
    return 0


def run_traceability(report: Path, memory: Path, out: Path, memory_limit: int) -> int:
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    memory_records = load_memory_records(memory, limit=max(0, memory_limit))
    index = build_traceability_index(report_payload, memory_records)
    write_json_report(index, out)

    summary = index["summary"]
    print("AVERA Traceability Index")
    print(f"Report: {report}")
    print(f"Memory: {memory}")
    print(f"Output: {out}")
    print(f"Components: {summary['component_count']}")
    print(f"Requirements: {summary['requirement_count']}")
    print(f"Tests: {summary['test_count']}")
    print(f"Failures: {summary['failure_count']}")
    print(f"Memory analysis records: {summary['memory_analysis_records']}")
    print(f"Memory gate records: {summary['memory_gate_records']}")
    return 0


def run_decision(
    report: Path,
    gate: Path | None,
    traceability: Path | None,
    out: Path,
) -> int:
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    gate_payload = json.loads(gate.read_text(encoding="utf-8")) if gate else None
    traceability_payload = (
        json.loads(traceability.read_text(encoding="utf-8")) if traceability else None
    )
    decision = evaluate_decision(
        report=report_payload,
        gate=gate_payload,
        traceability=traceability_payload,
    )
    write_json_report(decision, out)

    print("AVERA Decision")
    print(f"Report: {report}")
    print(f"Output: {out}")
    print(f"Action: {decision['action']}")
    print(f"Category: {decision['category']}")
    print(f"Priority: {decision['priority']}")
    print(f"Owner: {decision['owner']}")
    return 0


def run_pack(
    workspace: Path,
    report: Path,
    markdown: Path | None,
    graph: Path | None,
    memory: Path | None,
    traceability: Path | None,
    decision: Path | None,
    trend: Path | None,
    out: Path,
    manifest_out: Path | None = None,
    audit_log: Path | None = None,
) -> int:
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    graph_payload = json.loads(graph.read_text(encoding="utf-8")) if graph and graph.exists() else None
    memory_records = load_memory_records(memory) if memory and memory.exists() else []
    traceability_payload = (
        json.loads(traceability.read_text(encoding="utf-8"))
        if traceability and traceability.exists()
        else None
    )
    decision_payload = (
        json.loads(decision.read_text(encoding="utf-8"))
        if decision and decision.exists()
        else None
    )
    trend_payload = (
        json.loads(trend.read_text(encoding="utf-8"))
        if trend and trend.exists()
        else None
    )

    pack = build_workspace_pack(
        workspace=workspace,
        report=report_payload,
        report_path=report,
        markdown_path=markdown,
        graph=graph_payload,
        graph_path=graph,
        memory_records=memory_records,
        memory_path=memory,
        traceability=traceability_payload,
        traceability_path=traceability,
        decision=decision_payload,
        decision_path=decision,
        trend=trend_payload,
        trend_path=trend,
    )
    write_workspace_pack(pack, out)

    # Emit the formal Evidence Manifest binding the run's artifacts (including the
    # workspace pack just written) under one content-addressed integrity root.
    manifest_path = manifest_out or (out.parent / "avera-evidence-manifest.json")
    manifest = build_evidence_manifest(
        workspace=workspace,
        artifacts={
            "report": (report_payload, report),
            "graph": (graph_payload, graph),
            "traceability": (traceability_payload, traceability),
            "decision": (decision_payload, decision),
            "trend": (trend_payload, trend),
            "workspace_pack": (pack, out),
        },
    )
    write_evidence_manifest(manifest, manifest_path)

    # Bind the manifest's integrity root into the immutable, hash-chained audit
    # log. This is the anchor a regulated sign-off later references.
    audit_log_path = audit_log or (out.parent / "avera-audit.jsonl")
    audit_record = record_manifest_in_audit_log(
        manifest, audit_log_path, manifest_path=manifest_path
    )

    print("AVERA Workspace Pack")
    print(f"Workspace: {workspace}")
    print(f"Output: {out}")
    print(f"Artifacts: {pack['manifest']['artifact_count']}")
    print(f"Missing: {pack['manifest']['missing_artifacts']}")
    print("AVERA Evidence Manifest")
    print(f"Manifest: {manifest_path}")
    print(f"Integrity root: {manifest.integrity_root}")
    print(f"Complete: {manifest.completeness['complete']}")
    print("AVERA Audit Log")
    print(f"Audit log: {audit_log_path}")
    print(f"Audit event: {audit_record.event} (seq {audit_record.seq})")
    print(f"Audit record hash: {audit_record.self_hash}")
    return 0


def run_trend(memory: Path, traceability: Path | None, out: Path, memory_limit: int) -> int:
    memory_records = load_memory_records(memory, limit=max(0, memory_limit))
    traceability_payload = (
        json.loads(traceability.read_text(encoding="utf-8"))
        if traceability and traceability.exists()
        else None
    )
    trend = build_trend_index(memory_records, traceability_payload)
    write_json_report(trend, out)

    summary = trend["summary"]
    print("AVERA Trend Index")
    print(f"Memory: {memory}")
    print(f"Output: {out}")
    print(f"Memory records: {summary['memory_record_count']}")
    print(f"Components tracked: {summary['component_count']}")
    print(f"Requirements tracked: {summary['requirement_count']}")
    print(f"Tests tracked: {summary['test_count']}")
    return 0


def run_validate_artifact(artifact: str, path: Path, bundle: bool) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = validate_bundle(payload) if bundle else validate_artifact(artifact, payload)

    print("AVERA Artifact Validation")
    print(f"Artifact: {artifact}")
    print(f"Path: {path}")
    print(f"OK: {result.ok}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"- {error}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    return 0 if result.ok else 1


def run_demo_refresh(
    project: Path,
    report_out: Path,
    memory: Path,
    traceability_out: Path,
    decision_out: Path,
    trend_out: Path,
    pack_out: Path,
    memory_limit: int,
) -> int:
    analyze_code = run_analyze(project, report_out, memory)
    if analyze_code != 0:
        return analyze_code

    report_path = report_out / "avera-report.json"
    markdown_path = report_out / "avera-report.md"
    graph_path = report_out / "avera-evidence-graph.json"

    traceability_code = run_traceability(report_path, memory, traceability_out, memory_limit)
    if traceability_code != 0:
        return traceability_code

    decision_code = run_decision(report_path, None, traceability_out, decision_out)
    if decision_code != 0:
        return decision_code

    trend_code = run_trend(memory, traceability_out, trend_out, memory_limit)
    if trend_code != 0:
        return trend_code

    pack_code = run_pack(
        project,
        report_path,
        markdown_path,
        graph_path,
        memory,
        traceability_out,
        decision_out,
        trend_out,
        pack_out,
    )
    if pack_code != 0:
        return pack_code

    manifest_out = pack_out.parent / "avera-evidence-manifest.json"
    audit_log_out = pack_out.parent / "avera-audit.jsonl"

    print("AVERA Demo Refresh")
    print(f"Project: {project}")
    print(f"Report dir: {report_out}")
    print(f"Traceability: {traceability_out}")
    print(f"Decision: {decision_out}")
    print(f"Trend: {trend_out}")
    print(f"Workspace pack: {pack_out}")
    print(f"Evidence manifest: {manifest_out}")
    print(f"Audit log: {audit_log_out}")
    return 0


def run_query(traceability: Path, kind: str, value: str) -> int:
    payload = json.loads(traceability.read_text(encoding="utf-8"))
    handlers = {
        "component": query_component,
        "requirement": query_requirement,
        "test": query_test,
        "risk": query_risk,
        "gate": query_gate_status,
    }
    result = handlers[kind](payload, value)

    print("AVERA Query")
    print(f"Traceability: {traceability}")
    print(f"Kind: {kind}")
    print(f"Value: {value}")
    if result is None:
        print("Match: none")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _read_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def _attach_signal_summary(project: Path, report_payload: dict[str, object]) -> None:
    signal_trace_path = project / "signal_trace.csv"
    if not signal_trace_path.exists():
        return
    signal_points = load_signal_trace(signal_trace_path)
    report_payload["signal_trace_points"] = len(signal_points)
    report_payload["signal_summary"] = summarize_signal_trace(signal_points)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        raise SystemExit(run_analyze(args.project, args.out, args.memory))
    if args.command == "adapt-junit":
        raise SystemExit(run_adapt_junit(args.input, args.out, args.run_id, args.stage))
    if args.command == "adapt-simulation":
        raise SystemExit(run_adapt_simulation(args.input, args.out, args.run_id, args.stage))
    if args.command == "adapt-requirements":
        raise SystemExit(run_adapt_requirements(args.input, args.out))
    if args.command == "adapt-logs":
        raise SystemExit(run_adapt_logs(args.input, args.out, args.run_id, args.stage))
    if args.command == "validate-workspace":
        raise SystemExit(run_validate_workspace(args.project))
    if args.command == "run-fixtures":
        raise SystemExit(run_fixtures(args.fixtures, args.out, args.memory))
    if args.command == "gate":
        raise SystemExit(
            run_gate(
                args.report,
                args.max_risk,
                args.min_confidence_score,
                args.memory,
                args.policy,
                args.policy_file,
            )
        )
    if args.command == "memory":
        raise SystemExit(run_memory(args.path, args.limit))
    if args.command == "traceability":
        raise SystemExit(
            run_traceability(
                args.report,
                args.memory,
                args.out,
                args.memory_limit,
            )
        )
    if args.command == "decision":
        raise SystemExit(
            run_decision(
                args.report,
                args.gate,
                args.traceability,
                args.out,
            )
        )
    if args.command == "pack":
        raise SystemExit(
            run_pack(
                args.workspace,
                args.report,
                args.markdown,
                args.graph,
                args.memory,
                args.traceability,
                args.decision,
                args.trend,
                args.out,
                args.manifest_out,
                args.audit_log,
            )
        )
    if args.command == "query":
        raise SystemExit(run_query(args.traceability, args.kind, args.value))
    if args.command == "trend":
        raise SystemExit(run_trend(args.memory, args.traceability, args.out, args.memory_limit))
    if args.command == "validate-artifact":
        raise SystemExit(run_validate_artifact(args.artifact, args.path, args.bundle))
    if args.command == "demo-refresh":
        raise SystemExit(
            run_demo_refresh(
                args.project,
                args.report_out,
                args.memory,
                args.traceability_out,
                args.decision_out,
                args.trend_out,
                args.pack_out,
                args.memory_limit,
            )
        )

    parser.error(f"Unknown command: {args.command}")
