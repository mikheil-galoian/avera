"""Pre-built powertrain requirement catalogue for AVERA.

Provides the full powertrain requirement set as both a Python list and a
CSV-generation helper so that fixture files can be produced programmatically
or the catalogue can be consumed directly by :func:`avera.ingestion.load_requirements`.

Requirement schema (matches AVERA requirements CSV columns)::

    id            — unique requirement identifier (PT-REQ-XXX)
    component     — subsystem name (e.g. "Engine Control Unit")
    requirement   — human-readable text description
    metric        — metric key measured by tests
    operator      — comparison direction (<= or >=)
    threshold     — numeric limit
    safety_level  — AVERA safety level string (critical / high / medium / low / none)
    next_checks   — comma-separated test IDs that verify this requirement
"""

from __future__ import annotations

import csv
import io
from typing import Any

from .constants import ASIL_TO_SAFETY_LEVEL, Metrics, threshold_operator, THRESHOLDS

# ---------------------------------------------------------------------------
# Full powertrain requirement catalogue
# ---------------------------------------------------------------------------

POWERTRAIN_REQUIREMENTS: list[dict[str, Any]] = [

    # -----------------------------------------------------------------------
    # Engine overspeed protection — ASIL D (critical)
    # -----------------------------------------------------------------------
    {
        "id": "PT-REQ-001",
        "component": "Engine Control Unit",
        "requirement": (
            "Maximum engine speed must not exceed 7000 RPM "
            "under any operating condition or fault state."
        ),
        "metric": Metrics.MAX_ENGINE_RPM,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.MAX_ENGINE_RPM],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_d"],
        "next_checks": "PT-ECU-OS-01,PT-ECU-OS-02",
    },
    {
        "id": "PT-REQ-002",
        "component": "Engine Control Unit",
        "requirement": (
            "ECU overspeed fuel cut-off must engage within 50 ms "
            "of detecting an overspeed condition."
        ),
        "metric": Metrics.OVERSPEED_RESPONSE_MS,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.OVERSPEED_RESPONSE_MS],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_d"],
        "next_checks": "PT-ECU-OS-01,PT-ECU-OS-02",
    },

    # -----------------------------------------------------------------------
    # Throttle response — ASIL C (high)
    # -----------------------------------------------------------------------
    {
        "id": "PT-REQ-003",
        "component": "Engine Control Unit",
        "requirement": (
            "Throttle response from 100% to 0% must complete within 120 ms "
            "to support safe deceleration."
        ),
        "metric": Metrics.THROTTLE_RESPONSE_MS,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.THROTTLE_RESPONSE_MS],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_c"],
        "next_checks": "PT-ECU-THR-01",
    },

    # -----------------------------------------------------------------------
    # Transmission shift quality — ASIL B (medium)
    # -----------------------------------------------------------------------
    {
        "id": "PT-REQ-010",
        "component": "Transmission Control Unit",
        "requirement": (
            "Torque hole duration during any gear change must not exceed 100 ms "
            "to prevent driveline shock."
        ),
        "metric": Metrics.TORQUE_HOLE_MS,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.TORQUE_HOLE_MS],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_b"],
        "next_checks": "PT-TCU-SQ-01,PT-TCU-SQ-02",
    },
    {
        "id": "PT-REQ-011",
        "component": "Transmission Control Unit",
        "requirement": (
            "Full gear engagement must complete within 800 ms "
            "from shift command initiation."
        ),
        "metric": Metrics.SHIFT_COMPLETION_MS,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.SHIFT_COMPLETION_MS],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_b"],
        "next_checks": "PT-TCU-SQ-01,PT-TCU-SQ-02",
    },
    {
        "id": "PT-REQ-012",
        "component": "Transmission Control Unit",
        "requirement": (
            "Gear slip ratio during shift must not exceed 0.05 "
            "to ensure mechanical integrity."
        ),
        "metric": Metrics.GEAR_SLIP_RATIO,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.GEAR_SLIP_RATIO],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_b"],
        "next_checks": "PT-TCU-SQ-02",
    },

    # -----------------------------------------------------------------------
    # Fuel injection — ASIL B (medium)
    # -----------------------------------------------------------------------
    {
        "id": "PT-REQ-020",
        "component": "Fuel Injection System",
        "requirement": (
            "Injection timing error relative to target must not exceed 2.0 degrees BTDC "
            "to maintain combustion efficiency and emission limits."
        ),
        "metric": Metrics.INJECTION_TIMING_ERROR_DEG,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.INJECTION_TIMING_ERROR_DEG],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_b"],
        "next_checks": "PT-FIS-INJ-01",
    },
    {
        "id": "PT-REQ-021",
        "component": "Fuel Injection System",
        "requirement": (
            "Common rail pressure must remain at or above 100 bar "
            "during all injection events to ensure complete atomisation."
        ),
        "metric": Metrics.INJECTION_PRESSURE_BAR,
        "operator": ">=",
        "threshold": THRESHOLDS[Metrics.INJECTION_PRESSURE_BAR],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_b"],
        "next_checks": "PT-FIS-INJ-01,PT-FIS-INJ-02",
    },

    # -----------------------------------------------------------------------
    # Thermal management — ASIL B / A
    # -----------------------------------------------------------------------
    {
        "id": "PT-REQ-040",
        "component": "Thermal Management System",
        "requirement": (
            "Engine coolant temperature must not exceed 115 °C "
            "under sustained high-load operation."
        ),
        "metric": Metrics.COOLANT_TEMP_C,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.COOLANT_TEMP_C],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_b"],
        "next_checks": "PT-TMS-COOL-01",
    },
    {
        "id": "PT-REQ-041",
        "component": "Thermal Management System",
        "requirement": (
            "Engine oil temperature must not exceed 140 °C "
            "to preserve lubrication film integrity."
        ),
        "metric": Metrics.OIL_TEMP_C,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.OIL_TEMP_C],
        "safety_level": ASIL_TO_SAFETY_LEVEL["asil_a"],
        "next_checks": "PT-TMS-COOL-01",
    },

    # -----------------------------------------------------------------------
    # Emissions — QM / regulatory
    # -----------------------------------------------------------------------
    {
        "id": "PT-REQ-030",
        "component": "Emissions Management System",
        "requirement": (
            "NOₓ emissions must not exceed 60 mg/km (Euro 6d type-approval limit)."
        ),
        "metric": Metrics.NOX_MG_PER_KM,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.NOX_MG_PER_KM],
        "safety_level": "low",
        "next_checks": "PT-EMS-NOX-01",
    },
    {
        "id": "PT-REQ-031",
        "component": "Emissions Management System",
        "requirement": (
            "Fleet-average CO₂ emissions must not exceed 95 g/km "
            "(EU fleet CO₂ regulation target)."
        ),
        "metric": Metrics.CO2_G_PER_KM,
        "operator": "<=",
        "threshold": THRESHOLDS[Metrics.CO2_G_PER_KM],
        "safety_level": "low",
        "next_checks": "PT-EMS-NOX-01",
    },
]

