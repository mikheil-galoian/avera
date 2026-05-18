"""Requirement coverage proof generator.

Every requirement must be covered by at least one test case.
Uncovered requirements are a structural risk — the absence of evidence
is itself evidence of a gap, especially under IEC-62304 / DO-178C / EN-50128.

Design contract:
- ``CoverageChecker`` operates on requirements (CSV rows) and a traceability
  map (test_id → list[req_id]).
- ``check()`` returns a ``CoverageReport`` containing covered/uncovered
  requirements and a per-requirement risk escalation: uncovered requirements
  at safety level >= ASIL-C / DAL-B / SIL-3 / Class-C auto-escalate to
  ``release_blocking``; lower levels escalate to ``medium``.
- The checker integrates with the existing ``safety_rank()`` from
  ``avera.classify.risk_levels`` — no new taxonomy needed.

Usage::

    from avera.coverage import CoverageChecker

    checker = CoverageChecker(
        requirements=[
            {"id": "BMS-REQ-001", "safety_level": "asil-d"},
            {"id": "BMS-REQ-002", "safety_level": "asil-b"},
        ],
        test_coverage_map={
            "BMS-HIL-TEMP-01": ["BMS-REQ-001"],
        },
    )
    report = checker.check()
    print(report.coverage_pct)        # 50.0
    print(report.uncovered_req_ids)   # ['BMS-REQ-002']
    print(report.max_gap_risk)        # 'medium'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from avera.classify.risk_levels import safety_rank


# Risk escalation thresholds
_HIGH_RANK = 3    # ASIL-C / DAL-B / SIL-3 / Class-C → release_blocking when uncovered
_MED_RANK  = 1    # anything >= ASIL-A / SIL-1 → medium when uncovered


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoverageGap:
    """One uncovered requirement with its escalated risk."""

    req_id: str
    safety_level: str
    safety_rank: int
    escalated_risk: str       # "release_blocking" | "high" | "medium" | "low"
    covering_tests: list[str] = field(default_factory=list)


@dataclass
class CoverageReport:
    """Full coverage proof artifact returned by ``CoverageChecker.check()``."""

    total_requirements: int
    covered_count: int
    uncovered_count: int
    coverage_pct: float

    covered_req_ids: list[str]
    uncovered_req_ids: list[str]
    gaps: list[CoverageGap]           # only uncovered requirements

    max_gap_risk: str                 # worst escalated risk across all gaps
    schema_version: str = "avera.coverage.v1.0"

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "total_requirements": self.total_requirements,
            "covered_count": self.covered_count,
            "uncovered_count": self.uncovered_count,
            "coverage_pct": self.coverage_pct,
            "covered_req_ids": self.covered_req_ids,
            "uncovered_req_ids": self.uncovered_req_ids,
            "max_gap_risk": self.max_gap_risk,
            "gaps": [
                {
                    "req_id": g.req_id,
                    "safety_level": g.safety_level,
                    "safety_rank": g.safety_rank,
                    "escalated_risk": g.escalated_risk,
                    "covering_tests": g.covering_tests,
                }
                for g in self.gaps
            ],
        }


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

class CoverageChecker:
    """Verify that every requirement is exercised by at least one test.

    Parameters
    ----------
    requirements:
        List of requirement dicts.  Each must have an ``"id"`` key and
        optionally a ``"safety_level"`` key (defaults to ``"unknown"``).
    test_coverage_map:
        Mapping of ``test_id → list[req_id]`` stating which tests cover
        which requirements.  Typically extracted from the traceability index.
    """

    def __init__(
        self,
        requirements: list[dict[str, Any]],
        test_coverage_map: dict[str, list[str]],
    ) -> None:
        self._requirements = requirements
        self._coverage_map = test_coverage_map

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self) -> CoverageReport:
        """Run the coverage analysis and return a ``CoverageReport``."""

        # Build reverse map: req_id → [test_ids that cover it]
        covered_by: dict[str, list[str]] = {}
        for test_id, req_ids in self._coverage_map.items():
            for rid in req_ids:
                covered_by.setdefault(rid, []).append(test_id)

        covered_ids: list[str] = []
        uncovered_ids: list[str] = []
        gaps: list[CoverageGap] = []

        for req in self._requirements:
            req_id = str(req.get("id") or req.get("req_id") or "")
            if not req_id:
                continue

            covering = covered_by.get(req_id, [])
            if covering:
                covered_ids.append(req_id)
            else:
                safety_level = str(req.get("safety_level") or req.get("level") or "unknown")
                rank = safety_rank(safety_level)
                escalated = _escalate(rank)
                gaps.append(CoverageGap(
                    req_id=req_id,
                    safety_level=safety_level,
                    safety_rank=rank,
                    escalated_risk=escalated,
                    covering_tests=[],
                ))
                uncovered_ids.append(req_id)

        total = len(covered_ids) + len(uncovered_ids)
        pct = round(100.0 * len(covered_ids) / total, 2) if total else 100.0

        max_risk = _worst_risk([g.escalated_risk for g in gaps])

        return CoverageReport(
            total_requirements=total,
            covered_count=len(covered_ids),
            uncovered_count=len(uncovered_ids),
            coverage_pct=pct,
            covered_req_ids=sorted(covered_ids),
            uncovered_req_ids=sorted(uncovered_ids),
            gaps=gaps,
            max_gap_risk=max_risk,
        )

    @classmethod
    def from_traceability(
        cls,
        requirements: list[dict[str, Any]],
        traceability: dict[str, Any],
    ) -> "CoverageChecker":
        """Construct from an AVERA traceability index dict.

        The traceability index has a ``tests`` section mapping test_id to
        metadata that includes a ``requirements`` list.
        """
        tests_section = traceability.get("tests") or {}

        if isinstance(tests_section, dict):
            items = tests_section.items()
        else:
            items = ((t.get("test", ""), t) for t in tests_section if isinstance(t, dict))

        coverage_map: dict[str, list[str]] = {}
        for test_id, meta in items:
            if not isinstance(meta, dict):
                continue
            req_refs = meta.get("requirements") or []
            if isinstance(req_refs, list):
                coverage_map[str(test_id)] = [str(r) for r in req_refs]

        return cls(requirements=requirements, test_coverage_map=coverage_map)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_RISK_ORDER = ["low", "medium", "high", "release_blocking"]


def _escalate(rank: int) -> str:
    """Map a safety rank to an escalated gap risk."""
    if rank >= _HIGH_RANK:       # ASIL-C+ / SIL-3+ / DAL-B+ / Class-C
        return "release_blocking"
    if rank >= _MED_RANK:        # ASIL-A/B / SIL-1/2 / Class-A/B
        return "medium"
    return "low"                 # rank 0 — unclassified


def _worst_risk(risks: list[str]) -> str:
    if not risks:
        return "low"
    return max(risks, key=lambda r: _RISK_ORDER.index(r) if r in _RISK_ORDER else -1)
