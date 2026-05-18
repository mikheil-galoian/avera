"""Deterministic gate policy for AVERA reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


RISK_RANK = {
    "unknown": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "release_blocking": 4,
    "safety_critical": 5,
}

BLOCKING_VERDICTS = {
    "confirmed_regression",
    "worsened_preexisting_failure",
}

REVIEW_VERDICTS = {
    "environment_failure",
    "insufficient_evidence",
    "possible_regression",
    "requirements_coverage_gap",
}


@dataclass(frozen=True)
class GateDecision:
    status: str
    exit_code: int
    reasons: list[str] = field(default_factory=list)
    report_summary: dict[str, Any] = field(default_factory=dict)


def evaluate_gate(
    report: dict[str, Any],
    *,
    max_allowed_risk: str = "medium",
    min_confidence_score: float = 0.5,
) -> GateDecision:
    """Evaluate a generated AVERA report against a conservative gate policy."""

    verdict = str(report.get("verdict") or "insufficient_evidence")
    risk = str(report.get("risk") or "unknown")
    confidence_score = _float(report.get("confidence_score"), default=0.0)
    risk_rank = RISK_RANK.get(risk, 0)
    max_risk_rank = RISK_RANK.get(max_allowed_risk, RISK_RANK["medium"])

    reasons: list[str] = []
    status = "pass"

    if verdict in BLOCKING_VERDICTS:
        status = "block"
        reasons.append(f"blocking verdict: {verdict}")

    if risk_rank > max_risk_rank:
        status = "block"
        reasons.append(f"risk {risk} exceeds allowed risk {max_allowed_risk}")

    if status != "block" and verdict in REVIEW_VERDICTS:
        status = "review"
        reasons.append(f"manual review verdict: {verdict}")

    if status != "block" and confidence_score < min_confidence_score:
        status = "review"
        reasons.append(
            f"confidence_score {confidence_score:.2f} below minimum {min_confidence_score:.2f}"
        )

    if not reasons:
        reasons.append("report satisfies gate policy")

    return GateDecision(
        status=status,
        exit_code=0 if status == "pass" else 1,
        reasons=reasons,
        report_summary={
            "schema_version": report.get("schema_version"),
            "verdict": verdict,
            "risk": risk,
            "confidence": report.get("confidence"),
            "confidence_score": confidence_score,
            "max_allowed_risk": max_allowed_risk,
            "min_confidence_score": min_confidence_score,
        },
    )


def _float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
