"""Powertrain domain constants for AVERA.

Defines ASIL safety levels (ISO 26262), canonical metric names, standard
safety thresholds, and their comparison operators for the powertrain
verification domain.

ASIL mapping
------------
ASIL D → "release_blocking"  (e.g. engine overspeed, brake torque)
ASIL C → "high"             (e.g. throttle response, clutch engagement)
ASIL B → "medium"           (e.g. transmission shift, injection timing)
ASIL A → "low"              (e.g. cabin comfort, fuel economy limits)
QM     → "none"             (non-safety quality metrics)

The ASIL-D mapping uses AVERA's "release_blocking" string (safety_rank 4) so
that confirmed regressions on ASIL-D requirements produce risk="release_blocking"
from the AVERA risk classifier.  This aligns with ISO 26262 Part 9 gate policy.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ASIL level identifiers
# ---------------------------------------------------------------------------

ASIL_D = "asil_d"
ASIL_C = "asil_c"
ASIL_B = "asil_b"
ASIL_A = "asil_a"
QM     = "qm"

# Map ASIL level → AVERA safety_level string used in requirements.
# Values must match AVERA's SAFETY_LEVEL_RANK table in classify/risk_levels.py.
ASIL_TO_SAFETY_LEVEL: dict[str, str] = {
    ASIL_D: "release_blocking",   # safety_rank 4 → risk=release_blocking on confirmed_regression
    ASIL_C: "high",
    ASIL_B: "medium",
    ASIL_A: "low",
    QM:     "none",
}

# Reverse map
SAFETY_LEVEL_TO_ASIL: dict[str, str] = {v: k for k, v in ASIL_TO_SAFETY_LEVEL.items()}


# ---------------------------------------------------------------------------
# Canonical metric names (use these everywhere to avoid typos)
# ---------------------------------------------------------------------------

class Metrics:
    """Canonical powertrain metric identifiers."""

    # Engine subsystem
    MAX_ENGINE_RPM          = "max_engine_rpm"
    OVERSPEED_RESPONSE_MS   = "overspeed_response_ms"
    IDLE_RPM                = "idle_rpm"
    THROTTLE_RESPONSE_MS    = "throttle_response_ms"

    # Transmission subsystem
    TORQUE_HOLE_MS          = "torque_hole_ms"
    SHIFT_COMPLETION_MS     = "shift_completion_ms"
    GEAR_SLIP_RATIO         = "gear_slip_ratio"

    # Fuel injection subsystem
    INJECTION_TIMING_ERROR_DEG = "injection_timing_error_deg"
    INJECTION_PRESSURE_BAR     = "injection_pressure_bar"
    RAIL_PRESSURE_DROP_BAR     = "rail_pressure_drop_bar"

    # Thermal management
    COOLANT_TEMP_C          = "coolant_temp_c"
    OIL_TEMP_C              = "oil_temp_c"
    EXHAUST_TEMP_C          = "exhaust_temp_c"

    # Emissions
    NOX_MG_PER_KM           = "nox_mg_per_km"
    CO2_G_PER_KM            = "co2_g_per_km"
    PM_MG_PER_KM            = "pm_mg_per_km"

    # Torque / power
    PEAK_TORQUE_NM          = "peak_torque_nm"
    TORQUE_ACCURACY_PERCENT = "torque_accuracy_percent"


# ---------------------------------------------------------------------------
# Standard safety thresholds (upper limits unless noted)
# ---------------------------------------------------------------------------
# Values are based on common automotive ECU/TCU specifications and emissions
# legislation (Euro 6d, ISO 26262 risk parameters).  Override per-project.

THRESHOLDS: dict[str, float] = {
    # Engine
    Metrics.MAX_ENGINE_RPM:           7000.0,   # RPM hard limit (ASIL-D)
    Metrics.OVERSPEED_RESPONSE_MS:      50.0,   # ms — ECU must cut fuel within 50 ms
    Metrics.THROTTLE_RESPONSE_MS:      120.0,   # ms — 10–0% throttle response

    # Transmission
    Metrics.TORQUE_HOLE_MS:            100.0,   # ms — torque interruption during shift
    Metrics.SHIFT_COMPLETION_MS:       800.0,   # ms — full gear engagement time
    Metrics.GEAR_SLIP_RATIO:             0.05,  # ratio — max allowable slip during shift

    # Injection
    Metrics.INJECTION_TIMING_ERROR_DEG:  2.0,   # degrees BTDC deviation
    Metrics.INJECTION_PRESSURE_BAR:    100.0,   # bar — MINIMUM (see THRESHOLD_OPERATORS)
    Metrics.RAIL_PRESSURE_DROP_BAR:     10.0,   # bar — max transient pressure drop

    # Thermal
    Metrics.COOLANT_TEMP_C:            115.0,   # °C — engine coolant warning limit
    Metrics.OIL_TEMP_C:                140.0,   # °C — engine oil temperature limit
    Metrics.EXHAUST_TEMP_C:            950.0,   # °C — catalyst inlet limit

    # Emissions (Euro 6d limits)
    Metrics.NOX_MG_PER_KM:             60.0,   # mg/km
    Metrics.CO2_G_PER_KM:              95.0,   # g/km (fleet average)
    Metrics.PM_MG_PER_KM:               4.5,   # mg/km

    # Torque
    Metrics.TORQUE_ACCURACY_PERCENT:     2.0,   # % deviation from requested torque
}

# Metrics where threshold is a MINIMUM (operator ">="); all others are "<="
THRESHOLD_OPERATORS: dict[str, str] = {
    Metrics.INJECTION_PRESSURE_BAR: ">=",
    Metrics.PEAK_TORQUE_NM:         ">=",
}


def threshold_operator(metric: str) -> str:
    """Return the comparison operator (``"<="`` or ``">="``)) for *metric*."""
    return THRESHOLD_OPERATORS.get(metric, "<=")


def asil_for_metric(metric: str) -> str:
    """Return a sensible default ASIL level for a powertrain metric.

    Used when auto-generating requirements without an explicit ASIL annotation.
    """
    _metric_asil: dict[str, str] = {
        Metrics.MAX_ENGINE_RPM:          ASIL_D,
        Metrics.OVERSPEED_RESPONSE_MS:   ASIL_D,
        Metrics.THROTTLE_RESPONSE_MS:    ASIL_C,
        Metrics.TORQUE_HOLE_MS:          ASIL_B,
        Metrics.SHIFT_COMPLETION_MS:     ASIL_B,
        Metrics.GEAR_SLIP_RATIO:         ASIL_B,
        Metrics.INJECTION_TIMING_ERROR_DEG: ASIL_B,
        Metrics.INJECTION_PRESSURE_BAR:  ASIL_B,
        Metrics.RAIL_PRESSURE_DROP_BAR:  ASIL_B,
        Metrics.COOLANT_TEMP_C:          ASIL_B,
        Metrics.OIL_TEMP_C:              ASIL_A,
        Metrics.EXHAUST_TEMP_C:          ASIL_A,
        Metrics.NOX_MG_PER_KM:          QM,
        Metrics.CO2_G_PER_KM:           QM,
        Metrics.PM_MG_PER_KM:           QM,
        Metrics.TORQUE_ACCURACY_PERCENT: ASIL_A,
    }
    return _metric_asil.get(metric, QM)
