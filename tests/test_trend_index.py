from __future__ import annotations

import inspect
import json
from copy import deepcopy
from typing import Any

import pytest


trend_index = pytest.importorskip(
    "avera.trends.index",
    reason="trend index module is not implemented yet",
)


def test_build_trend_index_tracks_verdict_and_risk_history_newest_first() -> None:
    index = _build_trend_index(
        memory_records=[
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T10:00:00Z",
                "verdict": "possible_regression",
                "risk": "medium",
                "affected_components": ["BMS Power"],
                "affected_requirements": [{"id": "BMS-REQ-112"}],
            },
            {
                "record_type": "gate",
                "timestamp_utc": "2026-04-23T10:05:00Z",
                "verdict": "confirmed_regression",
                "risk": "high",
                "gate_status": "blocked",
                "gate_exit_code": 2,
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
            },
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T10:10:00Z",
                "verdict": "successful_change",
                "risk": "low",
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
            },
        ],
        traceability=_trend_traceability(),
    )

    assert _history_timestamps(index, "verdict_history") == [
        "2026-04-23T10:10:00Z",
        "2026-04-23T10:05:00Z",
        "2026-04-23T10:00:00Z",
    ]
    assert _history_values(index, "verdict_history", "verdict") == [
        "successful_change",
        "confirmed_regression",
        "possible_regression",
    ]
    assert _history_timestamps(index, "risk_history") == [
        "2026-04-23T10:10:00Z",
        "2026-04-23T10:05:00Z",
        "2026-04-23T10:00:00Z",
    ]
    assert _history_values(index, "risk_history", "risk") == [
        "low",
        "high",
        "medium",
    ]


def test_build_trend_index_counts_component_trends() -> None:
    index = _build_trend_index(
        memory_records=[
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T10:00:00Z",
                "verdict": "possible_regression",
                "risk": "medium",
                "affected_components": ["BMS Power"],
                "affected_requirements": [{"id": "BMS-REQ-112"}],
            },
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T10:10:00Z",
                "verdict": "confirmed_regression",
                "risk": "high",
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
            },
            {
                "record_type": "gate",
                "timestamp_utc": "2026-04-23T10:15:00Z",
                "verdict": "confirmed_regression",
                "risk": "high",
                "gate_status": "blocked",
                "gate_exit_code": 2,
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
            },
        ],
        traceability=_trend_traceability(),
    )

    thermal_control = _entry_by_id(index["components"], "BMS Thermal Control")
    assert _first_int(thermal_control, "history_count", "event_count", "analysis_count", "record_count") == 2
    assert _counter_map(thermal_control, "verdict_counts") == {
        "confirmed_regression": 2,
    }
    assert _counter_map(thermal_control, "risk_counts") == {
        "high": 2,
    }

    power = _entry_by_id(index["components"], "BMS Power")
    assert _first_int(power, "history_count", "event_count", "analysis_count", "record_count") == 1
    assert _counter_map(power, "verdict_counts") == {
        "possible_regression": 1,
    }
    assert _counter_map(power, "risk_counts") == {
        "medium": 1,
    }


def test_build_trend_index_counts_requirement_trends() -> None:
    index = _build_trend_index(
        memory_records=[
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T10:00:00Z",
                "verdict": "possible_regression",
                "risk": "medium",
                "affected_components": ["BMS Power"],
                "affected_requirements": [{"id": "BMS-REQ-112"}],
            },
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T10:10:00Z",
                "verdict": "confirmed_regression",
                "risk": "high",
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
            },
            {
                "record_type": "gate",
                "timestamp_utc": "2026-04-23T10:15:00Z",
                "verdict": "confirmed_regression",
                "risk": "high",
                "gate_status": "blocked",
                "gate_exit_code": 2,
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
            },
        ],
        traceability=_trend_traceability(),
    )

    req_118 = _entry_by_id(index["requirements"], "BMS-REQ-118")
    assert _first_int(req_118, "history_count", "event_count", "analysis_count", "record_count") == 2
    assert _counter_map(req_118, "verdict_counts") == {
        "confirmed_regression": 2,
    }
    assert _counter_map(req_118, "risk_counts") == {
        "high": 2,
    }

    req_112 = _entry_by_id(index["requirements"], "BMS-REQ-112")
    assert _first_int(req_112, "history_count", "event_count", "analysis_count", "record_count") == 1
    assert _counter_map(req_112, "verdict_counts") == {
        "possible_regression": 1,
    }
    assert _counter_map(req_112, "risk_counts") == {
        "medium": 1,
    }