# ---------------------------------------------------------------------------
# Filtered views
# ---------------------------------------------------------------------------

_CSV_COLUMNS = (
    "id", "component", "requirement", "metric",
    "operator", "threshold", "safety_level", "next_checks",
)


def requirements_for_component(component: str) -> list[dict[str, Any]]:
    """Return requirements whose ``component`` matches *component* (case-insensitive)."""
    needle = component.lower()
    return [r for r in POWERTRAIN_REQUIREMENTS if needle in r["component"].lower()]


def requirements_for_safety_level(level: str) -> list[dict[str, Any]]:
    """Return requirements at a given AVERA safety level."""
    return [r for r in POWERTRAIN_REQUIREMENTS if r["safety_level"] == level]


def requirements_by_id(*ids: str) -> list[dict[str, Any]]:
    """Return only the requirements whose ``id`` is in *ids*."""
    id_set = set(ids)
    return [r for r in POWERTRAIN_REQUIREMENTS if r["id"] in id_set]


# ---------------------------------------------------------------------------
# CSV serialisation helper
# ---------------------------------------------------------------------------

def to_csv(reqs: list[dict[str, Any]] | None = None) -> str:
    """Serialise *reqs* (or the full catalogue) to a CSV string.

    The CSV format is identical to the AVERA requirements CSV schema so it
    can be written to disk and consumed by :func:`avera.ingestion.load_requirements`.
    """
    if reqs is None:
        reqs = POWERTRAIN_REQUIREMENTS

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for req in reqs:
        writer.writerow({col: req.get(col, "") for col in _CSV_COLUMNS})
    return buf.getvalue()
