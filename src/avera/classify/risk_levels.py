"""Risk level taxonomy and ranking helpers for AVERA classification."""

from __future__ import annotations

LOW = "low"
MEDIUM = "medium"
HIGH = "high"
RELEASE_BLOCKING = "release_blocking"
UNKNOWN = "unknown"
SAFETY_CRITICAL = "safety_critical"

ALL_RISK_LEVELS = (
    UNKNOWN,
    LOW,
    MEDIUM,
    HIGH,
    RELEASE_BLOCKING,
)

RISK_RANK = {
    LOW: 1,
    MEDIUM: 2,
    HIGH: 3,
    RELEASE_BLOCKING: 4,
}

SAFETY_LEVEL_RANK = {
    # Automotive ISO 26262 (ASIL) short and long forms
    "low": 1,
    "asil-a": 1,
    "asil_a": 1,
    "a": 1,
    "medium": 2,
    "asil-b": 2,
    "asil_b": 2,
    "b": 2,
    "high": 3,
    SAFETY_CRITICAL: 3,
    "safety-critical": 3,
    "safety_critical": 3,
    "asil-c": 3,
    "asil_c": 3,
    "c": 3,
    "release_blocking": 4,
    "release-blocking": 4,
    "asil-d": 4,
    "asil_d": 4,
    "d": 4,
    # Aviation DO-178C (DAL) — A=most critical, E=no safety effect
    # Single-letter forms are reserved for ASIL; always use dal-* prefix for aviation.
    "dal-e": 0,
    "dal_e": 0,
    "dale": 0,
    "dal-d": 1,
    "dal_d": 1,
    "dald": 1,
    "dal-c": 2,
    "dal_c": 2,
    "dalc": 2,
    "dal-b": 3,
    "dal_b": 3,
    "dalb": 3,
    "dal-a": 4,
    "dal_a": 4,
    "dala": 4,
    # Railway EN-50128 (SIL)
    "sil0": 0,
    "sil-0": 0,
    "sil1": 1,
    "sil-1": 1,
    "sil2": 2,
    "sil-2": 2,
    "sil3": 3,
    "sil-3": 3,
    "sil4": 4,
    "sil-4": 4,
    # Medical IEC-62304 — Class A (minor) / B (serious) / C (life-threatening)
    # Always use class-* prefix to avoid collision with ASIL single-letter forms.
    "class-a": 1,
    "class_a": 1,
    "iec-a": 1,
    "class-b": 2,
    "class_b": 2,
    "iec-b": 2,
    "class-c": 3,
    "class_c": 3,
    "iec-c": 3,
    # Space NASA NPR 7150.2 — software Class A (human-rated) .. F (general).
    # Six classes compressed onto the 0..4 scale (D and E -> minor). Always use
    # the nasa-* prefix to avoid collision with ASIL/IEC single-letter forms.
    "nasa-a": 4, "nasa_a": 4, "nasaa": 4,
    "nasa-b": 3, "nasa_b": 3, "nasab": 3,
    "nasa-c": 2, "nasa_c": 2, "nasac": 2,
    "nasa-d": 1, "nasa_d": 1, "nasad": 1,
    "nasa-e": 1, "nasa_e": 1, "nasae": 1,
    "nasa-f": 0, "nasa_f": 0, "nasaf": 0,
}


def normalize_risk_level(value: str | None, default: str = UNKNOWN) -> str:
    """Return a known risk level string while preserving existing string values."""
    normalized = str(value or "").strip().lower().replace("-", "_")
    return normalized if normalized in ALL_RISK_LEVELS else default


def risk_rank(value: str | None) -> int:
    """Return sortable rank for a risk level."""
    return RISK_RANK.get(normalize_risk_level(value), 0)


def safety_rank(value: object) -> int:
    """Return sortable rank for requirement safety labels."""
    normalized = str(value or "").strip().lower()
    return SAFETY_LEVEL_RANK.get(normalized, 0)