def test_build_trend_index_groups_test_stability_into_buckets() -> None:
    index = _build_trend_index(
        memory_records=[
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T08:00:00Z",
                "verdict": "successful_change",
                "risk": "low",
                "affected_components": ["BMS Power"],
                "affected_requirements": [{"id": "BMS-REQ-112"}],
                "test_results": [
                    {"test_id": "TC-BOOT-02", "status": "pass"},
                    {"test_id": "TC-FAST-01", "status": "pass"},
                ],
            },
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T09:00:00Z",
                "verdict": "possible_regression",
                "risk": "medium",
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
                "test_results": [
                    {"test_id": "TC-BOOT-02", "status": "pass"},
                    {"test_id": "TC-FAST-01", "status": "fail"},
                ],
            },
            {
                "record_type": "analysis",
                "timestamp_utc": "2026-04-23T10:00:00Z",
                "verdict": "confirmed_regression",
                "risk": "high",
                "affected_components": ["BMS Thermal Control"],
                "affected_requirements": [{"id": "BMS-REQ-118"}],
                "test_results": [
                    {"test_id": "TC-BOOT-02", "status": "pass"},
                    {"test_id": "TC-FAST-01", "status": "fail"},
                    {"test_id": "TC-ENV-01", "status": "error"},
                ],
            },
        ],
        traceability=_trend_traceability(),
    )

    buckets = _stability_buckets(index)
    assert _bucket_ids_any(buckets, "stable", "consistent") == ["TC-BOOT-02"]
    assert _bucket_ids_any(buckets, "regressed", "regression") == ["TC-FAST-01"]
    assert _bucket_ids_any(buckets, "unstable", "flaky", "inconsistent") == ["TC-ENV-01"]


def test_build_trend_index_is_stable_for_input_order() -> None:
    memory_records = [
        {
            "record_type": "analysis",
            "timestamp_utc": "2026-04-23T10:00:00Z",
            "verdict": "possible_regression",
            "risk": "medium",
            "affected_components": ["BMS Power"],
            "affected_requirements": [{"id": "BMS-REQ-112"}],
            "test_results": [{"test_id": "TC-BOOT-02", "status": "pass"}],
        },
        {
            "record_type": "analysis",
            "timestamp_utc": "2026-04-23T10:10:00Z",
            "verdict": "confirmed_regression",
            "risk": "high",
            "affected_components": ["BMS Thermal Control", "BMS Power"],
            "affected_requirements": [{"id": "BMS-REQ-118"}, {"id": "BMS-REQ-112"}],
            "test_results": [
                {"test_id": "TC-BOOT-02", "status": "fail"},
                {"test_id": "TC-FAST-01", "status": "fail"},
            ],
        },
        {
            "record_type": "gate",
            "timestamp_utc": "2026-04-23T10:12:00Z",
            "verdict": "confirmed_regression",
            "risk": "high",
            "gate_status": "blocked",
            "gate_exit_code": 2,
            "affected_components": ["BMS Thermal Control"],
            "affected_requirements": [{"id": "BMS-REQ-118"}],
            "affected_tests": ["TC-FAST-01", "TC-BOOT-02"],
        },
    ]

    first = _build_trend_index(memory_records=memory_records, traceability=_trend_traceability())
    second = _build_trend_index(
        memory_records=list(reversed(deepcopy(memory_records))),
        traceability=deepcopy(_trend_traceability()),
    )

    assert _canonicalize(first) == _canonicalize(second)
    assert _history_timestamps(first, "verdict_history") == [
        "2026-04-23T10:12:00Z",
        "2026-04-23T10:10:00Z",
        "2026-04-23T10:00:00Z",
    ]
    assert _history_timestamps(first, "risk_history") == [
        "2026-04-23T10:12:00Z",
        "2026-04-23T10:10:00Z",
        "2026-04-23T10:00:00Z",
    ]
    assert _container_ids(first["components"]) == ["BMS Power", "BMS Thermal Control"]
    assert _container_ids(first["requirements"]) == ["BMS-REQ-112", "BMS-REQ-118"]
    assert _container_ids(first["tests"]) == ["TC-BOOT-02", "TC-ENV-01", "TC-FAST-01"]


