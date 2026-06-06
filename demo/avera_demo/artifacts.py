from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import ArtifactEntry, ScenarioPaths, ScenarioProfile, ScenarioSummary, ShellSnapshot


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = PROJECT_ROOT / "fixtures"
REPORTS_ROOT = PROJECT_ROOT / "reports"
DEFAULT_SCENARIO = "bms-fast-charge"

SCENARIO_PROFILES: dict[str, ScenarioProfile] = {
    "bms-fast-charge": ScenarioProfile(
        domain="BMS",
        title="Fast-charge thermal regression",
        summary="A battery-management change introduces a measurable thermal regression during fast charging.",
        use_case="Primary canonical review path for release triage and proof-backed regression analysis.",
        primary_signal="max_cell_temp_c",
        fallback_note="Use this as the main live shell path in external demos.",
        pilot_track="standard",
    ),
    "bms-requirements-adapted": ScenarioProfile(
        domain="BMS",
        title="Adapted requirements export workspace",
        summary="A BMS regression workspace driven by a normalized ALM-style requirements export rather than only the canonical local requirements CSV.",
        use_case="Pilot-facing proof that AVERA can absorb richer requirements exports and still drive the same evidence-first review flow.",
        primary_signal="max_cell_temp_c / cooling_response_ms",
        fallback_note="Use this to show that external requirements exports can be normalized into a standard AVERA workspace before analysis.",
        pilot_track="adapted",
    ),
    "bms-log-adapted": ScenarioProfile(
        domain="BMS",
        title="Adapted verification log workspace",
        summary="A BMS regression workspace driven by normalized HIL verification log CSV artifacts rather than only hand-authored verification JSON.",
        use_case="Pilot-facing proof that richer verification logs can be turned into a normal AVERA review workspace without changing the kernel contract.",
        primary_signal="max_cell_temp_c / cooling_response_ms",
        fallback_note="Use this to show a log-heavy external evidence path feeding the same local review flow.",
        pilot_track="adapted",
    ),
    "adas-pedestrian-detection-regression": ScenarioProfile(
        domain="ADAS",
        title="Pedestrian detection regression",
        summary="An ADAS perception retune reduces pedestrian recall and delays braking in a mapped regression scenario.",
        use_case="Cross-domain proof that the same AVERA evidence model survives a change from BMS to ADAS.",
        primary_signal="pedestrian_recall / brake_trigger_latency_ms",
        fallback_note="If the live ADAS shell path is slow, use the static ADAS showcase asset for continuity.",
        pilot_track="standard",
    ),
    "adas-simulation-adapted": ScenarioProfile(
        domain="ADAS",
        title="Adapted simulation regression workspace",
        summary="A realistic ADAS workspace built from adapted simulation CSV artifacts instead of only hand-authored verification JSON.",
        use_case="Pilot-facing proof that AVERA can normalize external simulation evidence into its stable local review contract.",
        primary_signal="pedestrian_recall / brake_trigger_latency_ms",
        fallback_note="Use this to show the bridge from external artifacts into a normal AVERA workspace review flow.",
        pilot_track="adapted",
    ),
    # ── Aviation (DO-178C) ────────────────────────────────────────────────────
    "fadec-overspeed-regression": ScenarioProfile(
        domain="Aviation / DO-178C",
        title="FADEC overspeed response regression — DAL A",
        summary=(
            "A fuel-control change increases FADEC overspeed response latency from 42 ms to 63 ms, "
            "violating a DAL-A threshold of 50 ms. Verdict: confirmed_regression, risk: release_blocking."
        ),
        use_case=(
            "Cross-domain proof that AVERA handles aviation DO-178C safety levels at the highest "
            "assurance level (DAL A). Use in investor demos to show industry breadth."
        ),
        primary_signal="overspeed_response_ms",
        fallback_note="DAL-A is the most critical level — any regression is release-blocking by definition.",
        pilot_track="standard",
    ),
    "fcc-envelope-regression": ScenarioProfile(
        domain="Aviation / DO-178C",
        title="FCC envelope protection latency regression — DAL A",
        summary=(
            "A flight-control algorithm update raises envelope protection actuation latency from 148 ms "
            "to 247 ms, violating a DAL-A limit of 200 ms. Full release-blocking regression detected."
        ),
        use_case=(
            "Second aviation scenario for FCC showing AVERA generalises across "
            "avionics subsystems — engine control and flight envelope protection."
        ),
        primary_signal="envelope_engage_ms",
        fallback_note="Pair with FADEC scenario to demonstrate breadth within aviation domain.",
        pilot_track="standard",
    ),
    # ── Railway (EN-50128) ────────────────────────────────────────────────────
    "etcs-brake-response-regression": ScenarioProfile(
        domain="Railway / EN-50128",
        title="ETCS emergency brake response regression — SIL 4",
        summary=(
            "A priority-scheduler refactor in the brake controller raises emergency brake "
            "application time from 1047 ms to 1387 ms, exceeding the SIL 4 limit of 1200 ms. "
            "Verdict: confirmed_regression, risk: release_blocking."
        ),
        use_case=(
            "Third-domain proof that AVERA applies the same evidence model to rail safety — "
            "EN-50128 SIL 4 is the most stringent railway integrity level. "
            "Use in demos to show industry coverage beyond automotive and aviation."
        ),
        primary_signal="brake_application_ms",
        fallback_note="SIL 4 maps directly to release_blocking — any threshold breach stops the release.",
        pilot_track="standard",
    ),
    # ── Medical (IEC-62304) ───────────────────────────────────────────────────
    "infusion-pump-flow-regression": ScenarioProfile(
        domain="Medical / IEC-62304",
        title="Infusion pump flow rate regression — Class C",
        summary=(
            "A PID gain recalibration in the infusion pump flow controller raises steady-state "
            "deviation from 2.3% to 7.8%, violating the IEC-62304 Class C ceiling of 5.0%. "
            "Verdict: confirmed_regression, risk: high."
        ),
        use_case=(
            "Fourth-domain proof that AVERA handles medical device software under IEC-62304. "
            "Class C is the highest software safety class — life-threatening consequence. "
            "Completes the four-industry coverage story for the investor pitch."
        ),
        primary_signal="flow_rate_deviation_pct",
        fallback_note="IEC-62304 Class C pairs with ASIL-C rank — high risk, corrective action required before release.",
        pilot_track="standard",
    ),
    # ── Powertrain (Automotive) ───────────────────────────────────────────────
    "powertrain-overspeed-regression": ScenarioProfile(
        domain="Powertrain / ISO 26262",
        title="Powertrain overspeed regression — ASIL D",
        summary=(
            "An ECU torque-limiter update allows engine RPM to exceed the ASIL-D safety limit, "
            "producing a confirmed release-blocking regression."
        ),
        use_case=(
            "Expands the automotive story beyond BMS into powertrain — different subsystem, "
            "same AVERA evidence model. Demonstrates domain coverage within ISO 26262."
        ),
        primary_signal="engine_rpm",
        fallback_note="Use alongside BMS and ADAS scenarios to show full automotive breadth.",
        pilot_track="standard",
    ),
}


