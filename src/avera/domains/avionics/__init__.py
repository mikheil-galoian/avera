"""AVERA Aviation domain — DO-178C / ARP4754A support."""

from .constants import (
    DAL_A, DAL_B, DAL_C, DAL_D, DAL_E,
    DAL_RANK, DAL_LABELS,
    COVERAGE_BY_DAL,
    REGULATORY_REFERENCE,
    STANDARD,
)
from .requirements import AVIONICS_REQUIREMENTS_TEMPLATE

__all__ = [
    "DAL_A", "DAL_B", "DAL_C", "DAL_D", "DAL_E",
    "DAL_RANK", "DAL_LABELS",
    "COVERAGE_BY_DAL",
    "REGULATORY_REFERENCE",
    "STANDARD",
    "AVIONICS_REQUIREMENTS_TEMPLATE",
]
