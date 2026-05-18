"""DO-178C Design Assurance Level (DAL) constants and coverage requirements.

DAL A — Catastrophic failure condition  (most critical, ~ASIL D)
DAL B — Hazardous/Severe failure condition
DAL C — Major failure condition
DAL D — Minor failure condition
DAL E — No safety effect              (least critical, ~QM)

Coverage requirements per DAL (DO-178C Table A-7):
  DAL A: Statement + Branch + MC/DC
  DAL B: Statement + Branch + MC/DC
  DAL C: Statement + Branch
  DAL D: Statement
  DAL E: None required
"""

from __future__ import annotations

# DAL level identifiers
DAL_A = "dal-a"
DAL_B = "dal-b"
DAL_C = "dal-c"
DAL_D = "dal-d"
DAL_E = "dal-e"

# Human-readable labels
DAL_LABELS: dict[str, str] = {
    DAL_A: "DAL A — Catastrophic",
    DAL_B: "DAL B — Hazardous",
    DAL_C: "DAL C — Major",
    DAL_D: "DAL D — Minor",
    DAL_E: "DAL E — No Safety Effect",
}

# Rank: higher number = more critical (mirrors ASIL_RANK in automotive domain)
DAL_RANK: dict[str, int] = {
    DAL_E: 0,
    DAL_D: 1,
    DAL_C: 2,
    DAL_B: 3,
    DAL_A: 4,
}

# Aliases accepted in requirements CSV (normalised lower-case)
_DAL_ALIASES: dict[str, int] = {
    # explicit DAL forms
    "dal-a": 4, "dal_a": 4, "dala": 4, "a": 4,
    "dal-b": 3, "dal_b": 3, "dalb": 3, "b": 3,
    "dal-c": 2, "dal_c": 2, "dalc": 2, "c": 2,
    "dal-d": 1, "dal_d": 1, "dald": 1, "d": 1,
    "dal-e": 0, "dal_e": 0, "dale": 0, "e": 0,
    # descriptive names
    "catastrophic": 4,
    "hazardous": 3,
    "major": 2,
    "minor": 1,
    "no_safety_effect": 0,
    "none": 0,
}

# Coverage requirements per DAL (DO-178C Table A-7)
COVERAGE_BY_DAL: dict[str, list[str]] = {
    DAL_A: ["statement", "branch", "MCDC"],
    DAL_B: ["statement", "branch", "MCDC"],
    DAL_C: ["statement", "branch"],
    DAL_D: ["statement"],
    DAL_E: [],
}

STANDARD = "DO-178C"
REGULATORY_REFERENCE = (
    "DO-178C Software Considerations in Airborne Systems "
    "and Equipment Certification (RTCA, 2011)"
)


def dal_rank(value: object) -> int:
    """Return sortable rank for a DAL safety label (0 = least critical)."""
    normalised = str(value or "").strip().lower().replace(" ", "_")
    return _DAL_ALIASES.get(normalised, 0)


def required_coverage(dal: str) -> list[str]:
    """Return the list of required coverage types for a given DAL level."""
    key = dal.strip().lower()
    # accept raw 'a' … 'e' as well as 'dal-a' … 'dal-e'
    if len(key) == 1:
        key = f"dal-{key}"
    return COVERAGE_BY_DAL.get(key, [])


def mcdc_required(dal: str) -> bool:
    """Return True if MC/DC coverage is required for the given DAL level."""
    return "MCDC" in required_coverage(dal)
