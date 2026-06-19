"""AVERA Space domain — NASA NPR 7150.2 / NASA-STD-8739.8 support."""

from .constants import (
    NASA_A, NASA_B, NASA_C, NASA_D, NASA_E, NASA_F,
    NASA_CLASS_RANK, NASA_CLASS_LABELS,
    RIGOR_BY_CLASS,
    REGULATORY_REFERENCE,
    STANDARD,
    nasa_class_rank,
    required_rigor,
    independent_assurance_required,
)
from .requirements import SPACE_REQUIREMENTS_TEMPLATE

__all__ = [
    "NASA_A", "NASA_B", "NASA_C", "NASA_D", "NASA_E", "NASA_F",
    "NASA_CLASS_RANK", "NASA_CLASS_LABELS",
    "RIGOR_BY_CLASS",
    "REGULATORY_REFERENCE",
    "STANDARD",
    "nasa_class_rank",
    "required_rigor",
    "independent_assurance_required",
    "SPACE_REQUIREMENTS_TEMPLATE",
]
