"""US-10.2/US-10.3: automatically run the mutation lens on changed+covered
regions from EP-09 (change_coverage), bounded by a budget, combined with
EP-09's uncovered-line evidence into one verdict.

Only changed+covered lines are mutated — an uncovered line already has a
verdict (uncovered) from EP-09, so mutating it would spend the expensive
resource (a full test run per mutant) on something already answered.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

from avera.change_coverage import mutation_targeting as mt
from avera.change_coverage.mutation_targeting import (
    NOT_EVALUATED,
    ChangeTargetedMutationReport,
    CombinedEvidenceVerdict,
    RegionEvaluation,
    _covered_changed_ranges,
    combine_evidence,
    run_change_targeted_mutation,
)
from avera.change_coverage.report import (
    ChangeCoverageReport,
    FileCoverageOfChange,
    compute_change_coverage,
)
from avera.mutation.score import NO_MUTANTS, PARTIALLY_VERIFIED, UNVERIFIED, VERIFIED

MODULE = (
    "def is_adult(age):\n"
    "    return age >= 18\n"
    "\n"
    "\n"
    "def other(x):\n"
    "    return x < 5\n"
)
STRONG_CHECK = (
    "from mod import is_adult\n"
    "assert is_adult(18) is True\n"
    "assert is_adult(17) is False\n"
)
WEAK_CHECK = "from mod import is_adult\nassert is_adult(30)\n"


def _project(tmp_path: Path, check: str) -> tuple[Path, list[str]]:
    (tmp_path / "mod.py").write_text(MODULE, encoding="utf-8")
    check_file = tmp_path / "check.py"
    check_file.write_text(check, encoding="utf-8")
    return tmp_path, [sys.executable, str(check_file)]


def _coverage(path: str, **kwargs) -> ChangeCoverageReport:
    return ChangeCoverageReport(files=[FileCoverageOfChange(path=path, **kwargs)])


# ---------------------------------------------------------------------------
# _covered_changed_ranges
# ---------------------------------------------------------------------------

def test_covered_changed_ranges_excludes_uncovered_lines():
    assert _covered_changed_ranges([(1, 10)], uncovered_lines=[3, 4, 5]) == [(1, 2), (6, 10)]


def test_covered_changed_ranges_fully_covered():
    assert _covered_changed_ranges([(1, 5)], uncovered_lines=[]) == [(1, 5)]


def test_covered_changed_ranges_fully_uncovered():
    assert _covered_changed_ranges([(1, 5)], uncovered_lines=[1, 2, 3, 4, 5]) == []


# ---------------------------------------------------------------------------
# run_change_targeted_mutation
# ---------------------------------------------------------------------------

def test_covered_region_is_mutated_and_verdict_reflects_test_strength_strong(tmp_path):
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(1, 2)]}
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd)
    assert len(report.regions) == 1
    region = report.regions[0]
    assert region.path == "mod.py"
    assert region.status == VERIFIED
    assert region.mutation_score == 1.0
    assert report.budget_exhausted is False


def test_covered_region_with_weak_tests_is_reported_unverified(tmp_path):
    root, cmd = _project(tmp_path, WEAK_CHECK)
    changed = {"mod.py": [(1, 2)]}
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd)
    assert report.regions[0].status in (UNVERIFIED, PARTIALLY_VERIFIED)
    assert report.regions[0].mutation_score < 1.0
    assert report.regions[0].survivors  # at least one description present


def test_fully_uncovered_change_contributes_no_regions(tmp_path):
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(1, 2)]}
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=0,
                          uncovered_lines=[1, 2], coverage_of_change=0.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd)
    assert report.regions == []


def test_file_missing_from_coverage_report_contributes_no_regions(tmp_path):
    # has_coverage_data=False -> EP-09 already marks every changed line uncovered;
    # there is nothing covered to upgrade to "verified".
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(1, 2)]}
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=0,
                          uncovered_lines=[1, 2], coverage_of_change=0.0, has_coverage_data=False)
    report = run_change_targeted_mutation(root, changed, coverage, cmd)
    assert report.regions == []


def test_disjoint_covered_subranges_are_evaluated_as_separate_regions(tmp_path):
    root, cmd = _project(tmp_path, STRONG_CHECK)
    # Both functions changed; the gap between them (lines 3-4, blank) is
    # irrelevant since it's outside the changed set entirely in this fixture
    # — model two separate changed+covered spans directly instead.
    changed = {"mod.py": [(1, 2), (5, 6)]}
    coverage = _coverage("mod.py", changed_lines=4, covered_changed_lines=2,
                          uncovered_lines=[5, 6], coverage_of_change=0.5, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd)
    assert len(report.regions) == 1  # only (1,2) is covered; (5,6) is uncovered, skipped
    assert (report.regions[0].start, report.regions[0].end) == (1, 2)


def test_zero_candidate_mutants_is_no_mutants_not_not_evaluated(tmp_path):
    # A range with no mutable AST node (pure def/blank lines) is a real,
    # evaluated answer ("nothing to mutate here"), not a budget skip.
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(3, 4)]}  # the two blank lines between the functions
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd)
    assert report.regions[0].status == NO_MUTANTS
    assert report.budget_exhausted is False


def test_zero_candidate_mutants_never_invokes_the_expensive_runner(tmp_path, monkeypatch):
    # The whole point of the cheap pre-count is to never pay for a real test
    # run when there is statically nothing to mutate.
    def boom(*args, **kwargs):
        raise AssertionError("run_mutation_lens must not run for zero candidate mutants")

    monkeypatch.setattr(mt, "run_mutation_lens", boom)
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(3, 4)]}
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd)
    assert report.regions[0].status == NO_MUTANTS


def test_mutant_budget_exactly_matching_candidate_count_still_runs(tmp_path):
    # Budget check must be "would exceed" (>), not "would reach" (>=): a
    # region whose candidate count exactly fills the remaining budget is
    # allowed to run, not skipped one mutant short.
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(1, 2)]}  # exactly 3 real mutants (is_adult)
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd, max_mutants=3)
    assert report.regions[0].status != NOT_EVALUATED
    assert report.regions[0].mutation_score == 1.0
    assert report.budget_exhausted is False


def test_time_budget_boundary_is_inclusive(tmp_path, monkeypatch):
    # At exactly the deadline (not only strictly after it), evaluation must
    # already stop — a bare "later than" would let one more region start.
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(1, 2)]}
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    monkeypatch.setattr(mt.time, "monotonic", lambda: 0.0)  # "now" == deadline exactly
    report = run_change_targeted_mutation(root, changed, coverage, cmd, max_seconds=0.0)
    assert report.regions[0].status == NOT_EVALUATED
    assert report.budget_exhausted is True


def test_mutant_budget_exhausted_marks_region_not_evaluated(tmp_path):
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(1, 2)]}  # 3 real mutants here
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd, max_mutants=2)
    assert report.regions[0].status == NOT_EVALUATED
    assert report.regions[0].mutation_score is None
    assert report.budget_exhausted is True


def test_time_budget_already_exhausted_marks_every_region_not_evaluated(tmp_path):
    root, cmd = _project(tmp_path, STRONG_CHECK)
    changed = {"mod.py": [(1, 2)]}
    coverage = _coverage("mod.py", changed_lines=2, covered_changed_lines=2,
                          uncovered_lines=[], coverage_of_change=1.0, has_coverage_data=True)
    report = run_change_targeted_mutation(root, changed, coverage, cmd, max_seconds=0.0)
    assert report.regions[0].status == NOT_EVALUATED
    assert report.budget_exhausted is True


def test_report_to_dict_is_json_shaped():
    r = RegionEvaluation(path="a.py", start=1, end=2, status=VERIFIED,
                          mutation_score=1.0, survivors=[])
    assert r.to_dict() == {
        "path": "a.py", "start": 1, "end": 2, "status": VERIFIED,
        "mutation_score": 1.0, "survivors": [],
    }


def test_change_targeted_mutation_report_defaults_and_to_dict():
    r = ChangeTargetedMutationReport()
    assert r.regions == []
    assert r.budget_exhausted is False
    assert r.to_dict() == {"regions": [], "budget_exhausted": False}


# ---------------------------------------------------------------------------
# Result objects are evidence: must not be mutable after construction.
# ---------------------------------------------------------------------------

def test_region_evaluation_is_frozen():
    r = RegionEvaluation(path="a.py", start=1, end=1, status=VERIFIED, mutation_score=1.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.status = UNVERIFIED


def test_change_targeted_mutation_report_is_frozen():
    r = ChangeTargetedMutationReport()
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.budget_exhausted = True


def test_combined_evidence_verdict_is_frozen():
    v = CombinedEvidenceVerdict(uncovered_lines={}, weak_evidence_regions=[],
                                 not_evaluated_regions=[], coverage_of_change=1.0,
                                 change_mutation_score=None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.coverage_of_change = 0.0


# ---------------------------------------------------------------------------
# combine_evidence (US-10.3)
# ---------------------------------------------------------------------------

def test_combine_evidence_aggregates_uncovered_weak_and_score():
    coverage = compute_change_coverage(
        {"a.py": [(1, 5)], "b.py": [(1, 1)]},
        {"a.py": {1, 2}, "b.py": {1}},  # a.py: 3,4,5 uncovered; b.py fully covered
    )
    mutation_report = ChangeTargetedMutationReport(regions=[
        RegionEvaluation("a.py", 1, 2, PARTIALLY_VERIFIED, 0.5, ["x -> y @ line 1"]),
        RegionEvaluation("b.py", 1, 1, VERIFIED, 1.0, []),
    ])
    combined = combine_evidence(coverage, mutation_report)
    assert combined.uncovered_lines == {"a.py": [3, 4, 5]}
    assert [r.path for r in combined.weak_evidence_regions] == ["a.py"]
    assert combined.change_mutation_score == 0.75  # mean of 0.5 and 1.0
    assert combined.coverage_of_change == coverage.coverage_of_change


def test_combine_evidence_with_nothing_evaluated_has_no_score_not_zero():
    coverage = compute_change_coverage({}, {})
    combined = combine_evidence(coverage, ChangeTargetedMutationReport())
    assert combined.change_mutation_score is None
    assert combined.weak_evidence_regions == []
    assert combined.not_evaluated_regions == []


def test_combined_evidence_verdict_to_dict_is_json_shaped():
    v = CombinedEvidenceVerdict(
        uncovered_lines={"a.py": [1]},
        weak_evidence_regions=[RegionEvaluation("a.py", 2, 2, UNVERIFIED, 0.1, ["x"])],
        not_evaluated_regions=[RegionEvaluation("b.py", 1, 1, NOT_EVALUATED, None)],
        coverage_of_change=0.5,
        change_mutation_score=0.1,
    )
    d = v.to_dict()
    assert d["uncovered_lines"] == {"a.py": [1]}
    assert d["weak_evidence_regions"] == [
        {"path": "a.py", "start": 2, "end": 2, "status": UNVERIFIED,
         "mutation_score": 0.1, "survivors": ["x"]}
    ]
    assert d["not_evaluated_regions"] == [
        {"path": "b.py", "start": 1, "end": 1, "status": NOT_EVALUATED,
         "mutation_score": None, "survivors": []}
    ]
    assert d["coverage_of_change"] == 0.5
    assert d["change_mutation_score"] == 0.1


def test_combine_evidence_separates_not_evaluated_from_weak():
    coverage = compute_change_coverage({}, {})
    mutation_report = ChangeTargetedMutationReport(
        regions=[
            RegionEvaluation("a.py", 1, 1, NOT_EVALUATED, None, []),
            RegionEvaluation("b.py", 1, 1, UNVERIFIED, 0.2, ["x"]),
        ],
        budget_exhausted=True,
    )
    combined = combine_evidence(coverage, mutation_report)
    assert [r.path for r in combined.not_evaluated_regions] == ["a.py"]
    assert [r.path for r in combined.weak_evidence_regions] == ["b.py"]
    assert combined.change_mutation_score == 0.2  # only the evaluated one counts
