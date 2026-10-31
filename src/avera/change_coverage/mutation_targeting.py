"""Change-targeted mutation (EP-10): automatically run the mutation lens on
changed+covered regions from EP-09, so "covered" is upgraded to "verified"
without a human naming functions by hand.

Only lines that are BOTH changed and covered are mutated. An uncovered
changed line already has a verdict — uncovered — from EP-09; mutating it
would spend the one expensive resource here (a real test-suite run per
mutant) re-measuring something EP-09 already answered for free.

Bounded by a budget. The mutant count for a candidate region is cheap to
compute up front (a pure AST operation, no test execution) and is checked
against the remaining mutant budget before the expensive part starts; the
wall-clock deadline is checked before starting each region. A region skipped
this way is reported as ``not_evaluated`` — distinct from ``no_mutants``
(genuinely nothing mutable there) and from an evaluated-but-weak verdict —
never silently folded into either.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from avera.mutation import run_mutation_lens
from avera.mutation.engine import generate_mutants
from avera.mutation.score import mutation_confidence

from .diff import _merge_ranges
from .report import ChangeCoverageReport

NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True)
class RegionEvaluation:
    """The mutation-lens result for one changed+covered line range."""

    path: str
    start: int
    end: int
    status: str  # a avera.mutation.score verdict, or NOT_EVALUATED
    mutation_score: float | None  # None only when status == NOT_EVALUATED
    survivors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "start": self.start,
            "end": self.end,
            "status": self.status,
            "mutation_score": self.mutation_score,
            "survivors": list(self.survivors),
        }


@dataclass(frozen=True)
class ChangeTargetedMutationReport:
    regions: list[RegionEvaluation] = field(default_factory=list)
    budget_exhausted: bool = False

    def to_dict(self) -> dict:
        return {
            "regions": [r.to_dict() for r in self.regions],
            "budget_exhausted": self.budget_exhausted,
        }


def _covered_changed_ranges(
    changed_ranges: list[tuple[int, int]], uncovered_lines: list[int]
) -> list[tuple[int, int]]:
    """Changed line ranges minus uncovered lines, regrouped into contiguous
    (start, end) ranges. Reuses the diff module's range merger: a covered
    line is modelled as a singleton range and adjacent ones coalesce."""
    uncovered = set(uncovered_lines)
    changed_lines = sorted({ln for start, end in changed_ranges for ln in range(start, end + 1)})
    covered_lines = [ln for ln in changed_lines if ln not in uncovered]
    return _merge_ranges([(ln, ln) for ln in covered_lines])


def run_change_targeted_mutation(
    root: str | Path,
    changed: dict[str, list[tuple[int, int]]],
    coverage: ChangeCoverageReport,
    test_command: Sequence[str],
    *,
    max_mutants: int = 200,  # the exact default is not a correctness boundary — any
    # reasonably large ceiling is as valid as another; the mutation lens on this
    # function cannot distinguish 200 from 201 here without an artificial
    # 200-mutant fixture, so this one survivor is accepted (same posture as
    # T-13's chunk-size survivor), not force-tested.
    max_seconds: float = 60.0,
) -> ChangeTargetedMutationReport:
    """For every changed+covered region, run the mutation lens, bounded by
    ``max_mutants`` (total across this whole call) and ``max_seconds`` (wall
    clock, checked before starting each region, not an interrupt mid-run)."""
    root = Path(root)
    deadline = time.monotonic() + max_seconds
    mutants_used = 0
    budget_exhausted = False
    regions: list[RegionEvaluation] = []

    for file_report in coverage.files:
        path = file_report.path
        if path not in changed:
            continue
        for start, end in _covered_changed_ranges(changed[path], file_report.uncovered_lines):
            if time.monotonic() >= deadline:
                budget_exhausted = True
                regions.append(RegionEvaluation(path, start, end, NOT_EVALUATED, None))
                continue

            source_path = root / path
            text = source_path.read_text(encoding="utf-8")
            candidate_count = len(generate_mutants(text, start, end))

            if candidate_count == 0:
                empty = mutation_confidence([])
                regions.append(
                    RegionEvaluation(path, start, end, empty.verdict, empty.mutation_score)
                )
                continue

            if mutants_used + candidate_count > max_mutants:
                budget_exhausted = True
                regions.append(RegionEvaluation(path, start, end, NOT_EVALUATED, None))
                continue

            result = run_mutation_lens(
                source_path, test_command, line_range=(start, end), cwd=root, timeout=max_seconds
            )
            mutants_used += result.confidence.total
            regions.append(
                RegionEvaluation(
                    path, start, end, result.confidence.verdict,
                    result.confidence.mutation_score, list(result.confidence.survivors),
                )
            )

    return ChangeTargetedMutationReport(regions=regions, budget_exhausted=budget_exhausted)


# ---------------------------------------------------------------------------
# US-10.3: combine EP-09's coverage-of-change with this module's mutation
# evaluation into one verdict.
# ---------------------------------------------------------------------------

_WEAK_STATUSES = frozenset({"partially_verified", "unverified"})


@dataclass(frozen=True)
class CombinedEvidenceVerdict:
    uncovered_lines: dict[str, list[int]]
    weak_evidence_regions: list[RegionEvaluation]
    not_evaluated_regions: list[RegionEvaluation]
    coverage_of_change: float
    change_mutation_score: float | None  # mean over evaluated regions; None if none evaluated

    def to_dict(self) -> dict:
        return {
            "uncovered_lines": dict(self.uncovered_lines),
            "weak_evidence_regions": [r.to_dict() for r in self.weak_evidence_regions],
            "not_evaluated_regions": [r.to_dict() for r in self.not_evaluated_regions],
            "coverage_of_change": self.coverage_of_change,
            "change_mutation_score": self.change_mutation_score,
        }


def combine_evidence(
    coverage: ChangeCoverageReport, mutation: ChangeTargetedMutationReport
) -> CombinedEvidenceVerdict:
    uncovered = {f.path: f.uncovered_lines for f in coverage.files if f.uncovered_lines}
    weak = [r for r in mutation.regions if r.status in _WEAK_STATUSES]
    not_evaluated = [r for r in mutation.regions if r.status == NOT_EVALUATED]
    evaluated_scores = [r.mutation_score for r in mutation.regions if r.mutation_score is not None]
    aggregate = sum(evaluated_scores) / len(evaluated_scores) if evaluated_scores else None
    return CombinedEvidenceVerdict(
        uncovered_lines=uncovered,
        weak_evidence_regions=weak,
        not_evaluated_regions=not_evaluated,
        coverage_of_change=coverage.coverage_of_change,
        change_mutation_score=aggregate,
    )
