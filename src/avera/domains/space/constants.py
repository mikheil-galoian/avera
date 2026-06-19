"""NASA software classification (NPR 7150.2) constants and assurance rigor.

NASA classifies flight and ground software by criticality. The governing public
standards are NPR 7150.2 (NASA Software Engineering Requirements) and
NASA-STD-8739.8 (Software Assurance and Software Safety Standard). Higher class =
more required verification, documentation, and independence.

  Class A — Human-rated space flight software            (most critical)
  Class B — Non-human-rated / mission-critical flight software
  Class C — Mission support / ground systems controlling space assets
  Class D — Basic science & engineering / analysis software
  Class E — Design concept, research & technology software
  Class F — General-purpose / business & IT software     (least critical)

NASA defines six classes; AVERA's safety-rank scale has five buckets (0..4), so
Class D and E both map to "minor" (rank 1). Safety-criticality is an orthogonal
NASA designation: when a component is flagged safety-critical, its effective
class should be treated as A regardless of the base class.

Class identifiers use a ``nasa-`` prefix so they never collide with the
single-letter ASIL forms or the ``class-`` IEC-62304 medical forms already in
:data:`avera.classify.risk_levels.SAFETY_LEVEL_RANK`.
"""

from __future__ import annotations

# NASA software class identifiers
NASA_A = "nasa-a"
NASA_B = "nasa-b"
NASA_C = "nasa-c"
NASA_D = "nasa-d"
NASA_E = "nasa-e"
NASA_F = "nasa-f"

# Human-readable labels
NASA_CLASS_LABELS: dict[str, str] = {
    NASA_A: "Class A — Human-Rated Flight",
    NASA_B: "Class B — Mission-Critical Flight",
    NASA_C: "Class C — Mission Support / Ground Control",
    NASA_D: "Class D — Science & Engineering",
    NASA_E: "Class E — Research & Technology",
    NASA_F: "Class F — General Purpose",
}

# Rank: higher number = more critical (mirrors DAL_RANK in the avionics domain).
# Six NASA classes are compressed onto AVERA's five-bucket scale (D and E -> 1).
NASA_CLASS_RANK: dict[str, int] = {
    NASA_F: 0,
    NASA_E: 1,
    NASA_D: 1,
    NASA_C: 2,
    NASA_B: 3,
    NASA_A: 4,
}

# Aliases accepted in requirements CSV (normalised lower-case). Single-letter
# forms are intentionally NOT included — they are reserved for ASIL.
_NASA_ALIASES: dict[str, int] = {
    "nasa-a": 4, "nasa_a": 4, "nasaa": 4, "class-a-nasa": 4,
    "nasa-b": 3, "nasa_b": 3, "nasab": 3,
    "nasa-c": 2, "nasa_c": 2, "nasac": 2,
    "nasa-d": 1, "nasa_d": 1, "nasad": 1,
    "nasa-e": 1, "nasa_e": 1, "nasae": 1,
    "nasa-f": 0, "nasa_f": 0, "nasaf": 0,
    # descriptive forms
    "human_rated": 4, "human-rated": 4,
    "mission_critical": 3, "mission-critical": 3,
    "mission_support": 2, "mission-support": 2,
    "general_purpose": 0, "general-purpose": 0,
}

# Verification rigor per class (illustrative, DO-178C-aligned as NASA practice
# commonly references). Classes A/B add independent software assurance.
RIGOR_BY_CLASS: dict[str, list[str]] = {
    NASA_A: ["statement", "branch", "MCDC", "independent_assurance"],
    NASA_B: ["statement", "branch", "MCDC", "independent_assurance"],
    NASA_C: ["statement", "branch"],
    NASA_D: ["statement"],
    NASA_E: [],
    NASA_F: [],
}

STANDARD = "NASA NPR 7150.2 / NASA-STD-8739.8"
REGULATORY_REFERENCE = (
    "NASA NPR 7150.2 (NASA Software Engineering Requirements) and "
    "NASA-STD-8739.8 (Software Assurance and Software Safety Standard)"
)


def nasa_class_rank(value: object) -> int:
    """Return sortable rank for a NASA software class (0 = least critical)."""
    normalised = str(value or "").strip().lower().replace(" ", "_")
    return _NASA_ALIASES.get(normalised, 0)


def required_rigor(nasa_class: str) -> list[str]:
    """Return the verification rigor activities required for a NASA class."""
    key = str(nasa_class or "").strip().lower()
    if len(key) == 1:
        key = f"nasa-{key}"
    return RIGOR_BY_CLASS.get(key, [])


def independent_assurance_required(nasa_class: str) -> bool:
    """Return True when a class requires independent software assurance (A/B)."""
    return "independent_assurance" in required_rigor(nasa_class)
