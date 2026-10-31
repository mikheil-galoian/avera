"""Change coverage mapping (AVERA Change Impact, EP-09).

Answers one question a pass/fail gate cannot: *is the code that actually
changed backed by any test at all?* Combines a unified diff (what changed)
with a standard coverage report (what tests touched) into a deterministic
per-file and aggregate coverage-of-change figure, with the uncovered lines
as first-class output — an auditor needs the lines, not just a percentage.

Deliberately not named ``coverage`` — ``avera.coverage`` already means
*requirement* coverage (which requirement has a test, for ISO 26262 /
IEC 62304 style audits). This package is *line* coverage of a *diff*, a
different concept entirely; see docs/AVERA_CHANGE_IMPACT_STAGE.md.

Zero new dependencies: unified diff is plain text, LCOV is line-oriented
text, Cobertura is XML (stdlib ``xml.etree``) — preserving AVERA's
zero-dependency property.

``mutation_targeting`` (EP-10) builds on this: it runs the mutation lens
(``avera.mutation``) automatically on changed+covered regions, upgrading
"covered" to "verified" without a human naming functions by hand.
"""

from __future__ import annotations

from .cobertura import parse_cobertura
from .diff import parse_unified_diff
from .lcov import parse_lcov
from .mutation_targeting import (
    ChangeTargetedMutationReport,
    CombinedEvidenceVerdict,
    RegionEvaluation,
    combine_evidence,
    run_change_targeted_mutation,
)
from .report import ChangeCoverageReport, FileCoverageOfChange, compute_change_coverage

__all__ = [
    "ChangeCoverageReport",
    "ChangeTargetedMutationReport",
    "CombinedEvidenceVerdict",
    "FileCoverageOfChange",
    "RegionEvaluation",
    "combine_evidence",
    "compute_change_coverage",
    "parse_cobertura",
    "parse_lcov",
    "parse_unified_diff",
    "run_change_targeted_mutation",
]
