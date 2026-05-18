"""AVERA Powertrain domain module.

Provides ISO 26262-aligned constants, a pre-built requirement catalogue,
and ready-to-use verification fixture sets for powertrain ECU/TCU validation.

Quick start::

    from avera.domains.powertrain import (
        Metrics,
        THRESHOLDS,
        POWERTRAIN_REQUIREMENTS,
        OVERSPEED_REGRESSION,
        get_fixture,
    )

    # All requirements for critical safety level (ASIL-D)
    critical_reqs = [r for r in POWERTRAIN_REQUIREMENTS if r["safety_level"] == "critical"]

    # Pre-built fixture scenario
    fixture = get_fixture("powertrain-overspeed-regression")
    baseline = fixture["baseline"]
    current  = fixture["current"]
    reqs     = fixture["requirements"]
"""

from .constants import (
    ASIL_A,
    ASIL_B,
    ASIL_C,
    ASIL_D,
    ASIL_TO_SAFETY_LEVEL,
    Metrics,
    QM,
    SAFETY_LEVEL_TO_ASIL,
    THRESHOLD_OPERATORS,
    THRESHOLDS,
    asil_for_metric,
    threshold_operator,
)
from .fixtures import (
    ALL_FIXTURES,
    EMISSIONS_IMPROVEMENT,
    OVERSPEED_REGRESSION,
    SHIFT_QUALITY_REGRESSION,
    get_fixture,
)
from .requirements import (
    POWERTRAIN_REQUIREMENTS,
    requirements_by_id,
    requirements_for_component,
    requirements_for_safety_level,
    to_csv,
)

__all__ = [
    # ASIL constants
    "ASIL_D",
    "ASIL_C",
    "ASIL_B",
    "ASIL_A",
    "QM",
    "ASIL_TO_SAFETY_LEVEL",
    "SAFETY_LEVEL_TO_ASIL",
    # Metrics and thresholds
    "Metrics",
    "THRESHOLDS",
    "THRESHOLD_OPERATORS",
    "threshold_operator",
    "asil_for_metric",
    # Requirements catalogue
    "POWERTRAIN_REQUIREMENTS",
    "requirements_for_component",
    "requirements_for_safety_level",
    "requirements_by_id",
    "to_csv",
    # Fixture scenarios
    "OVERSPEED_REGRESSION",
    "SHIFT_QUALITY_REGRESSION",
    "EMISSIONS_IMPROVEMENT",
    "ALL_FIXTURES",
    "get_fixture",
]
