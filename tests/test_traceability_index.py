from __future__ import annotations

import json
import inspect
from copy import deepcopy
from typing import Any

import pytest


traceability = pytest.importorskip(
    "avera.traceability.index",
    reason="traceability index module is not implemented yet",
)


def test_build_traceability_index_aggregates_report_and_memory_records() -> None:
    report = {
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "affected_components": [
            "BMS Thermal Control",
            "BMS Power",
            "BMS Thermal Control",
        ],
        "affected_requirements": [
            {"id": "BMS-REQ-118", "component": "BMS Thermal Control"},
            {"id": "BMS-REQ-112", "component": "BMS Power"},
        ],
        "introduced_failures": [
            {
                "test_id": "TC-FAST-01",
                "component": "BMS Thermal Control",
                "requirement_id": "BMS-REQ-118",
                "status": "fail",
            }
        ],
        "preexisting_failures": [
            {
                "test_id": "TC-BOOT-02",
                "component": "BMS Power",
                "requirement_id": "BMS-REQ-112",
                "status": "fail",
            }
        ],
        "threshold_evidence": [
            {
                "test_id": "TC-FAST-01",
                "requirement_id": "BMS-REQ-118",
                "metric": "max_cell_temp_c",
                "operator": "<=",
                "threshold": 50.0,
                "baseline_passed": True,
                "current_passed": False,
            }
        ],
    }
    memory_records = [
        {
            "record_type": "analysis",
            "timestamp_utc": "2026-04-23T10:11:12Z",
            "verdict": "confirmed_regression",
            "risk": "high",
            "affected_components": [
                "BMS Charge Controller",
                "BMS Thermal Control",
            ],
            "affected_requirements": [
                {"id": "BMS-REQ-119"},
                {"id": "BMS-REQ-118"},
            ],
            "introduced_failures": [
                {
                    "test_id": "TC-FAST-01",
                    "component": "BMS Thermal Control",
                    "requirement_id": "BMS-REQ-118",
                }
            ],
            "preexisting_failures": [
                {
                    "test_id": "TC-SOAK-03",
                    "component": "BMS Charge Controller",
                    "requirement_id": "BMS-REQ-119",
                }
            ],
            "threshold_evidence": [
                {
                    "test_id": "TC-SOAK-03",
                    "requirement_id": "BMS-REQ-119",
                    "metric": "pack_temp_c",
                    "operator": "<=",
                    "threshold": 55.0,
                    "baseline_passed": True,
                    "current_passed": True,
                }
            ],
        },
        {
            "record_type": "gate",
            "timestamp_utc": "2026-04-23T10:12:00Z",
            "gate_status": "blocked",
            "gate_exit_code": 2,
            "verdict": "confirmed_regression",
            "risk": "high",
            "report_path": "reports/avera-report.json",
            "affected_components": ["BMS Thermal Control"],
            "affected_requirements": [{"id": "BMS-REQ-118"}],
            "affected_tests": ["TC-FAST-01"],
        },
    ]

    index = _build_traceability_index(report, memory_records=memory_records)

    assert index["schema_version"] == "avera.traceability_index.v0.1"
    assert index["summary"] == {
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "confidence_score": None,
        "component_count": 3,
        "requirement_count": 3,
        "test_count": 3,
        "failure_count": 4,
        "memory_analysis_records": 1,
        "memory_gate_records": 1,
    }
    assert _bucket_ids(index, "components", ("component", "name", "id")) == [
        "BMS Charge Controller",
        "BMS Power",
        "BMS Thermal Control",
    ]
    assert _bucket_ids(index, "requirements", ("requirement", "id", "name")) == [
        "BMS-REQ-112",
        "BMS-REQ-118",
        "BMS-REQ-119",
    ]
    assert _bucket_ids(index, "tests", ("test", "test_id", "id", "name")) == [
        "TC-BOOT-02",
        "TC-FAST-01",
        "TC-SOAK-03",
    ]
    assert _history_timestamps(index["risks"][0]["records"]) == [
        "2026-04-23T10:12:00Z",
        "2026-04-23T10:11:12Z",
        None,
    ]
    assert _bucket_ids(index, "gates", ("gate", "gate_status", "status", "id")) == [
        "blocked",
    ]

    thermal_control = next(
        item for item in index["components"] if item["component"] == "BMS Thermal Control"
    )
    assert _sorted_text_values(
        thermal_control,
        "requirements",
        "affected_requirements",
        "requirement_ids",
    ) == ["BMS-REQ-118"]
    assert _sorted_text_values(
        thermal_control,
        "tests",
        "affected_tests",
        "test_ids",
    ) == ["TC-FAST-01"]
    assert _history_timestamps(thermal_control["risk_history"][0]["records"]) == [
        "2026-04-23T10:12:00Z",
        "2026-04-23T10:11:12Z",
        None,
    ]
    assert thermal_control["gate_history"] == [
        {
            "gate_status": "blocked",
            "status": "blocked",
            "gate_exit_codes": [2],
            "records": [
                {
                    "timestamp_utc": "2026-04-23T10:12:00Z",
                    "verdict": "confirmed_regression",
                    "risk": "high",
                    "report_path": "reports/avera-report.json",
                    "reasons": [],
                }
            ],
        }
    ]

    requirements = _bucket_entries(index, "requirements", ("requirement", "id", "name"))
    requirement_118 = next(item for item in requirements if item["id"] == "BMS-REQ-118")
    assert _sorted_text_values(
        requirement_118,
        "components",
        "affected_components",
        "component_ids",
    ) == ["BMS Charge Controller", "BMS Thermal Control"]
    assert _sorted_text_values(
        requirement_118,
        "tests",
        "affected_tests",
        "test_ids",
    ) == ["TC-FAST-01"]

    tests = _bucket_entries(index, "tests", ("test", "test_id", "id", "name"))
    fast_charge = next(item for item in tests if item["id"] == "TC-FAST-01")
    assert _sorted_text_values(
        fast_charge,
        "components",
        "component",
        "affected_components",
    ) == ["BMS Thermal Control"]
    assert _sorted_text_values(
        fast_charge,
        "requirements",
        "affected_requirements",
        "requirement_ids",
    ) == ["BMS-REQ-118"]

    charge_controller = next(
        item for item in index["components"] if item["component"] == "BMS Charge Controller"
    )
    assert _sorted_text_values(
        charge_controller,
        "requirements",
        "affected_requirements",
        "requirement_ids",
    ) == ["BMS-REQ-118", "BMS-REQ-119"]
    assert _sorted_text_values(
        charge_controller,
        "tests",
        "affected_tests",
        "test_ids",
    ) == ["TC-SOAK-03"]
    assert _history_timestamps(charge_controller["risk_history"][0]["records"]) == [
        "2026-04-23T10:12:00Z",
        "2026-04-23T10:11:12Z",
        None,
    ]
    assert charge_controller["gate_history"] == thermal_control["gate_history"]

    power = next(item for item in index["components"] if item["component"] == "BMS Power")
    assert _sorted_text_values(
        power,
        "requirements",
        "affected_requirements",
        "requirement_ids",
    ) == ["BMS-REQ-112"]
    assert _sorted_text_values(
        power,
        "tests",
        "affected_tests",
        "test_ids",
    ) == ["TC-BOOT-02"]
    assert _history_timestamps(power["risk_history"][0]["records"]) == [
        "2026-04-23T10:12:00Z",
        "2026-04-23T10:11:12Z",
        None,
    ]
    assert power["gate_history"] == thermal_control["gate_history"]


