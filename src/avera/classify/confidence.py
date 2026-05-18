"""Confidence taxonomy for AVERA classification."""

from __future__ import annotations

LOW = "low"
MEDIUM = "medium"
HIGH = "high"

ALL_CONFIDENCE_LEVELS = (
    LOW,
    MEDIUM,
    HIGH,
)

CONFIDENCE_RANK = {
    LOW: 1,
    MEDIUM: 2,
    HIGH: 3,
}

CONFIDENCE_BASE_SCORE = {
    LOW: 0.35,
    MEDIUM: 0.65,
    HIGH: 0.85,
}

VERDICT_SCORE_CAPS = {
    "environment_failure": 0.45,
    "insufficient_evidence": 0.45,
    "requirements_coverage_gap": 0.6,
    "possible_regression": 0.75,
}


def normalize_confidence(value: str | None, default: str = LOW) -> str:
    """Return a known confidence string without changing report shape."""

    normalized = str(value or "").strip().lower().replace("-", "_")
    return normalized if normalized in ALL_CONFIDENCE_LEVELS else default


def confidence_rank(value: str | None) -> int:
    """Return sortable rank for a confidence level."""

    return CONFIDENCE_RANK.get(normalize_confidence(value), 0)


def score_confidence(
    confidence: str | None,
    *,
    verdict: str | None = None,
    factors: list[str] | tuple[str, ...] = (),
) -> float:
    """Return a conservative 0..1 score while preserving the label taxonomy."""

    score = CONFIDENCE_BASE_SCORE[normalize_confidence(confidence)]
    for factor in factors:
        normalized = str(factor).strip()
        if normalized.startswith("+"):
            score += 0.03
        elif normalized.startswith("-"):
            score -= 0.05

    normalized_verdict = str(verdict or "").strip().lower().replace("-", "_")
    if normalized_verdict == "confirmed_regression":
        score += 0.05
    elif normalized_verdict in {"expected_change", "successful_change"}:
        score += 0.02

    cap = VERDICT_SCORE_CAPS.get(normalized_verdict, 0.95)
    return round(max(0.0, min(score, cap)), 2)
