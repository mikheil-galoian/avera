"""Pre-built powertrain verification fixture sets for AVERA.

Each fixture set is a self-contained scenario that exercises the AVERA
pipeline end-to-end with realistic powertrain data.  Fixture sets are
returned as pure Python dicts — no file I/O required — so they integrate
cleanly with unit tests and CI pipelines.

Available scenarios
-------------------
``OVERSPEED_REGRESSION``
    ECU overspeed limiter modified; new code raises the effective RPM cap,
    causing test PT-ECU-OS-01 to fail with ``max_engine_rpm=7250``.
    Expected AVERA verdict: ``confirmed_regression``, risk ``critical``.

``SHIFT_QUALITY_REGRESSION``
    TCU shift control retuned; torque hole duration during 3→4 upshift
    increased to 143 ms, exceeding the 100 ms limit.
    Expected verdict: ``confirmed_regression``, risk ``medium``.

``EMISSIONS_IMPROVEMENT``
    Emissions management calibration improved; NOₓ and CO₂ metrics both
    dropped below baseline.  No failures in baseline or current.
    Expected verdict: ``no_regression``.

Fixture structure
-----------------
Each scenario dict has the keys::

    baseline       — AVERA verification-run dict (runId, stage, tests)
    current        — AVERA verification-run dict
    requirements   — list of requirement dicts (AVERA schema)
    component_map  — dict mapping source file → {component, requirements, tests}
    change_description — str explaining the change

Usage::

    from avera.domains.powertrain.fixtures import OVERSPEED_REGRESSION
    from avera.core import analyze   # or pipeline equivalent
"""

from __future__ import annotations

from typing import Any

from .requirements import requirements_by_id


# ---------------------------------------------------------------------------
# Scenario 1 — Engine overspeed regression (ASIL-D, critical)
# ---------------------------------------------------------------------------

OVERSPEED_REGRESSION: dict[str, Any] = {
    "baseline": {
        "runId": "baseline-pt-overspeed-001",
        "stage": "baseline",
        "tests": [
            {
                "id": "PT-ECU-OS-01",
                "component": "Engine Control Unit",
                "status": "passed",
                "metrics": {
                    "max_engine_rpm": 6850.0,
                    "overspeed_response_ms": 38.0,
                },
                "evidence": "",
            },
            {
                "id": "PT-ECU-OS-02",
                "component": "Engine Control Unit",
                "status": "passed",
                "metrics": {
                    "max_engine_rpm": 6720.0,
                    "overspeed_response_ms": 41.0,
                },
                "evidence": "",
            },
        ],
    },
    "current": {
        "runId": "current-pt-overspeed-001",
        "stage": "current",
        "tests": [
            {
                "id": "PT-ECU-OS-01",
                "component": "Engine Control Unit",
                "status": "failed",
                "metrics": {
                    "max_engine_rpm": 7250.0,   # exceeds PT-REQ-001 limit of 7000
                    "overspeed_response_ms": 42.0,
                },
                "evidence": (
                    "Engine speed reached 7250 RPM during wide-open-throttle ramp. "
                    "Overspeed limiter threshold raised in ECU calibration; "
                    "PT-REQ-001 violation confirmed."
                ),
            },
            {
                "id": "PT-ECU-OS-02",
                "component": "Engine Control Unit",
                "status": "passed",
                "metrics": {
                    "max_engine_rpm": 6840.0,
                    "overspeed_response_ms": 40.0,
                },
                "evidence": "",
            },
        ],
    },
    "requirements": requirements_by_id("PT-REQ-001", "PT-REQ-002"),
    "component_map": {
        "src/ecu/overspeed_protection.c": {
            "component": "Engine Control Unit",
            "requirements": ["PT-REQ-001", "PT-REQ-002"],
            "tests": ["PT-ECU-OS-01", "PT-ECU-OS-02"],
        },
    },
    "change_description": (
        "An engineer raised the overspeed limiter threshold in "
        "src/ecu/overspeed_protection.c from 7000 RPM to 7500 RPM to "
        "allow higher performance tuning profiles.  The change violates "
        "PT-REQ-001 (ASIL-D) and must be reverted or justified by a "
        "full safety case update per ISO 26262."
    ),
    # Reference outcome for test assertions
    "_expected": {
        "verdict": "confirmed_regression",
        "risk": "release_blocking",   # ASIL-D safety_level → release_blocking
    },
}


# ---------------------------------------------------------------------------
# Scenario 2 — Transmission shift quality regression (ASIL-B, medium)
# ---------------------------------------------------------------------------

