"""Build trend indexes from AVERA memory and traceability artifacts."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


SCHEMA_VERSION = "avera.trend_index.v0.1"


def build_trend_index(
    memory_records: list[dict[str, Any]],
    traceability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic trend index from memory and optional traceability."""

    records = sorted(
        list(memory_records or []),
        key=lambda record: str(record.get("timestamp_utc") or ""),
        reverse=True,
    )
    traceability = traceability or {}

    verdict_history = _history(records, "verdict")
    risk_history = _history(records, "risk")
    components = _component_trends(records, traceability)
    requirements = _requirement_trends(records, traceability)
    tests, test_stability_buckets = _test_trends(records, traceability)

    analysis_count = sum(1 for record in records if record.get("record_type") == "analysis")
    gate_count = sum(1 for record in records if record.get("record_type") == "gate")

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "component_count": len(components),
            "requirement_count": len(requirements),
            "test_count": len(tests),
            "memory_record_count": len(records),
            "memory_analysis_records": analysis_count,
            "memory_gate_records": gate_count,
        },
        "verdict_history": verdict_history,
        "risk_history": risk_history,
        "components": components,
        "requirements": requirements,
        "tests": tests,
        "test_stability_buckets": test_stability_buckets,
    }


def _history(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in records:
        value = str(record.get(field) or "").strip()
        if not value:
            continue
        item = {
            "timestamp_utc": record.get("timestamp_utc"),
            field: value,
            "record_type": record.get("record_type"),
        }
        if field == "verdict":
            item["risk"] = record.get("risk")
        if field == "risk":
            item["verdict"] = record.get("verdict")
        items.append(item)
    return items


def _component_trends(records: list[dict[str, Any]], traceability: dict[str, Any]) -> list[dict[str, Any]]:
    stats = {
        name: {
            "component": name,
            "history_count": 0,
            "verdict_counts": Counter(),
            "risk_counts": Counter(),
            "latest_timestamp_utc": None,
        }
        for name in _component_names(traceability)
    }

    for record in records:
        verdict = str(record.get("verdict") or "unknown")
        risk = str(record.get("risk") or "unknown")
        timestamp = str(record.get("timestamp_utc") or "")
        for component in _record_component_names(record):
            entry = stats.setdefault(
                component,
                {
                    "component": component,
                    "history_count": 0,
                    "verdict_counts": Counter(),
                    "risk_counts": Counter(),
                    "latest_timestamp_utc": None,
                },
            )
            entry["history_count"] += 1
            entry["verdict_counts"][verdict] += 1
            entry["risk_counts"][risk] += 1
            if timestamp and (entry["latest_timestamp_utc"] is None or timestamp > entry["latest_timestamp_utc"]):
                entry["latest_timestamp_utc"] = timestamp

    return [
        {
            "component": name,
            "history_count": entry["history_count"],
            "verdict_counts": dict(sorted(entry["verdict_counts"].items())),
            "risk_counts": dict(sorted(entry["risk_counts"].items())),
            "latest_timestamp_utc": entry["latest_timestamp_utc"],
        }
        for name, entry in sorted(stats.items())
    ]


def _requirement_trends(records: list[dict[str, Any]], traceability: dict[str, Any]) -> list[dict[str, Any]]:
    stats = {
        name: {
            "requirement": name,
            "history_count": 0,
            "verdict_counts": Counter(),
            "risk_counts": Counter(),
            "latest_timestamp_utc": None,
        }
        for name in _requirement_names(traceability)
    }

    for record in records:
        verdict = str(record.get("verdict") or "unknown")
        risk = str(record.get("risk") or "unknown")
        timestamp = str(record.get("timestamp_utc") or "")
        for requirement in _record_requirement_names(record):
            entry = stats.setdefault(
                requirement,
                {
                    "requirement": requirement,
                    "history_count": 0,
                    "verdict_counts": Counter(),
                    "risk_counts": Counter(),
                    "latest_timestamp_utc": None,
                },
            )
            entry["history_count"] += 1
            entry["verdict_counts"][verdict] += 1
            entry["risk_counts"][risk] += 1
            if timestamp and (entry["latest_timestamp_utc"] is None or timestamp > entry["latest_timestamp_utc"]):
                entry["latest_timestamp_utc"] = timestamp

    return [
        {
            "requirement": name,
            "history_count": entry["history_count"],
            "verdict_counts": dict(sorted(entry["verdict_counts"].items())),
            "risk_counts": dict(sorted(entry["risk_counts"].items())),
            "latest_timestamp_utc": entry["latest_timestamp_utc"],
        }
        for name, entry in sorted(stats.items())
    ]


def _test_trends(
    records: list[dict[str, Any]],
    traceability: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    components_by_test: dict[str, set[str]] = {name: set() for name in _test_names(traceability)}
    requirements_by_test: dict[str, set[str]] = {name: set() for name in _test_names(traceability)}

    for test_name, meta in _traceability_tests(traceability).items():
        components_by_test.setdefault(test_name, set()).update(_string_list(meta.get("components")))
        requirements_by_test.setdefault(test_name, set()).update(_string_list(meta.get("requirements")))

    for record in records:
        for result in record.get("test_results") or []:
            if not isinstance(result, dict):
                continue
            test_name = str(result.get("test_id") or result.get("id") or "").strip()
            status = str(result.get("status") or "").strip().lower()
            if not test_name or not status:
                continue
            counters[test_name][status] += 1

    tests: list[dict[str, Any]] = []
    buckets: dict[str, list[str]] = {"stable": [], "regressed": [], "unstable": []}

    for test_name in sorted(set(_test_names(traceability)) | set(counters)):
        counts = counters.get(test_name, Counter())
        bucket = _stability_bucket(counts)
        tests.append(
            {
                "test": test_name,
                "components": sorted(components_by_test.get(test_name, set())),
                "requirements": sorted(requirements_by_test.get(test_name, set())),
                "status_counts": dict(sorted(counts.items())),
                "stability_bucket": bucket,
            }
        )
        if bucket:
            buckets.setdefault(bucket, []).append(test_name)

    buckets = {name: sorted(values) for name, values in sorted(buckets.items()) if values}
    return tests, buckets


def _stability_bucket(counts: Counter[str]) -> str:
    if counts.get("error", 0):
        return "unstable"
    if counts.get("fail", 0) or counts.get("failed", 0):
        return "regressed"
    if counts.get("pass", 0) or counts.get("passed", 0):
        return "stable"
    return ""


def _component_names(traceability: dict[str, Any]) -> set[str]:
    components = traceability.get("components") or {}
    if isinstance(components, dict):
        return {str(name).strip() for name in components if str(name).strip()}
    return {
        str(item.get("component") or "").strip()
        for item in components
        if isinstance(item, dict) and str(item.get("component") or "").strip()
    }


def _requirement_names(traceability: dict[str, Any]) -> set[str]:
    requirements = traceability.get("requirements") or {}
    if isinstance(requirements, dict):
        return {str(name).strip() for name in requirements if str(name).strip()}
    return {
        str(item.get("requirement") or "").strip()
        for item in requirements
        if isinstance(item, dict) and str(item.get("requirement") or "").strip()
    }


def _test_names(traceability: dict[str, Any]) -> set[str]:
    tests = traceability.get("tests") or {}
    if isinstance(tests, dict):
        return {str(name).strip() for name in tests if str(name).strip()}
    return {
        str(item.get("test") or "").strip()
        for item in tests
        if isinstance(item, dict) and str(item.get("test") or "").strip()
    }


def _traceability_tests(traceability: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tests = traceability.get("tests") or {}
    if isinstance(tests, dict):
        return {str(name): value for name, value in tests.items() if isinstance(value, dict)}
    return {
        str(item.get("test")): item
        for item in tests
        if isinstance(item, dict) and str(item.get("test") or "").strip()
    }


def _record_component_names(record: dict[str, Any]) -> list[str]:
    return _string_list(record.get("affected_components"))


def _record_requirement_names(record: dict[str, Any]) -> list[str]:
    return _string_list(record.get("affected_requirements"))


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    else:
        values = value if isinstance(value, list | tuple | set) else [value]
    results: list[str] = []
    for item in values:
        if isinstance(item, dict):
            text = str(item.get("id") or "").strip()
        else:
            text = str(item).strip()
        if text:
            results.append(text)
    return sorted(set(results))