def test_build_traceability_index_works_without_memory_records() -> None:
    report = {
        "verdict": "possible_regression",
        "risk": "medium",
        "confidence": "medium",
        "affected_components": ["BMS Power"],
        "affected_requirements": [{"id": "BMS-REQ-112", "component": "BMS Power"}],
        "introduced_failures": [
            {
                "test_id": "TC-BOOT-02",
                "component": "BMS Power",
                "requirement_id": "BMS-REQ-112",
            }
        ],
    }

    with_memory = _build_traceability_index(report, memory_records=None)
    without_memory = _build_traceability_index(report)

    assert _canonicalize(with_memory) == _canonicalize(without_memory)
    assert _bucket_ids(without_memory, "components", ("component", "name", "id")) == [
        "BMS Power",
    ]
    assert _bucket_ids(
        without_memory,
        "requirements",
        ("requirement", "id", "name"),
    ) == ["BMS-REQ-112"]
    assert _bucket_ids(without_memory, "tests", ("test", "test_id", "id", "name")) == [
        "TC-BOOT-02",
    ]


def test_build_traceability_index_is_stable_for_input_order() -> None:
    report = {
        "verdict": "confirmed_regression",
        "risk": "high",
        "confidence": "high",
        "affected_components": [
            "BMS Charge Controller",
            "BMS Thermal Control",
            "BMS Power",
            "BMS Thermal Control",
        ],
        "affected_requirements": [
            {"id": "BMS-REQ-119", "component": "BMS Charge Controller"},
            {"id": "BMS-REQ-112", "component": "BMS Power"},
            {"id": "BMS-REQ-118", "component": "BMS Thermal Control"},
        ],
        "introduced_failures": [
            {
                "test_id": "TC-FAST-01",
                "component": "BMS Thermal Control",
                "requirement_id": "BMS-REQ-118",
            },
            {
                "test_id": "TC-BOOT-02",
                "component": "BMS Power",
                "requirement_id": "BMS-REQ-112",
            },
        ],
        "preexisting_failures": [
            {
                "test_id": "TC-SOAK-03",
                "component": "BMS Charge Controller",
                "requirement_id": "BMS-REQ-119",
            }
        ],
        "threshold_evidence": [
            {
                "test_id": "TC-SOAK-03",
                "requirement_id": "BMS-REQ-119",
                "metric": "pack_temp_c",
                "operator": "<=",
                "threshold": 55.0,
                "baseline_passed": True,
                "current_passed": True,
            },
            {
                "test_id": "TC-FAST-01",
                "requirement_id": "BMS-REQ-118",
                "metric": "max_cell_temp_c",
                "operator": "<=",
                "threshold": 50.0,
                "baseline_passed": True,
                "current_passed": False,
            },
        ],
    }

    memory_records = [
        {
            "record_type": "analysis",
            "timestamp_utc": "2026-04-23T10:09:00Z",
            "verdict": "possible_regression",
            "risk": "medium",
            "affected_components": ["BMS Thermal Control"],
            "affected_requirements": [
                {"id": "BMS-REQ-118"},
            ],
            "introduced_failures": [
                {
                    "test_id": "TC-FAST-01",
                    "component": "BMS Thermal Control",
                    "requirement_id": "BMS-REQ-118",
                }
            ],
        },
        {
            "record_type": "gate",
            "timestamp_utc": "2026-04-23T10:12:00Z",
            "gate_status": "blocked",
            "gate_exit_code": 2,
            "verdict": "confirmed_regression",
            "risk": "high",
            "affected_components": ["BMS Thermal Control", "BMS Charge Controller"],
            "affected_requirements": [
                {"id": "BMS-REQ-118"},
                {"id": "BMS-REQ-119"},
            ],
            "affected_tests": ["TC-FAST-01", "TC-SOAK-03"],
        },
        {
            "record_type": "analysis",
            "timestamp_utc": "2026-04-23T10:11:12Z",
            "verdict": "confirmed_regression",
            "risk": "high",
            "affected_components": [
                "BMS Power",
                "BMS Thermal Control",
                "BMS Charge Controller",
            ],
            "affected_requirements": [
                {"id": "BMS-REQ-112"},
                {"id": "BMS-REQ-118"},
                {"id": "BMS-REQ-119"},
            ],
            "introduced_failures": [
                {
                    "test_id": "TC-BOOT-02",
                    "component": "BMS Power",
                    "requirement_id": "BMS-REQ-112",
                }
            ],
        },
    ]

    first = _build_traceability_index(report, memory_records=memory_records)
    second = _build_traceability_index(
        deepcopy(
            {
                **report,
                "affected_components": list(reversed(report["affected_components"])),
                "affected_requirements": list(reversed(report["affected_requirements"])),
                "introduced_failures": list(reversed(report["introduced_failures"])),
                "preexisting_failures": list(reversed(report["preexisting_failures"])),
                "threshold_evidence": list(reversed(report["threshold_evidence"])),
            }
        ),
        memory_records=list(reversed(memory_records)),
    )

    assert _canonicalize(first) == _canonicalize(second)
    assert first["summary"]["memory_analysis_records"] == 2
    assert first["summary"]["memory_gate_records"] == 1
    assert _bucket_ids(first, "components", ("component", "name", "id")) == [
        "BMS Charge Controller",
        "BMS Power",
        "BMS Thermal Control",
    ]
    assert _bucket_ids(first, "requirements", ("requirement", "id", "name")) == [
        "BMS-REQ-112",
        "BMS-REQ-118",
        "BMS-REQ-119",
    ]
    assert _bucket_ids(first, "tests", ("test", "test_id", "id", "name")) == [
        "TC-BOOT-02",
        "TC-FAST-01",
        "TC-SOAK-03",
    ]
    thermal_control = next(
        item for item in first["components"] if item["component"] == "BMS Thermal Control"
    )
    assert _history_timestamps(thermal_control["risk_history"][0]["records"]) == [
        "2026-04-23T10:12:00Z",
        "2026-04-23T10:11:12Z",
        None,
    ]
    assert _history_timestamps(thermal_control["risk_history"][1]["records"]) == [
        "2026-04-23T10:09:00Z",
    ]
    assert _history_timestamps(thermal_control["gate_history"][0]["records"]) == [
        "2026-04-23T10:12:00Z",
    ]
    assert first["gates"] == [
        {
            "gate_status": "blocked",
            "status": "blocked",
            "gate_exit_codes": [2],
            "records": [
                {
                    "timestamp_utc": "2026-04-23T10:12:00Z",
                    "verdict": "confirmed_regression",
                    "risk": "high",
                    "report_path": None,
                    "reasons": [],
                }
            ],
        }
    ]


