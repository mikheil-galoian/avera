"""Combine a diff (``parse_unified_diff``) with a coverage report
(``parse_lcov`` / ``parse_cobertura``) into one deterministic, fail-closed
coverage-of-change report.

Fail-closed: a file present in the diff but absent from the coverage report
counts as fully uncovered — it is never silently skipped, because an auditor
reading the result must see that the evidence is missing, not infer it from
an absence.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FileCoverageOfChange:
    """Coverage-of-change for one file."""

    path: str
    changed_lines: int
    covered_changed_lines: int
    uncovered_lines: list[int] = field(default_factory=list)
    coverage_of_change: float = 0.0
    has_coverage_data: bool = False  # False = file absent from the coverage report entirely

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "changed_lines": self.changed_lines,
            "covered_changed_lines": self.covered_changed_lines,
            "uncovered_lines": list(self.uncovered_lines),
            "coverage_of_change": self.coverage_of_change,
            "has_coverage_data": self.has_coverage_data,
        }


@dataclass(frozen=True)
class ChangeCoverageReport:
    """Aggregate coverage-of-change across every file in a diff."""

    files: list[FileCoverageOfChange] = field(default_factory=list)
    total_changed_lines: int = 0
    total_covered_changed_lines: int = 0
    coverage_of_change: float = 1.0  # vacuously "fully covered" when nothing changed

    def to_dict(self) -> dict:
        return {
            "files": [f.to_dict() for f in self.files],
            "total_changed_lines": self.total_changed_lines,
            "total_covered_changed_lines": self.total_covered_changed_lines,
            "coverage_of_change": self.coverage_of_change,
        }


def _lines_in_ranges(ranges: list[tuple[int, int]]) -> list[int]:
    return [line for start, end in ranges for line in range(start, end + 1)]


def compute_change_coverage(
    changed: dict[str, list[tuple[int, int]]],
    covered: dict[str, set[int]],
) -> ChangeCoverageReport:
    """Build the report. ``changed`` and ``covered`` are the outputs of
    ``parse_unified_diff`` and ``parse_lcov``/``parse_cobertura``
    respectively; path keys must match exactly (no fuzzy matching — a
    mismatch between the two is reported as missing coverage, never guessed)."""
    files: list[FileCoverageOfChange] = []
    total_changed = 0
    total_covered = 0

    for path in sorted(changed):
        changed_lines = _lines_in_ranges(changed[path])
        has_data = path in covered
        covered_lines = covered.get(path, set())
        uncovered = sorted(ln for ln in changed_lines if ln not in covered_lines)
        covered_count = len(changed_lines) - len(uncovered)
        ratio = covered_count / len(changed_lines) if changed_lines else 1.0

        files.append(
            FileCoverageOfChange(
                path=path,
                changed_lines=len(changed_lines),
                covered_changed_lines=covered_count,
                uncovered_lines=uncovered,
                coverage_of_change=ratio,
                has_coverage_data=has_data,
            )
        )
        total_changed += len(changed_lines)
        total_covered += covered_count

    aggregate = total_covered / total_changed if total_changed else 1.0
    return ChangeCoverageReport(
        files=files,
        total_changed_lines=total_changed,
        total_covered_changed_lines=total_covered,
        coverage_of_change=aggregate,
    )
# real-diff-probe
