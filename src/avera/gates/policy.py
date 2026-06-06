"""Deterministic gate policy for AVERA reports.

The gate is **deterministic** and **data-driven**. The thresholds and verdict
sets live in a :class:`GatePolicy`. The built-in :data:`DEFAULT_GATE_POLICY`
reproduces AVERA's original conservative behaviour exactly, so existing callers
that pass nothing (or the legacy ``max_allowed_risk`` / ``min_confidence_score``
keywords) are unaffected.

Domain policies (automotive, aviation, medical, railway, ai_agent, general) are
loaded from JSON files under ``policies/`` via :mod:`avera.gates.policy_loader`.
A policy only ever *parametrises* the same deterministic decision logic — it
never introduces non-deterministic behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Built-in default constants (kept for backward compatibility / direct import).
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Policy data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GatePolicy:
    """A versioned, data-driven gate policy.

    All fields parametrise the same deterministic decision logic in
    :func:`evaluate_gate`. Two policies applied to the same report are guaranteed
    to be individually deterministic.
    """

    policy_id: str
    max_allowed_risk: str
    min_confidence_score: float
    blocking_verdicts: frozenset[str]
    review_verdicts: frozenset[str]
    risk_rank: dict[str, int] = field(default_factory=lambda: dict(RISK_RANK))
    domain: str = "general"
    schema_version: str = "avera.gate_policy.v1"


# The built-in default reproduces AVERA's original hardcoded behaviour exactly.
DEFAULT_GATE_POLICY = GatePolicy(
    policy_id="general.builtin.v1",
    max_allowed_risk="medium",
    min_confidence_score=0.5,
    blocking_verdicts=frozenset(BLOCKING_VERDICTS),
    review_verdicts=frozenset(REVIEW_VERDICTS),
    risk_rank=dict(RISK_RANK),
    domain="general",
)


@dataclass(frozen=True)
class GateDecision:
    status: str
    exit_code: int
    reasons: list[str] = field(default_factory=list)
    report_summary: dict[str, Any] = field(default_factory=dict)


def evaluate_gate(
    report: dict[str, Any],
    *,
    max_allowed_risk: str | None = None,
    min_confidence_score: float | None = None,
    policy: GatePolicy | None = None,
) -> GateDecision:
    """Evaluate a generated AVERA report against a deterministic gate policy.

    Parameters
    ----------
    report:
        A generated AVERA report dict.
    max_allowed_risk, min_confidence_score:
        Legacy per-call overrides. When provided they take precedence over the
        policy. When ``None`` the policy's value is used. Omitting both reproduces
        the original default behaviour.
    policy:
        A :class:`GatePolicy`. Defaults to :data:`DEFAULT_GATE_POLICY`, which is
        byte-for-byte equivalent to the original hardcoded gate.
    """

    active = policy or DEFAULT_GATE_POLICY
    effective_max_risk = (
        max_allowed_risk if max_allowed_risk is not None else active.max_allowed_risk
    )
    effective_min_conf = (
        min_confidence_score if min_confidence_score is not None else active.min_confidence_score
    )
    risk_rank_map = active.risk_rank or RISK_RANK

    verdict = str(report.get("verdict") or "insufficient_evidence")
    risk = str(report.get("risk") or "unknown")
    confidence_score = _float(report.get("confidence_score"), default=0.0)
    risk_rank = risk_rank_map.get(risk, 0)
    max_risk_rank = risk_rank_map.get(effective_max_risk, RISK_RANK["medium"])

    reasons: list[str] = []
    status = "pass"

    if verdict in active.blocking_verdicts:
        status = "block"
        reasons.append(f"blocking verdict: {verdict}")

    if risk_rank > max_risk_rank:
        status = "block"
        reasons.append(f"risk {risk} exceeds allowed risk {effective_max_risk}")

    if status != "block" and verdict in active.review_verdicts:
        status = "review"
        reasons.append(f"manual review verdict: {verdict}")

    if status != "block" and confidence_score < effective_min_conf:
        status = "review"
        reasons.append(
            f"confidence_score {confidence_score:.2f} below minimum {effective_min_conf:.2f}"
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
            "max_allowed_risk": effective_max_risk,
            "min_confidence_score": effective_min_conf,
            "policy_id": active.policy_id,
        },
    )


def _float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
