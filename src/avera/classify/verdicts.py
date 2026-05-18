"""Stable verdict taxonomy for AVERA classification."""

from __future__ import annotations

EXPECTED_CHANGE = "expected_change"
SUCCESSFUL_CHANGE = "successful_change"
CONFIRMED_REGRESSION = "confirmed_regression"
POSSIBLE_REGRESSION = "possible_regression"
PREEXISTING_FAILURE = "preexisting_failure"
WORSENED_PREEXISTING_FAILURE = "worsened_preexisting_failure"
ENVIRONMENT_FAILURE = "environment_failure"
REQUIREMENTS_COVERAGE_GAP = "requirements_coverage_gap"
INSUFFICIENT_EVIDENCE = "insufficient_evidence"

ALL_VERDICTS = (
    EXPECTED_CHANGE,
    SUCCESSFUL_CHANGE,
    CONFIRMED_REGRESSION,
    POSSIBLE_REGRESSION,
    PREEXISTING_FAILURE,
    WORSENED_PREEXISTING_FAILURE,
    ENVIRONMENT_FAILURE,
    REQUIREMENTS_COVERAGE_GAP,
    INSUFFICIENT_EVIDENCE,
)

FAULT_VERDICTS = (
    CONFIRMED_REGRESSION,
    POSSIBLE_REGRESSION,
)

NON_FAULT_VERDICTS = (
    EXPECTED_CHANGE,
    SUCCESSFUL_CHANGE,
    PREEXISTING_FAILURE,
    WORSENED_PREEXISTING_FAILURE,
    ENVIRONMENT_FAILURE,
    REQUIREMENTS_COVERAGE_GAP,
    INSUFFICIENT_EVIDENCE,
)


def normalize_verdict(value: str | None, default: str = INSUFFICIENT_EVIDENCE) -> str:
    """Return a known verdict string without changing the external API."""

    normalized = str(value or "").strip().lower().replace("-", "_")
    return normalized if normalized in ALL_VERDICTS else default


def is_fault_verdict(value: str | None) -> bool:
    """Return whether a verdict represents an AVERA-attributed regression risk."""

    return normalize_verdict(value) in FAULT_VERDICTS