SHIFT_QUALITY_REGRESSION: dict[str, Any] = {
    "baseline": {
        "runId": "baseline-pt-shift-001",
        "stage": "baseline",
        "tests": [
            {
                "id": "PT-TCU-SQ-01",
                "component": "Transmission Control Unit",
                "status": "passed",
                "metrics": {
                    "torque_hole_ms": 87.0,
                    "shift_completion_ms": 720.0,
                    "gear_slip_ratio": 0.031,
                },
                "evidence": "",
            },
            {
                "id": "PT-TCU-SQ-02",
                "component": "Transmission Control Unit",
                "status": "passed",
                "metrics": {
                    "torque_hole_ms": 92.0,
                    "shift_completion_ms": 755.0,
                    "gear_slip_ratio": 0.028,
                },
                "evidence": "",
            },
        ],
    },
    "current": {
        "runId": "current-pt-shift-001",
        "stage": "current",
        "tests": [
            {
                "id": "PT-TCU-SQ-01",
                "component": "Transmission Control Unit",
                "status": "failed",
                "metrics": {
                    "torque_hole_ms": 143.0,    # exceeds PT-REQ-010 limit of 100 ms
                    "shift_completion_ms": 780.0,
                    "gear_slip_ratio": 0.033,
                },
                "evidence": (
                    "Torque hole of 143 ms detected during 3→4 upshift at 60 km/h. "
                    "TCU clutch fill pressure recalibration produced a longer "
                    "open-clutch window, breaching PT-REQ-010."
                ),
            },
            {
                "id": "PT-TCU-SQ-02",
                "component": "Transmission Control Unit",
                "status": "passed",
                "metrics": {
                    "torque_hole_ms": 95.0,
                    "shift_completion_ms": 762.0,
                    "gear_slip_ratio": 0.030,
                },
                "evidence": "",
            },
        ],
    },
    "requirements": requirements_by_id("PT-REQ-010", "PT-REQ-011", "PT-REQ-012"),
    "component_map": {
        "src/tcu/shift_controller.c": {
            "component": "Transmission Control Unit",
            "requirements": ["PT-REQ-010", "PT-REQ-011", "PT-REQ-012"],
            "tests": ["PT-TCU-SQ-01", "PT-TCU-SQ-02"],
        },
    },
    "change_description": (
        "TCU clutch fill pressure was recalibrated in src/tcu/shift_controller.c "
        "to reduce clutch wear on 3→4 upshifts.  The longer clutch fill time "
        "inadvertently extended the torque-hole window from 87 ms (baseline) "
        "to 143 ms (current), violating PT-REQ-010."
    ),
    "_expected": {
        "verdict": "confirmed_regression",
        "risk": "medium",
    },
}


# ---------------------------------------------------------------------------
# Scenario 3 — Emissions improvement / no regression (QM)
# ---------------------------------------------------------------------------

EMISSIONS_IMPROVEMENT: dict[str, Any] = {
    "baseline": {
        "runId": "baseline-pt-emissions-001",
        "stage": "baseline",
        "tests": [
            {
                "id": "PT-EMS-NOX-01",
                "component": "Emissions Management System",
                "status": "passed",
                "metrics": {
                    "nox_mg_per_km": 54.0,
                    "co2_g_per_km": 91.0,
                },
                "evidence": "",
            },
        ],
    },
    "current": {
        "runId": "current-pt-emissions-001",
        "stage": "current",
        "tests": [
            {
                "id": "PT-EMS-NOX-01",
                "component": "Emissions Management System",
                "status": "passed",
                "metrics": {
                    "nox_mg_per_km": 49.0,     # improved vs baseline
                    "co2_g_per_km": 88.0,      # improved vs baseline
                },
                "evidence": "",
            },
        ],
    },
    "requirements": requirements_by_id("PT-REQ-030", "PT-REQ-031"),
    "component_map": {
        "src/ems/emissions_monitor.c": {
            "component": "Emissions Management System",
            "requirements": ["PT-REQ-030", "PT-REQ-031"],
            "tests": ["PT-EMS-NOX-01"],
        },
    },
    "change_description": (
        "Emissions management calibration updated in src/ems/emissions_monitor.c "
        "to improve SCR dosing efficiency.  Both NOₓ and CO₂ metrics improved "
        "versus baseline.  No threshold violations."
    ),
    # "successful_change" is AVERA's verdict when both baseline and current pass
    "_expected": {
        "verdict": "successful_change",
    },
}


# ---------------------------------------------------------------------------
# Registry — all named fixtures in one place
# ---------------------------------------------------------------------------

ALL_FIXTURES: dict[str, dict[str, Any]] = {
    "powertrain-overspeed-regression": OVERSPEED_REGRESSION,
    "powertrain-shift-quality":        SHIFT_QUALITY_REGRESSION,
    "powertrain-emissions-ok":         EMISSIONS_IMPROVEMENT,
}


def get_fixture(name: str) -> dict[str, Any]:
    """Return a fixture by its registry name.

    Raises
    ------
    KeyError
        If *name* is not a registered fixture.
    """
    try:
        return ALL_FIXTURES[name]
    except KeyError:
        available = ", ".join(sorted(ALL_FIXTURES))
        raise KeyError(
            f"Unknown powertrain fixture {name!r}. "
            f"Available: {available}"
        ) from None