def list_scenarios() -> list[str]:
    if not FIXTURES_ROOT.exists():
        return []
    return sorted(path.name for path in FIXTURES_ROOT.iterdir() if path.is_dir())


def list_scenarios_for_track(track: str) -> list[str]:
    scenarios = list_scenarios()
    if track == "all":
        return scenarios
    if track not in {"standard", "adapted"}:
        return scenarios
    return [name for name in scenarios if build_profile(scenario_paths(name)).pilot_track == track]


def scenario_paths(name: str) -> ScenarioPaths:
    fixture_dir = FIXTURES_ROOT / name
    preferred_report_dir = REPORTS_ROOT / "fixtures" / name
    fallback_report_dir = REPORTS_ROOT / name
    report_dir = preferred_report_dir if preferred_report_dir.exists() else fallback_report_dir
    return ScenarioPaths(
        name=name,
        fixture_dir=fixture_dir,
        report_dir=report_dir,
        traceability_path=REPORTS_ROOT / "avera-traceability-index.json",
        decision_path=REPORTS_ROOT / "avera-decision.json",
        trend_path=REPORTS_ROOT / "avera-trend-index.json",
        pack_path=REPORTS_ROOT / "avera-workspace-pack.json",
        manifest_path=REPORTS_ROOT / "avera-evidence-manifest.json",
        audit_log_path=REPORTS_ROOT / "avera-audit.jsonl",
        memory_path=REPORTS_ROOT / "avera-memory.jsonl",
    )


