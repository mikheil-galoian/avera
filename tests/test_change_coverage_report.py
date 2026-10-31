"""US-09.4: coverage_of_change computation — combines parse_unified_diff's
output with parse_lcov/parse_cobertura's output into one deterministic,
fail-closed report.

Fail-closed rule: a file present in the diff but absent from the coverage
report counts as fully uncovered, never silently skipped.
"""

from __future__ import annotations

import dataclasses

import pytest

from avera.change_coverage.report import (
    ChangeCoverageReport,
    FileCoverageOfChange,
    compute_change_coverage,
)


def test_fully_covered_file():
    changed = {"a.py": [(1, 3)]}
    covered = {"a.py": {1, 2, 3}}
    report = compute_change_coverage(changed, covered)
    file_report = report.files[0]
    assert file_report.path == "a.py"
    assert file_report.changed_lines == 3
    assert file_report.covered_changed_lines == 3
    assert file_report.uncovered_lines == []
    assert file_report.coverage_of_change == 1.0
    assert file_report.has_coverage_data is True


def test_partially_covered_file_lists_the_uncovered_lines():
    changed = {"a.py": [(1, 3), (10, 10)]}  # lines 1,2,3,10 changed
    covered = {"a.py": {1, 10}}  # 2 and 3 are changed but not test-executed
    report = compute_change_coverage(changed, covered)
    file_report = report.files[0]
    assert file_report.changed_lines == 4
    assert file_report.covered_changed_lines == 2
    assert file_report.uncovered_lines == [2, 3]
    assert file_report.coverage_of_change == 0.5


def test_file_absent_from_coverage_report_is_fully_uncovered_not_skipped():
    changed = {"new_untested.py": [(1, 5)]}
    covered: dict[str, set[int]] = {}  # the coverage report never mentions this file
    report = compute_change_coverage(changed, covered)
    file_report = report.files[0]
    assert file_report.has_coverage_data is False
    assert file_report.covered_changed_lines == 0
    assert file_report.uncovered_lines == [1, 2, 3, 4, 5]
    assert file_report.coverage_of_change == 0.0


def test_coverage_report_lines_outside_the_diff_are_irrelevant():
    changed = {"a.py": [(5, 5)]}
    covered = {"a.py": {1, 2, 3, 999}}  # none of these overlap the one changed line
    report = compute_change_coverage(changed, covered)
    assert report.files[0].covered_changed_lines == 0
    assert report.files[0].uncovered_lines == [5]


def test_aggregate_across_multiple_files():
    changed = {"a.py": [(1, 4)], "b.py": [(1, 1)]}
    covered = {"a.py": {1, 2}, "b.py": set()}
    report = compute_change_coverage(changed, covered)
    assert report.total_changed_lines == 5
    assert report.total_covered_changed_lines == 2
    assert report.coverage_of_change == 0.4


def test_empty_diff_yields_a_clean_zero_report_not_a_crash():
    report = compute_change_coverage({}, {})
    assert report.files == []
    assert report.total_changed_lines == 0
    assert report.total_covered_changed_lines == 0
    assert report.coverage_of_change == 1.0  # nothing changed -> vacuously fully "covered"


def test_files_are_sorted_for_determinism():
    changed = {"z.py": [(1, 1)], "a.py": [(1, 1)]}
    report = compute_change_coverage(changed, {})
    assert [f.path for f in report.files] == ["a.py", "z.py"]


# ---------------------------------------------------------------------------
# Dataclass contract: frozen (evidence must not be mutable after the fact)
# and defaults, exercised directly since compute_change_coverage always
# supplies every field explicitly.
# ---------------------------------------------------------------------------

def test_file_coverage_of_change_is_frozen():
    f = FileCoverageOfChange(path="a.py", changed_lines=1, covered_changed_lines=1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.path = "b.py"


def test_change_coverage_report_is_frozen():
    r = ChangeCoverageReport()
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.coverage_of_change = 0.0


def test_file_coverage_of_change_defaults():
    f = FileCoverageOfChange(path="a.py", changed_lines=0, covered_changed_lines=0)
    assert f.has_coverage_data is False
    assert f.uncovered_lines == []
    assert f.coverage_of_change == 0.0


def test_change_coverage_report_defaults():
    r = ChangeCoverageReport()
    assert r.files == []
    assert r.total_changed_lines == 0
    assert r.total_covered_changed_lines == 0
    assert r.coverage_of_change == 1.0


def test_to_dict_is_json_shaped_and_deterministic():
    changed = {"a.py": [(1, 2)]}
    covered = {"a.py": {1}}
    d = compute_change_coverage(changed, covered).to_dict()
    assert d["coverage_of_change"] == 0.5
    assert d["files"][0] == {
        "path": "a.py",
        "changed_lines": 2,
        "covered_changed_lines": 1,
        "uncovered_lines": [2],
        "coverage_of_change": 0.5,
        "has_coverage_data": True,
    }
