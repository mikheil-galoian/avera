from __future__ import annotations

import json
from typing import Any

import streamlit as st

from .artifacts import build_summary, read_artifact
from .models import ArtifactEntry, ScenarioPaths, ShellSnapshot


def render_sidebar(snapshot: ShellSnapshot) -> tuple[bool, bool]:
    scenario = snapshot.scenario
    st.sidebar.markdown("### Workspace")
    st.sidebar.code(str(scenario.fixture_dir), language="text")
    st.sidebar.code(str(scenario.report_dir), language="text")
    run_col, refresh_col = st.sidebar.columns(2)
    run_requested = run_col.button("Analyze", use_container_width=True)
    refresh_requested = refresh_col.button("Refresh", use_container_width=True)
    return run_requested, refresh_requested


def render_shell(snapshot: ShellSnapshot) -> None:
    render_header(snapshot)
    render_operator_strip(snapshot)
    render_artifact_strip(snapshot)

    overview_tab, evidence_tab, traceability_tab, workspace_tab, artifacts_tab = st.tabs(
        ["Overview", "Evidence", "Traceability", "Workspace", "Artifacts"]
    )
    with overview_tab:
        render_overview(snapshot)
    with evidence_tab:
        render_evidence(snapshot)
    with traceability_tab:
        render_traceability(snapshot)
    with workspace_tab:
        render_workspace(snapshot)
    with artifacts_tab:
        render_artifacts(snapshot)


