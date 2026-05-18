"""Template requirements for common avionics subsystems (DO-178C baseline).

These are reference requirements illustrating the AVERA schema.
Real project requirements come from the workspace requirements.csv.
"""

from __future__ import annotations

AVIONICS_REQUIREMENTS_TEMPLATE: list[dict[str, object]] = [
    # ── Flight Management System ──────────────────────────────────────────
    {
        "id": "FMS-REQ-001",
        "component": "Flight Management System",
        "requirement": (
            "Navigation position error shall not exceed 0.1 NM (185 m) "
            "under nominal GPS conditions."
        ),
        "metric": "position_error_nm",
        "operator": "<=",
        "threshold": 0.1,
        "safety_level": "dal-b",
        "next_checks": "FMS-NAV-SIL-01,FMS-NAV-SIL-02",
    },
    {
        "id": "FMS-REQ-002",
        "component": "Flight Management System",
        "requirement": (
            "Route computation time from pilot input to display "
            "shall not exceed 2.0 seconds."
        ),
        "metric": "route_compute_ms",
        "operator": "<=",
        "threshold": 2000.0,
        "safety_level": "dal-c",
        "next_checks": "FMS-PERF-SIL-01",
    },
    # ── Full Authority Digital Engine Control ─────────────────────────────
    {
        "id": "FADEC-REQ-001",
        "component": "Full Authority Digital Engine Control",
        "requirement": (
            "Engine overspeed protection must activate within 50 ms "
            "when N1 exceeds 105% of rated speed."
        ),
        "metric": "overspeed_response_ms",
        "operator": "<=",
        "threshold": 50.0,
        "safety_level": "dal-a",
        "next_checks": "FADEC-ENG-HIL-01,FADEC-ENG-HIL-02",
    },
    {
        "id": "FADEC-REQ-002",
        "component": "Full Authority Digital Engine Control",
        "requirement": (
            "Fuel flow computation error shall not exceed 0.5% of "
            "full-scale flow at any operating point."
        ),
        "metric": "fuel_flow_error_pct",
        "operator": "<=",
        "threshold": 0.5,
        "safety_level": "dal-b",
        "next_checks": "FADEC-FUEL-SIL-01",
    },
    # ── Flight Control Computer ───────────────────────────────────────────
    {
        "id": "FCC-REQ-001",
        "component": "Flight Control Computer",
        "requirement": (
            "Control surface actuation latency from pilot input "
            "to surface movement shall not exceed 80 ms."
        ),
        "metric": "actuation_latency_ms",
        "operator": "<=",
        "threshold": 80.0,
        "safety_level": "dal-a",
        "next_checks": "FCC-CTRL-HIL-01,FCC-CTRL-HIL-02",
    },
    {
        "id": "FCC-REQ-002",
        "component": "Flight Control Computer",
        "requirement": (
            "Envelope protection system must engage within 200 ms "
            "upon detection of an overspeed exceedance."
        ),
        "metric": "envelope_engage_ms",
        "operator": "<=",
        "threshold": 200.0,
        "safety_level": "dal-a",
        "next_checks": "FCC-ENV-HIL-01",
    },
]
