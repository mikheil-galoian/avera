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
import math
import os
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

    policy_id = str(data["policy_id"]).strip()
    if not policy_id:
        raise PolicyError("policy_id must be a non-empty string")

    # min_confidence_score must be a finite number in [0, 1]; a NaN/inf or an
    # out-of-range value would silently send every report to review (the gate
    # can never satisfy `confidence >= NaN`). Reject it instead of degrading.
    if isinstance(data["min_confidence_score"], bool):
        raise PolicyError("min_confidence_score must be a number, not a bool")
    try:
        min_conf = float(data["min_confidence_score"])
    except (TypeError, ValueError) as exc:
        raise PolicyError("min_confidence_score must be a number") from exc
    if not math.isfinite(min_conf) or not (0.0 <= min_conf <= 1.0):
        raise PolicyError(
            f"min_confidence_score must be a finite number in [0, 1], got {min_conf!r}"
        )

    blocking = data.get("blocking_verdicts")
    review = data.get("review_verdicts")
    risk_rank = data.get("risk_rank")

    if blocking is not None and not isinstance(blocking, list):
        raise PolicyError("blocking_verdicts must be a list")
    if review is not None and not isinstance(review, list):
        raise PolicyError("review_verdicts must be a list")
    if risk_rank is not None and not isinstance(risk_rank, dict):
        raise PolicyError("risk_rank must be an object")

    # Build the effective ranking, validating each level is an integer. A
    # non-integer rank would make the gate's risk comparison meaningless.
    effective_rank: dict[str, int] = {}
    for level, rank in (risk_rank or RISK_RANK).items():
        if isinstance(rank, bool) or not isinstance(rank, int):
            raise PolicyError(
                f"risk_rank[{level!r}] must be an integer, got {rank!r}"
            )
        effective_rank[str(level)] = rank
    if not effective_rank:
        raise PolicyError("risk_rank must define at least one level")

    # The configured ceiling must be a level the ranking actually knows about,
    # otherwise the gate cannot place it and would silently degrade.
    max_risk = str(data["max_allowed_risk"]).strip()
    if max_risk not in effective_rank:
        raise PolicyError(
            f"max_allowed_risk {max_risk!r} is not present in risk_rank "
            f"(known levels: {', '.join(sorted(effective_rank))})"
        )

    return GatePolicy(
        policy_id=policy_id,
        max_allowed_risk=max_risk,
        min_confidence_score=min_conf,
        blocking_verdicts=frozenset(str(v) for v in (blocking or [])),
        review_verdicts=frozenset(str(v) for v in (review or [])),
        risk_rank=effective_rank,
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


def _candidate_dirs(explicit: str | Path | None) -> list[Path]:
    """Ordered candidate directories to resolve a built-in policy file from.

    Order: explicit arg (an intentional API choice by the caller), then the
    trusted package-relative repo dir, then AVERA_POLICIES_DIR env, then
    ``<cwd>/policies``. The trusted package dir is tried BEFORE env/cwd so that
    a present built-in always resolves from the shipped, audited location — the
    environment cannot silently swap a built-in policy for a laxer copy. Env/cwd
    remain as a fallback only when the package copy is absent (covers the
    installed GitHub Action running inside a checked-out repository).
    """
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit))
    candidates.append(POLICIES_DIR)
    env_dir = os.environ.get("AVERA_POLICIES_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.append(Path.cwd() / "policies")
    return candidates


def load_builtin_policy(name: str, *, policies_dir: str | Path | None = None) -> GatePolicy:
    """Load a built-in policy by friendly name (e.g. ``"automotive"``)."""

    stem = BUILTIN_POLICIES.get(name)
    if stem is None:
        raise PolicyError(
            f"unknown built-in policy: {name!r}. "
            f"Available: {', '.join(sorted(BUILTIN_POLICIES))}"
        )
    tried: list[str] = []
    for base in _candidate_dirs(policies_dir):
        path = base / f"{stem}.json"
        tried.append(str(path))
        if path.exists():
            return load_policy(path)
    raise PolicyError(
        f"policy file for {name!r} not found. Tried: {', '.join(tried)}"
    )


def list_builtin_policies() -> list[str]:
    """Return the friendly names of available built-in policies."""

    return sorted(BUILTIN_POLICIES)
