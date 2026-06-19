"""Template requirements for common spacecraft subsystems (NASA NPR 7150.2).

These are reference requirements illustrating the AVERA schema for the space
domain. Real project requirements come from the workspace requirements.csv.
"""

from __future__ import annotations

SPACE_REQUIREMENTS_TEMPLATE: list[dict[str, object]] = [
    # ── Guidance, Navigation & Control ────────────────────────────────────
    {
        "id": "GNC-REQ-001",
        "component": "Guidance Navigation and Control",
        "requirement": (
            "Attitude determination error shall not exceed 0.05 degrees "
            "(3-sigma) during powered flight."
        ),
        "metric": "attitude_error_deg",
        "operator": "<=",
        "threshold": 0.05,
        "safety_level": "nasa-a",
        "next_checks": "GNC-ADCS-HIL-01,GNC-ADCS-HIL-02",
    },
    {
        "id": "GNC-REQ-002",
        "component": "Guidance Navigation and Control",
        "requirement": (
            "Thruster command latency from fault detection to actuation "
            "shall not exceed 20 ms."
        ),
        "metric": "thruster_latency_ms",
        "operator": "<=",
        "threshold": 20.0,
        "safety_level": "nasa-a",
        "next_checks": "GNC-RCS-HIL-01",
    },
    # ── Fault Detection, Isolation & Recovery ─────────────────────────────
    {
        "id": "FDIR-REQ-001",
        "component": "Fault Management",
        "requirement": (
            "Safe-mode entry must complete within 500 ms of an uncorrectable "
            "fault being latched."
        ),
        "metric": "safe_mode_entry_ms",
        "operator": "<=",
        "threshold": 500.0,
        "safety_level": "nasa-a",
        "next_checks": "FDIR-SAFE-SIL-01,FDIR-SAFE-SIL-02",
    },
    # ── Telemetry, Tracking & Command ─────────────────────────────────────
    {
        "id": "TTC-REQ-001",
        "component": "Telemetry Tracking and Command",
        "requirement": (
            "Uplink command authentication failure rate shall not exceed "
            "1e-9 per command."
        ),
        "metric": "command_auth_failure_rate",
        "operator": "<=",
        "threshold": 1e-9,
        "safety_level": "nasa-b",
        "next_checks": "TTC-CMD-SIL-01",
    },
    # ── Electrical Power Subsystem ────────────────────────────────────────
    {
        "id": "EPS-REQ-001",
        "component": "Electrical Power Subsystem",
        "requirement": (
            "Battery state-of-charge estimation error shall not exceed 3% "
            "across the operational temperature range."
        ),
        "metric": "soc_error_pct",
        "operator": "<=",
        "threshold": 3.0,
        "safety_level": "nasa-c",
        "next_checks": "EPS-BATT-SIL-01",
    },
]