def artifact_catalog(scenario: ScenarioPaths) -> list[ArtifactEntry]:
    artifacts = [
        ArtifactEntry("requirements", "Requirements", scenario.fixture_dir / "requirements.csv", "csv", True),
        ArtifactEntry("component_map", "Component Map", scenario.fixture_dir / "component_map.json", "json", True),
        ArtifactEntry("baseline_results", "Baseline Results", scenario.fixture_dir / "baseline_results.json", "json", True),
        ArtifactEntry("current_results", "Current Results", scenario.fixture_dir / "current_results.json", "json", True),
        ArtifactEntry("change_description", "Change Description", scenario.fixture_dir / "change_description.txt", "text"),
        ArtifactEntry("signal_trace", "Signal Trace", scenario.fixture_dir / "signal_trace.csv", "csv"),
        ArtifactEntry("report_json", "Assessment Report", scenario.report_dir / "avera-report.json", "json", True),
        ArtifactEntry("report_markdown", "Assessment Narrative", scenario.report_dir / "avera-report.md", "text"),
        ArtifactEntry("evidence_graph", "Evidence Graph", scenario.report_dir / "avera-evidence-graph.json", "json"),
        ArtifactEntry("traceability", "Traceability Index", scenario.traceability_path, "json"),
        ArtifactEntry("decision", "Decision", scenario.decision_path, "json"),
        ArtifactEntry("trend", "Trend Index", scenario.trend_path, "json"),
        ArtifactEntry("workspace_pack", "Workspace Pack", scenario.pack_path, "json"),
        ArtifactEntry("evidence_manifest", "Evidence Manifest", scenario.manifest_path, "json"),
        ArtifactEntry("audit_log", "Audit Log", scenario.audit_log_path, "text"),
        ArtifactEntry("memory", "Memory Log", scenario.memory_path, "text"),
    ]
    raw_sources = [
        ArtifactEntry(
            "requirements_export_variant",
            "Requirements Export Variant",
            scenario.fixture_dir / "requirements_export_variant.csv",
            "csv",
        ),
        ArtifactEntry(
            "baseline_verification_log",
            "Baseline Verification Log CSV",
            scenario.fixture_dir / "baseline_verification_log.csv",
            "csv",
        ),
        ArtifactEntry(
            "current_verification_log",
            "Current Verification Log CSV",
            scenario.fixture_dir / "current_verification_log.csv",
            "csv",
        ),
        ArtifactEntry("baseline_junit_xml", "Baseline JUnit XML", scenario.fixture_dir / "baseline_results.xml", "text"),
        ArtifactEntry("current_junit_xml", "Current JUnit XML", scenario.fixture_dir / "current_results.xml", "text"),
        ArtifactEntry(
            "baseline_simulation_csv",
            "Baseline Simulation CSV",
            scenario.fixture_dir / "baseline_simulation_results.csv",
            "csv",
        ),
        ArtifactEntry(
            "current_simulation_csv",
            "Current Simulation CSV",
            scenario.fixture_dir / "current_simulation_results.csv",
            "csv",
        ),
    ]
    return artifacts + [entry for entry in raw_sources if entry.path.exists()]


