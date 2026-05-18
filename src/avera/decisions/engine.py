"""Decision engine for turning AVERA evidence into engineering actions."""

from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "avera.decision.v0.2"


def evaluate_decision(
    report: dict[str, Any],
    gate: dict[str, Any] | None = None,
    traceability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a conservative engineering decision from report, gate, and traceability."""

    verdict = str(report.get("verdict") or "insufficient_evidence")
    risk = str(report.get("risk") or "unknown")
    confidence = str(report.get("confidence") or "low")
    confidence_score = _float(report.get("confidence_score"), default=0.0)
    gate_status = _gate_status(gate)
    component_count = _count(traceability, "components")
    requirement_count = _count(traceability, "requirements")
    test_count = _count(traceability, "tests")
    top_components = _top_component_names(traceability, report)
    owner_routing = _owner_routing(verdict, top_components)

    if gate_status == "block" or verdict in {"confirmed_regression", "worsened_preexisting_failure"}:
        action = "block"
        category = "containment_required"
        priority = "immediate"
        release_recommendation = "do_not_release"
        owner = owner_routing["primary_owner"]
        actions = [
            "freeze_release_candidate",
            "reproduce_failure_on_target_test_path",
            "inspect_changed_component_and_requirement_links",
            "open_corrective_action_loop",
        ]
        corrective_actions = [
            "prepare_root_cause_ticket",
            "assign_fix_owner_for_affected_component",
            "capture_reproduction_artifacts",
        ]
        verification_playbook = [
            "rerun_failed_test_path",
            "rerun_threshold_checks_for_affected_requirements",
            "compare_against_last_passing_baseline",
        ]
        escalation = {
            "level": "program_blocker",
            "notify": ["component_owner", "validation_lead", "release_manager"],
        }
    elif verdict == "successful_change":
        action = "allow"
        category = "release_candidate"
        priority = "normal"
        release_recommendation = "release_allowed"
        owner = owner_routing["primary_owner"]
        actions = [
            "keep_regression_checks_attached_to_change",
            "archive_evidence_pack",
            "monitor_post_release_signals",
        ]
        corrective_actions = []
        verification_playbook = [
            "archive_passing_evidence",
            "schedule_post_release_signal_monitoring",
        ]
        escalation = {
            "level": "none",
            "notify": ["component_owner"],
        }
    elif verdict in {"insufficient_evidence", "requirements_coverage_gap"}:
        action = "review"
        category = "verification_gap"
        priority = "high"
        release_recommendation = "manual_review_required"
        owner = owner_routing["primary_owner"]
        actions = [
            "expand_requirement_coverage",
            "run_missing_verification_paths",
            "refresh_traceability_links",
        ]
        corrective_actions = [
            "map_missing_requirements_to_tests",
            "request_missing_evidence_artifacts",
        ]
        verification_playbook = [
            "run_uncovered_requirement_checks",
            "validate_traceability_links_before_rerun",
        ]
        escalation = {
            "level": "review_required",
            "notify": ["requirements_owner", "validation_lead"],
        }
    elif verdict == "environment_failure":
        action = "review"
        category = "environment_recheck"
        priority = "high"
        release_recommendation = "manual_review_required"
        owner = owner_routing["primary_owner"]
        actions = [
            "stabilize_environment",
            "rerun_verification",
            "separate_environmental_and_product_failures",
        ]
        corrective_actions = [
            "collect_lab_or_ci_diagnostics",
            "quarantine_environment_noise_from_product_signal",
        ]
        verification_playbook = [
            "rerun_same_test_in_clean_environment",
            "compare_environment_signatures_with_previous_runs",
        ]
        escalation = {
            "level": "lab_attention",
            "notify": ["ci_or_lab_owner", "validation_lead"],
        }
    else:
        action = "review"
        category = "manual_assessment"
        priority = "normal"
        release_recommendation = "manual_review_required"
        owner = owner_routing["primary_owner"]
        actions = [
            "review_traceability_index",
            "review_recent_memory_records",
            "decide_next_verification_step",
        ]
        corrective_actions = [
            "triage_with_cross_functional_review",
        ]
        verification_playbook = [
            "review_evidence_chain_end_to_end",
        ]
        escalation = {
            "level": "engineering_review",
            "notify": ["engineering_review_board"],
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "action": action,
        "status": action,
        "category": category,
        "priority": priority,
        "release_recommendation": release_recommendation,
        "owner": owner,
        "owner_routing": owner_routing,
        "verdict": verdict,
        "risk": risk,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "gate_status": gate_status,
        "actions": actions,
        "corrective_actions": corrective_actions,
        "verification_playbook": verification_playbook,
        "escalation": escalation,
        "context": {
            "component_count": component_count,
            "requirement_count": requirement_count,
            "test_count": test_count,
            "top_components": top_components,
        },
        "rationale": _rationale(verdict, risk, confidence_score, gate_status),
    }


def _gate_status(gate: dict[str, Any] | None) -> str | None:
    if not gate:
        return None
    for field in ("status", "gate_status"):
        value = gate.get(field)
        if value is not None:
            return str(value)
    return None


def _count(traceability: dict[str, Any] | None, field: str) -> int:
    if not traceability:
        return 0
    value = traceability.get(field)
    return len(value) if isinstance(value, list | dict) else 0


def _float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _rationale(
    verdict: str,
    risk: str,
    confidence_score: float,
    gate_status: str | None,
) -> list[str]:
    reasons = [f"verdict:{verdict}", f"risk:{risk}", f"confidence_score:{confidence_score:.2f}"]
    if gate_status:
        reasons.append(f"gate:{gate_status}")
    return reasons


def _top_component_names(traceability: dict[str, Any] | None, report: dict[str, Any]) -> list[str]:
    values = report.get("affected_components") or []
    if isinstance(values, str):
        values = [values]
    preferred = [str(value).strip() for value in values if str(value).strip()]
    if preferred:
        return preferred[:3]

    if traceability and isinstance(traceability.get("components"), list):
        names = [
            str(item.get("component") or "").strip()
            for item in traceability["components"]
            if isinstance(item, dict)
        ]
        names = [name for name in names if name]
        if names:
            return names[:3]
    return []


def _owner_routing(verdict: str, top_components: list[str]) -> dict[str, Any]:
    component = top_components[0] if top_components else "unmapped_component"
    if verdict in {"confirmed_regression", "worsened_preexisting_failure"}:
        primary_owner = "validation_and_component_owner"
        supporting = ["release_manager", "requirements_owner"]
    elif verdict in {"insufficient_evidence", "requirements_coverage_gap"}:
        primary_owner = "test_and_requirements_owner"
        supporting = ["component_owner", "validation_lead"]
    elif verdict == "environment_failure":
        primary_owner = "ci_or_lab_owner"
        supporting = ["validation_lead"]
    elif verdict == "successful_change":
        primary_owner = "component_owner"
        supporting = ["release_manager"]
    else:
        primary_owner = "engineering_review_board"
        supporting = ["component_owner"]
    return {
        "primary_owner": primary_owner,
        "supporting_owners": supporting,
        "focus_component": component,
    }