def _build_traceability_index(
    report: dict[str, Any],
    memory_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    function = traceability.build_traceability_index
    signature = inspect.signature(function)
    parameters = list(signature.parameters.values())

    if len(parameters) == 1:
        return function(report)

    second_parameter = parameters[1]
    if second_parameter.name == "memory_records":
        return function(report, memory_records=memory_records)

    if second_parameter.kind is inspect.Parameter.KEYWORD_ONLY:
        if memory_records is None:
            return function(report, **{second_parameter.name: None})
        return function(report, **{second_parameter.name: memory_records})

    if second_parameter.kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    ):
        if memory_records is None:
            return function(report, None)
        return function(report, memory_records)

    if memory_records is None:
        return function(report)
    return function(report, memory_records=memory_records)


def _bucket_entries(
    index: dict[str, Any],
    bucket_name: str,
    identifier_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    bucket = index[bucket_name]
    if isinstance(bucket, dict):
        items = []
        for key, value in bucket.items():
            if isinstance(value, dict):
                entry = {"id": _first_text(value, identifier_fields, default=str(key))}
                entry.update(value)
            else:
                entry = {"id": str(key), "value": value}
            items.append(entry)
        return sorted(items, key=lambda item: item["id"])

    items = []
    for value in bucket:
        if isinstance(value, dict):
            entry = {"id": _first_text(value, identifier_fields)}
            entry.update(value)
        else:
            entry = {"id": str(value)}
        items.append(entry)
    return sorted(items, key=lambda item: item["id"])


def _bucket_ids(
    index: dict[str, Any],
    bucket_name: str,
    identifier_fields: tuple[str, ...],
) -> list[str]:
    return [item["id"] for item in _bucket_entries(index, bucket_name, identifier_fields)]


def _history_timestamps(history: list[dict[str, Any]]) -> list[str | None]:
    return [item.get("timestamp_utc") for item in history]


def _sorted_text_values(
    entry: dict[str, Any],
    *field_names: str,
) -> list[str]:
    for field_name in field_names:
        value = entry.get(field_name)
        if value is None:
            continue
        if isinstance(value, dict):
            items = [str(key) for key in value.keys()]
        elif isinstance(value, (list, tuple, set)):
            items = [str(item) for item in value if str(item).strip()]
        else:
            items = [str(value)] if str(value).strip() else []
        return sorted(dict.fromkeys(items))
    return []


def _first_text(
    value: dict[str, Any],
    field_names: tuple[str, ...],
    *,
    default: str | None = None,
) -> str:
    for field_name in field_names:
        item = value.get(field_name)
        if item is None:
            continue
        text = str(item).strip()
        if text:
            return text
    if default is not None:
        return default
    raise AssertionError(f"Could not determine identifier from {value!r}")


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple((str(key), _canonicalize(item)) for key, item in sorted(value.items()))
    if isinstance(value, (list, tuple, set)):
        items = [_canonicalize(item) for item in value]
        return tuple(sorted(items, key=lambda item: json.dumps(item, sort_keys=True, default=str)))
    return value