def render_header(snapshot: ShellSnapshot) -> None:
    summary = build_summary(snapshot)
    st.title("AVERA Demo Shell")
    st.caption("Artifact-first local review surface for AVERA evidence workspaces")

    profile = snapshot.profile
    st.markdown(f"**{profile.domain}** | **{profile.title}**")
    st.write(profile.summary)
    st.caption(
        "Adapted pilot set" if profile.pilot_track == "adapted" else "Standard scenario set"
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Verdict", summary.verdict)
    col2.metric("Risk", summary.risk)
    col3.metric(
        "Confidence",
        summary.confidence,
        delta=f"{summary.confidence_score:.2f}" if summary.confidence_score is not None else None,
    )
    col4.metric("Decision", summary.action)
    col5.metric("Pack Artifacts", summary.artifact_count if summary.artifact_count is not None else "-")
    col6.metric("Files Present", f"{summary.present_artifacts}/{len(snapshot.artifacts)}")

    if summary.missing_artifacts:
        st.warning(f"{summary.missing_artifacts} expected artifact(s) are missing for this scenario.")
    else:
        st.success("All expected demo artifacts for this scenario are available.")


def render_operator_strip(snapshot: ShellSnapshot) -> None:
    profile = snapshot.profile
    left, middle, right = st.columns([1.0, 1.0, 1.1])
    with left:
        st.markdown("#### Use Case")
        st.write(profile.use_case)
    with middle:
        st.markdown("#### Primary Signal")
        st.code(profile.primary_signal, language="text")
    with right:
        st.markdown("#### Operator Note")
        st.write(profile.fallback_note)

    adapted_rows = build_adapted_source_rows(snapshot)
    if adapted_rows:
        with st.expander("Adapted Pilot Mode", expanded=True):
            st.markdown(
                "This scenario includes raw external artifacts alongside normalized AVERA workspace files. "
                "Use it to explain how upstream evidence is adapted before the normal review flow begins."
            )
            st.dataframe(adapted_rows, use_container_width=True, hide_index=True)


def render_artifact_strip(snapshot: ShellSnapshot) -> None:
    rows = []
    for artifact in snapshot.artifacts:
        rows.append(
            {
                "artifact": artifact.label,
                "required": artifact.required,
                "status": "ready" if artifact.path.exists() else "missing",
                "path": str(artifact.path),
            }
        )
    st.markdown("#### Artifact Inventory")
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_overview(snapshot: ShellSnapshot) -> None:
    report = snapshot.report if isinstance(snapshot.report, dict) else None
    decision = snapshot.decision if isinstance(snapshot.decision, dict) else None
    if not report:
        st.info("No report artifact yet. Run Analyze or point the shell at a prepared workspace.")
        return

    left, right = st.columns([1.15, 0.85])
    with left:
        if snapshot.change_description:
            with st.expander("Change Description", expanded=True):
                st.write(snapshot.change_description.strip())

        st.markdown("#### What Changed")
        summary_table = [
            {"field": "Scenario", "value": snapshot.scenario.name},
            {"field": "Domain", "value": snapshot.profile.domain},
            {"field": "Affected components", "value": ", ".join(report.get("affected_components", [])) or "-"},
            {"field": "Affected files", "value": ", ".join(report.get("affected_files", [])) or "-"},
            {
                "field": "Recommended checks",
                "value": ", ".join(report.get("recommended_next_checks", [])) or "-",
            },
        ]
        st.dataframe(summary_table, use_container_width=True, hide_index=True)

        evidence_summary = report.get("evidence_summary", [])
        st.markdown("#### Evidence Narrative")
        if evidence_summary:
            for line in evidence_summary:
                st.write(f"- {line}")
        else:
            st.caption("No evidence summary in the report artifact.")

    with right:
        st.markdown("#### Release Decision")
        if decision:
            summary_rows, rationale, corrective_actions, verification_playbook, escalation = build_decision_review(decision)
            st.dataframe(summary_rows, use_container_width=True, hide_index=True)

            if rationale:
                st.markdown("##### Decision Rationale")
                for item in rationale:
                    st.write(f"- {item}")

            if corrective_actions:
                st.markdown("##### Corrective Actions")
                for item in corrective_actions:
                    st.write(f"- {item}")

            if verification_playbook:
                st.markdown("##### Verification Playbook")
                for item in verification_playbook:
                    st.write(f"- {item}")

            if escalation:
                st.markdown("##### Escalation")
                st.info(escalation)
        else:
            st.info("Decision artifact not found.")

        with st.expander("Operator Sequence", expanded=True):
            st.markdown(
                "\n".join(
                    [
                        "1. Validate the workspace",
                        "2. Run analysis",
                        "3. Review traceability and decision",
                        "4. Validate the workspace pack",
                        "5. Hand off the artifact bundle for human review",
                    ]
                )
            )

    st.markdown("#### Requirement Impact")
    requirement_rows = normalize_requirement_rows(report.get("affected_requirements", []))
    if requirement_rows:
        st.dataframe(requirement_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("No affected requirements were recorded in the report.")


def render_evidence(snapshot: ShellSnapshot) -> None:
    report = snapshot.report if isinstance(snapshot.report, dict) else None
    if not report:
        st.info("No evidence report available yet.")
        return

    left, right = st.columns(2)
    with left:
        st.markdown("#### Comparison Summary")
        st.json(report.get("comparison_summary", {}), expanded=2)
        st.markdown("#### Threshold Evidence")
        threshold_rows = report.get("threshold_evidence", [])
        if threshold_rows:
            st.dataframe(threshold_rows, use_container_width=True, hide_index=True)
        else:
            st.caption("No threshold evidence captured.")
    with right:
        st.markdown("#### Confidence Factors")
        st.json(report.get("confidence_factors", []), expanded=2)
        st.markdown("#### Risk Drivers")
        st.json(report.get("risk_drivers", []), expanded=2)

    if snapshot.baseline_rows or snapshot.current_rows:
        st.markdown("#### Baseline vs Current")
        base_col, current_col = st.columns(2)
        base_col.caption("Baseline")
        base_col.dataframe(snapshot.baseline_rows, use_container_width=True, hide_index=True)
        current_col.caption("Current")
        current_col.dataframe(snapshot.current_rows, use_container_width=True, hide_index=True)

    if snapshot.signal_rows:
        st.markdown("#### Signal Trace")
        st.dataframe(snapshot.signal_rows, use_container_width=True, hide_index=True)


def render_traceability(snapshot: ShellSnapshot) -> None:
    traceability = snapshot.traceability if isinstance(snapshot.traceability, dict) else None
    decision = snapshot.decision if isinstance(snapshot.decision, dict) else None
    if not traceability:
        st.info("No traceability artifact available yet.")
        return

    counts = build_traceability_counts(traceability)
    left, right = st.columns(2)
    left.markdown("#### Index Summary")
    left.json(traceability.get("summary", {}), expanded=2)
    right.markdown("#### Owner Routing")
    right.json((decision or {}).get("owner_routing", {}), expanded=2)

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Components", counts["components"])
    metric_b.metric("Requirements", counts["requirements"])
    metric_c.metric("Tests", counts["tests"])

    render_traceability_review(traceability)
    render_traceability_raw(traceability)


def render_workspace(snapshot: ShellSnapshot) -> None:
    pack = snapshot.workspace_pack if isinstance(snapshot.workspace_pack, dict) else None
    trend = snapshot.trend if isinstance(snapshot.trend, dict) else None

    left, right = st.columns([0.9, 1.1])
    with left:
        st.markdown("#### Source Inputs")
        input_rows = [
            {"artifact": "Requirements", "rows": len(snapshot.requirements_rows), "path": str(snapshot.scenario.fixture_dir / "requirements.csv")},
            {"artifact": "Signal trace", "rows": len(snapshot.signal_rows), "path": str(snapshot.scenario.fixture_dir / "signal_trace.csv")},
            {"artifact": "Change description", "rows": 1 if snapshot.change_description else 0, "path": str(snapshot.scenario.fixture_dir / "change_description.txt")},
        ]
        st.dataframe(input_rows, use_container_width=True, hide_index=True)

        st.markdown("#### Change Context")
        if snapshot.change_description:
            st.code(snapshot.change_description.strip(), language="text")
        else:
            st.caption("No local change description for this scenario.")

        with st.expander("Pilot-Use Mode", expanded=True):
            st.markdown(
                "\n".join(
                    [
                        "1. Confirm runtime and workspace health",
                        "2. Regenerate artifacts if the evidence is stale",
                        "3. Review decision and traceability before release discussion",
                        "4. Validate the workspace pack for handoff",
                        "5. Use the pack and narrative as the human review boundary",
                    ]
                )
            )

        adapted_rows = build_adapted_source_rows(snapshot)
        if adapted_rows:
            st.markdown("#### Adapted Source Boundary")
            st.dataframe(adapted_rows, use_container_width=True, hide_index=True)

    with right:
        st.markdown("#### Workspace Pack Summary")
        if pack:
            st.json(pack.get("summary", {}), expanded=2)
            st.download_button(
                "Download workspace pack JSON",
                data=json.dumps(pack, indent=2, sort_keys=True),
                file_name="avera-workspace-pack.json",
                mime="application/json",
            )
        else:
            st.info("No workspace pack available yet.")

        st.markdown("#### Handoff Readiness")
        st.dataframe(build_workspace_readiness_rows(snapshot), use_container_width=True, hide_index=True)

        st.markdown("#### Trend Snapshot")
        if trend:
            st.json(trend.get("summary", {}), expanded=2)
        else:
            st.caption("Trend artifact not found.")


def render_artifacts(snapshot: ShellSnapshot) -> None:
    labels = {artifact.label: artifact for artifact in snapshot.artifacts}
    selected_label = st.selectbox("Artifact", list(labels))
    render_artifact_view(labels[selected_label])


def render_artifact_view(entry: ArtifactEntry) -> None:
    st.code(str(entry.path), language="text")
    payload = read_artifact(entry)
    if payload in (None, [], ""):
        st.warning("Artifact not found or empty.")
        return

    if entry.kind == "json":
        st.json(payload, expanded=False)
    elif entry.kind == "csv":
        st.dataframe(payload, use_container_width=True, hide_index=True)
    else:
        st.code(str(payload), language="text")


def normalize_requirement_rows(payload: list[dict[str, Any]] | Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []

    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "id": item.get("id", "-"),
                "component": item.get("component", "-"),
                "metric": item.get("metric", "-"),
                "threshold": item.get("threshold", "-"),
                "operator": item.get("operator", "-"),
                "safety_level": item.get("safety_level", "-"),
                "next_checks": ", ".join(item.get("next_checks", [])) if isinstance(item.get("next_checks"), list) else "-",
            }
        )
    return rows


def render_traceability_review(traceability: dict[str, Any]) -> None:
    components = normalize_bucket(traceability.get("components"), "component")
    requirements = normalize_bucket(traceability.get("requirements"), "requirement")
    tests = normalize_bucket(traceability.get("tests"), "test")

    st.markdown("#### Review Navigation")
    review_mode = st.radio(
        "Traceability focus",
        ["Component", "Requirement", "Test"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if review_mode == "Component" and components:
        selected = st.selectbox("Component", [item["label"] for item in components], key="trace_component")
        entry = next(item for item in components if item["label"] == selected)
        render_traceability_entry(entry, "component")
    elif review_mode == "Requirement" and requirements:
        selected = st.selectbox("Requirement", [item["label"] for item in requirements], key="trace_requirement")
        entry = next(item for item in requirements if item["label"] == selected)
        render_traceability_entry(entry, "requirement")
    elif review_mode == "Test" and tests:
        selected = st.selectbox("Test", [item["label"] for item in tests], key="trace_test")
        entry = next(item for item in tests if item["label"] == selected)
        render_traceability_entry(entry, "test")
    else:
        st.caption("No structured traceability entries are available for focused review.")


def render_traceability_entry(entry: dict[str, Any], kind: str) -> None:
    payload = entry["payload"]
    left, right = st.columns([0.95, 1.05])

    with left:
        st.markdown(f"##### {kind.title()} Summary")
        rows = [
            {"field": kind.title(), "value": entry["label"]},
            {"field": "Requirements", "value": ", ".join(payload.get("requirements", [])) or "-"},
            {"field": "Tests", "value": ", ".join(payload.get("tests", [])) or "-"},
            {"field": "Failures", "value": str(len(payload.get("failures", [])))},
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        if payload.get("threshold_evidence"):
            st.markdown("##### Threshold Evidence")
            st.dataframe(payload.get("threshold_evidence", []), use_container_width=True, hide_index=True)

    with right:
        st.markdown("##### Decision / History")
        st.json(
            {
                "risk_history": payload.get("risk_history", []),
                "gate_history": payload.get("gate_history", []),
            },
            expanded=False,
        )


def render_traceability_raw(traceability: dict[str, Any]) -> None:
    with st.expander("Raw Traceability Data", expanded=False):
        for key in ("components", "requirements", "tests", "gates", "risks"):
            payload = traceability.get(key)
            if payload:
                st.markdown(f"##### {key.replace('_', ' ').title()}")
                st.json(payload, expanded=False)


def normalize_bucket(payload: Any, label_key: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []

    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        label = item.get(label_key) or item.get("id") or item.get("name") or "-"
        rows.append({"label": str(label), "payload": item})
    return rows


def build_decision_review(decision: dict[str, Any]) -> tuple[list[dict[str, str]], list[str], list[str], list[str], str | None]:
    summary_rows = [
        {"field": "Action", "value": as_text(decision.get("action"))},
        {"field": "Category", "value": as_text(decision.get("category"))},
        {"field": "Priority", "value": as_text(decision.get("priority"))},
        {"field": "Owner", "value": as_text(decision.get("owner"))},
        {"field": "Release Recommendation", "value": as_text(decision.get("release_recommendation"))},
    ]
    rationale = normalize_string_list(decision.get("rationale"))
    corrective_actions = normalize_string_list(decision.get("corrective_actions"))
    verification_playbook = normalize_string_list(decision.get("verification_playbook"))
    escalation = as_optional_text(decision.get("escalation"))
    return summary_rows, rationale, corrective_actions, verification_playbook, escalation


def build_traceability_counts(traceability: dict[str, Any]) -> dict[str, int]:
    return {
        "components": len(normalize_bucket(traceability.get("components"), "component")),
        "requirements": len(normalize_bucket(traceability.get("requirements"), "requirement")),
        "tests": len(normalize_bucket(traceability.get("tests"), "test")),
    }


def build_workspace_readiness_rows(snapshot: ShellSnapshot) -> list[dict[str, str]]:
    checks = [
        ("Assessment report", isinstance(snapshot.report, dict)),
        ("Decision artifact", isinstance(snapshot.decision, dict)),
        ("Traceability index", isinstance(snapshot.traceability, dict)),
        ("Workspace pack", isinstance(snapshot.workspace_pack, dict)),
        ("Trend artifact", isinstance(snapshot.trend, dict)),
        ("Change description", bool(snapshot.change_description)),
    ]
    return [
        {"check": label, "status": "ready" if ok else "missing", "next_step": "review" if ok else "regenerate or supply artifact"}
        for label, ok in checks
    ]


def build_adapted_source_rows(snapshot: ShellSnapshot) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for artifact in snapshot.artifacts:
        if not artifact.path.exists():
            continue
        if artifact.key in {
            "requirements_export_variant",
            "baseline_verification_log",
            "current_verification_log",
            "baseline_simulation_csv",
            "current_simulation_csv",
            "baseline_junit_xml",
            "current_junit_xml",
        }:
            rows.append(
                {
                    "source_artifact": artifact.label,
                    "normalized_target": infer_normalized_target(artifact.key),
                    "path": str(artifact.path),
                }
            )
    return rows


def infer_normalized_target(key: str) -> str:
    mapping = {
        "requirements_export_variant": "requirements.csv",
        "baseline_verification_log": "baseline_results.json",
        "current_verification_log": "current_results.json",
        "baseline_simulation_csv": "baseline_results.json",
        "current_simulation_csv": "current_results.json",
        "baseline_junit_xml": "baseline_results.json",
        "current_junit_xml": "current_results.json",
    }
    return mapping.get(key, "-")


def normalize_string_list(payload: Any) -> list[str]:
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload if item not in (None, "")]


def as_text(value: Any) -> str:
    return str(value) if value not in (None, "") else "-"


def as_optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