def load_snapshot(scenario: ScenarioPaths) -> ShellSnapshot:
    baseline = read_json(scenario.fixture_dir / "baseline_results.json")
    current = read_json(scenario.fixture_dir / "current_results.json")
    return ShellSnapshot(
        scenario=scenario,
        profile=build_profile(scenario),
        report=read_json(scenario.report_dir / "avera-report.json"),
        decision=read_json(scenario.decision_path),
        traceability=read_json(scenario.traceability_path),
        trend=read_json(scenario.trend_path),
        workspace_pack=read_json(scenario.pack_path),
        evidence_manifest=read_json(scenario.manifest_path),
        audit_log=read_text(scenario.audit_log_path),
        baseline_rows=flatten_results(baseline),
        current_rows=flatten_results(current),
        signal_rows=read_csv_rows(scenario.fixture_dir / "signal_trace.csv"),
        requirements_rows=read_csv_rows(scenario.fixture_dir / "requirements.csv"),
        change_description=read_text(scenario.fixture_dir / "change_description.txt"),
        artifacts=artifact_catalog(scenario),
    )


def build_profile(scenario: ScenarioPaths) -> ScenarioProfile:
    if scenario.name in SCENARIO_PROFILES:
        return SCENARIO_PROFILES[scenario.name]

    # Infer domain from fixture name prefix
    name = scenario.name
    if name.startswith(("fadec", "fcc", "dal", "avionics")):
        domain = "Aviation / DO-178C"
    elif name.startswith(("sil", "railway", "etcs", "cab")):
        domain = "Railway / EN-50128"
    elif name.startswith(("imd", "pump", "infusion", "medical")):
        domain = "Medical / IEC-62304"
    else:
        domain = "Automotive / ISO 26262"
    return ScenarioProfile(
        domain=domain,
        title=name.replace("-", " ").title(),
        summary="Local AVERA evidence workspace.",
        use_case="Inspect the prepared artifacts, review the generated evidence, and decide the next engineering step.",
        primary_signal="-",
        fallback_note="If the live shell is unstable, keep artifact outputs and static showcase assets ready for continuity.",
    )


def build_summary(snapshot: ShellSnapshot) -> ScenarioSummary:
    report = snapshot.report if isinstance(snapshot.report, dict) else {}
    decision = snapshot.decision if isinstance(snapshot.decision, dict) else {}
    pack = snapshot.workspace_pack if isinstance(snapshot.workspace_pack, dict) else {}
    present = sum(1 for artifact in snapshot.artifacts if artifact.path.exists())
    missing = len(snapshot.artifacts) - present
    confidence_score = report.get("confidence_score")
    return ScenarioSummary(
        verdict=value_or_dash(report, "verdict"),
        risk=value_or_dash(report, "risk"),
        confidence=value_or_dash(report, "confidence"),
        confidence_score=confidence_score if isinstance(confidence_score, int | float) else None,
        action=value_or_dash(decision, "action"),
        artifact_count=pack.get("manifest", {}).get("artifact_count") if isinstance(pack.get("manifest"), dict) else None,
        present_artifacts=present,
        missing_artifacts=missing,
    )


def read_artifact(entry: ArtifactEntry) -> Any:
    if entry.kind == "json":
        return read_json(entry.path)
    if entry.kind == "csv":
        return read_csv_rows(entry.path)
    return read_text(entry.path)


def read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    return json.loads(text)


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def flatten_results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    rows: list[dict[str, Any]] = []
    for key, value in payload.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    rows.append({"group": key, **item})
    return rows


def value_or_dash(payload: dict[str, Any] | list[Any] | None, key: str) -> str:
    if not isinstance(payload, dict):
        return "-"
    value = payload.get(key)
    return str(value) if value not in (None, "") else "-"