def test_build_trend_index_handles_empty_input() -> None:
    index = _build_trend_index(memory_records=[], traceability=None)

    assert _history_timestamps(index, "verdict_history") == []
    assert _history_timestamps(index, "risk_history") == []
    assert _container_ids(index["components"]) == []
    assert _container_ids(index["requirements"]) == []
    assert _container_ids(index["tests"]) == []
    assert _stability_buckets(index) == {}
    assert _summary_counts(index) == {
        "component_count": 0,
        "requirement_count": 0,
        "test_count": 0,
        "memory_record_count": 0,
    }


def _build_trend_index(
    memory_records: list[dict[str, Any]],
    *,
    traceability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    function = trend_index.build_trend_index
    signature = inspect.signature(function)

    if "traceability" in signature.parameters:
        return function(memory_records=memory_records, traceability=traceability)

    parameters = list(signature.parameters.values())
    if len(parameters) >= 2:
        second_parameter = parameters[1]
        if second_parameter.kind is inspect.Parameter.KEYWORD_ONLY:
            return function(memory_records, **{second_parameter.name: traceability})
        return function(memory_records, traceability)

    return function(memory_records)


def _trend_traceability() -> dict[str, Any]:
    return {
        "schema_version": "avera.trend_traceability.v0.1",
        "components": {
            "BMS Power": {
                "requirements": ["BMS-REQ-112"],
                "tests": ["TC-BOOT-02"],
            },
            "BMS Thermal Control": {
                "requirements": ["BMS-REQ-118"],
                "tests": ["TC-FAST-01", "TC-ENV-01"],
            },
        },
        "requirements": {
            "BMS-REQ-112": {
                "components": ["BMS Power"],
                "tests": ["TC-BOOT-02"],
            },
            "BMS-REQ-118": {
                "components": ["BMS Thermal Control"],
                "tests": ["TC-FAST-01", "TC-ENV-01"],
            },
        },
        "tests": {
            "TC-BOOT-02": {
                "components": ["BMS Power"],
                "requirements": ["BMS-REQ-112"],
            },
            "TC-FAST-01": {
                "components": ["BMS Thermal Control"],
                "requirements": ["BMS-REQ-118"],
            },
            "TC-ENV-01": {
                "components": ["BMS Thermal Control"],
                "requirements": ["BMS-REQ-118"],
            },
        },
    }


def _entry_by_id(container: Any, wanted_id: str) -> dict[str, Any]:
    if isinstance(container, dict):
        value = container[wanted_id]
        if isinstance(value, dict):
            return value
        return {"id": wanted_id, "value": value}

    for item in container:
        if not isinstance(item, dict):
            if str(item) == wanted_id:
                return {"id": wanted_id}
            continue
        candidate = _first_text(item, ("id", "component", "requirement", "test", "name"))
        if candidate == wanted_id:
            return item

    raise AssertionError(f"Could not find {wanted_id!r} in {container!r}")


def _history_timestamps(index: dict[str, Any], key: str) -> list[str | None]:
    return [item.get("timestamp_utc") for item in _history_records(index, key)]


def _history_values(index: dict[str, Any], key: str, field_name: str) -> list[str | None]:
    return [item.get(field_name) for item in _history_records(index, key)]


def _history_records(index: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = index.get(key)
    if value is None:
        return []
    if isinstance(value, dict):
        return [value[k] for k in sorted(value)]
    return list(value)


def _counter_map(entry: dict[str, Any], *field_names: str) -> dict[str, int]:
    for field_name in field_names:
        value = entry.get(field_name)
        if isinstance(value, dict):
            return {str(key): int(count) for key, count in sorted(value.items())}
    return {}


def _first_int(entry: dict[str, Any], *field_names: str) -> int:
    for field_name in field_names:
        value = entry.get(field_name)
        if value is None:
            continue
        return int(value)
    raise AssertionError(f"Could not find an integer value in {entry!r}")


def _stability_buckets(index: dict[str, Any]) -> dict[str, list[str]]:
    value = index.get("test_stability_buckets")
    if value is None:
        value = index.get("stability_buckets")
    if value is None:
        tests = index.get("tests")
        if isinstance(tests, dict):
            buckets: dict[str, list[str]] = {}
            for test_id, item in tests.items():
                if not isinstance(item, dict):
                    continue
                bucket_name = str(item.get("stability_bucket") or item.get("bucket") or "").strip()
                if bucket_name:
                    buckets.setdefault(bucket_name, []).append(str(test_id))
            return {key: sorted(values) for key, values in sorted(buckets.items())}
        if isinstance(tests, list):
            buckets = {}
            for item in tests:
                if not isinstance(item, dict):
                    continue
                bucket_name = str(item.get("stability_bucket") or item.get("bucket") or "").strip()
                test_id = str(item.get("test_id") or item.get("test") or item.get("id") or "").strip()
                if bucket_name and test_id:
                    buckets.setdefault(bucket_name, []).append(test_id)
            return {key: sorted(values) for key, values in sorted(buckets.items())}
        return {}
    if isinstance(value, dict):
        result: dict[str, list[str]] = {}
        for bucket_name, bucket_items in value.items():
            if isinstance(bucket_items, dict):
                entries = bucket_items.get("tests") or bucket_items.get("items") or bucket_items.get("test_ids") or []
            else:
                entries = bucket_items
            result[str(bucket_name)] = sorted(_stringify_ids(entries))
        return result
    return {}


def _bucket_ids_any(buckets: dict[str, list[str]], *bucket_names: str) -> list[str]:
    for bucket_name in bucket_names:
        values = buckets.get(bucket_name)
        if values is not None:
            return list(values)
    return []


def _container_ids(container: Any) -> list[str]:
    if isinstance(container, dict):
        return sorted(str(key) for key in container.keys())
    return sorted(_first_text(item, ("id", "component", "requirement", "test", "name")) for item in container)


def _summary_counts(index: dict[str, Any]) -> dict[str, int]:
    summary = index.get("summary") or {}
    record_count = summary.get("memory_record_count")
    if record_count is None:
        record_count = int(summary.get("memory_analysis_records", 0)) + int(summary.get("memory_gate_records", 0))
    return {
        "component_count": int(summary.get("component_count", 0)),
        "requirement_count": int(summary.get("requirement_count", 0)),
        "test_count": int(summary.get("test_count", 0)),
        "memory_record_count": int(record_count),
    }


def _stringify_ids(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, dict):
        values = values.values()
    if isinstance(values, str):
        values = [values]
    result: list[str] = []
    for item in values:
        if isinstance(item, dict):
            text = _first_text(item, ("id", "test_id", "name", "component", "requirement"))
        else:
            text = str(item).strip()
        if text:
            result.append(text)
    return sorted(dict.fromkeys(result))


def _first_text(value: dict[str, Any], field_names: tuple[str, ...]) -> str:
    for field_name in field_names:
        item = value.get(field_name)
        if item is None:
            continue
        text = str(item).strip()
        if text:
            return text
    return ""


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple((str(key), _canonicalize(item)) for key, item in sorted(value.items()))
    if isinstance(value, (list, tuple, set)):
        items = [_canonicalize(item) for item in value]
        return tuple(sorted(items, key=lambda item: json.dumps(item, sort_keys=True, default=str)))
    return value
