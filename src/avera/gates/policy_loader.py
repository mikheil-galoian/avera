"""Load versioned, data-driven gate policies from JSON files.

Policies live under the repository ``policies/`` directory as JSON (chosen over
YAML to keep AVERA dependency-free — the standard library can parse JSON, and a
deterministic gate must not depend on an optional parser).

A policy file looks like::

    {
      "schema_version": "avera.gate_policy.v1",
      "policy_id": "automotive.v1",
      "domain": "automotive",
      "description": "...",
      "max_allowed_risk": "low",
      "min_confidence_score": 0.7,
      "blocking_verdicts": ["confirmed_regression", "worsened_preexisting_failure"],
      "review_verdicts": ["environment_failure", "insufficient_evidence", ...],
      "risk_rank": {"unknown": 0, "low": 1, ...}   // optional
    }

``risk_rank`` is optional; when omitted the built-in ranking is used.
"""

from __future__ import annotations

import json
from pathlib import Path

from .policy import RISK_RANK, GatePolicy

SCHEMA_VERSION = "avera.gate_policy.v1"

# Resolve the repository policies/ directory relative to this file:
# src/avera/gates/policy_loader.py -> repo root is parents[3].
_REPO_ROOT = Path(__file__).resolve().parents[3]
POLICIES_DIR = _REPO_ROOT / "policies"

# Friendly built-in names mapped to policy file stems.
BUILTIN_POLICIES: dict[str, str] = {
    "general": "general_policy",
    "automotive": "automotive_policy",
    "aviation": "aviation_policy",
    "medical": "medical_policy",
    "railway": "railway_policy",
    "ai_agent": "ai_agent_policy",
}


class PolicyError(ValueError):
    """Raised when a policy file is missing or malformed."""


def policy_from_dict(data: dict) -> GatePolicy:
    """Build a :class:`GatePolicy` from a parsed policy mapping."""

    if not isinstance(data, dict):
        raise PolicyError("policy must be a JSON object")

    for required in ("policy_id", "max_allowed_risk", "min_confidence_score"):
        if required not in data:
            raise PolicyError(f"policy missing required field: {required}")

    try:
        min_conf = float(data["min_confidence_score"])
    except (TypeError, ValueError) as exc:
        raise PolicyError("min_confidence_score must be a number") from exc

    blocking = data.get("blocking_verdicts")
    review = data.get("review_verdicts")
    risk_rank = data.get("risk_rank")

    if blocking is not None and not isinstance(blocking, list):
        raise PolicyError("blocking_verdicts must be a list")
    if review is not None and not isinstance(review, list):
        raise PolicyError("review_verdicts must be a list")
    if risk_rank is not None and not isinstance(risk_rank, dict):
        raise PolicyError("risk_rank must be an object")

    return GatePolicy(
        policy_id=str(data["policy_id"]),
        max_allowed_risk=str(data["max_allowed_risk"]),
        min_confidence_score=min_conf,
        blocking_verdicts=frozenset(str(v) for v in (blocking or [])),
        review_verdicts=frozenset(str(v) for v in (review or [])),
        risk_rank={str(k): int(v) for k, v in (risk_rank or RISK_RANK).items()},
        domain=str(data.get("domain", "general")),
        schema_version=str(data.get("schema_version", SCHEMA_VERSION)),
    )


def load_policy(path: str | Path) -> GatePolicy:
    """Load a gate policy from a JSON file path."""

    p = Path(path)
    if not p.exists():
        raise PolicyError(f"policy file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyError(f"invalid policy JSON in {p}: {exc}") from exc
    return policy_from_dict(data)


def load_builtin_policy(name: str, *, policies_dir: str | Path | None = None) -> GatePolicy:
    """Load a built-in policy by friendly name (e.g. ``"automotive"``)."""

    stem = BUILTIN_POLICIES.get(name)
    if stem is None:
        raise PolicyError(
            f"unknown built-in policy: {name!r}. "
            f"Available: {', '.join(sorted(BUILTIN_POLICIES))}"
        )
    base = Path(policies_dir) if policies_dir is not None else POLICIES_DIR
    return load_policy(base / f"{stem}.json")


def list_builtin_policies() -> list[str]:
    """Return the friendly names of available built-in policies."""

    return sorted(BUILTIN_POLICIES)
