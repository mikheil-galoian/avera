"""Build deterministic traceability indexes from AVERA evidence."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


SCHEMA_VERSION = "avera.traceability_index.v0.1"


def build_traceability_index(
    report: dict[str, Any],
    memory_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a component-first traceability index from report and memory records."""

    memory_records = memory_records or []
    components = _component_names(report)
    requirements = _requirements(report)
    failures = _failures(report)
    thresholds = _thresholds(report)

    component_index: dict[str, dict[str, Any]] = {}
    for component in components:
        component_index[component] = {
            "requirements": [],
            "tests": [],
            "failures": [],
            "threshold_evidence": [],
            "risk_history": [],
            "gate_history": [],
        }

    for requirement in requirements:
        component = requirement.get("component") or "unknown_component"
        bucket = component_index.setdefault(component, _empty_component_bucket())
        bucket["requirements"].append(requirement)

    for failure in failures:
        component = str(failure.get("component") or "unknown_component")
        bucket = component_index.setdefault(component, _empty_component_bucket())
        test_id = str(failure.get("test_id") or failure.get("id") or "unknown-test")
        if test_id not in bucket["tests"]:
            bucket["tests"].append(test_id)
        bucket["failures"].append(failure)

    for threshold in thresholds:
        component = _component_for_requirement(threshold.get("requirement_id"), requirements)
        bucket = component_index.setdefault(component, _empty_component_bucket())
        bucket["threshold_evidence"].append(threshold)
        test_id = threshold.get("test_id")
        if test_id and test_id not in bucket["tests"]:
            bucket["tests"].append(str(test_id))

    report_snapshot = _risk_snapshot(report)
    for component_name, component in component_index.items():
        component["risk_history"].extend(
            _risk_history_for_component(component_name, component, memory_records, report_snapshot)
        )
        component["gate_history"].extend(_gate_history(memory_records))
        _sort_component_bucket(component)

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": _summary(report, memory_records, component_index),
        "components": dict(sorted(component_index.items())),
        "requirements": sorted(requirements, key=lambda item: str(item.get("id") or "")),
        "tests": _tests(component_index),
        "risks": _risk_records(memory_records, report_snapshot),
        "gates": _gate_history(memory_records),
    }


def _component_names(report: dict[str, Any]) -> list[str]:
    values = report.get("affected_components") or []
    if not values and report.get("affected_component"):
        values = [report["affected_component"]]
    return _string_list(values) or ["unknown_component"]


def _requirements(report: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in report.get("affected_requirements") or []:
        if isinstance(item, dict):
            req_id = str(item.get("id") or "unknown-requirement")
            records.append(
                {
                    "id": req_id,
                    "component": str(item.get("component") or "unknown_component"),
                    "metric": item.get("metric"),
                    "safety_level": item.get("safety_level"),
                    "requirement": item.get("requirement"),
                }
            )
        else:
            records.append({"id": str(item), "component": "unknown_component"})
    return records


def _failures(report: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for category in ("introduced_failures", "preexisting_failures"):
        for item in report.get(category) or []:
            failure = dict(item) if isinstance(item, dict) else {"test_id": str(item)}
            failure["category"] = category
            records.append(failure)
    return records


def _thresholds(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item) if isinstance(item, dict) else {"metric": str(item)}
        for item in report.get("threshold_evidence") or []
    ]


def _component_for_requirement(requirement_id: Any, requirements: list[dict[str, Any]]) -> str:
    wanted = str(requirement_id or "")
    for requirement in requirements:
        if str(requirement.get("id") or "") == wanted:
            return str(requirement.get("component") or "unknown_component")
    return "unknown_component"


def _risk_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": "current_report",
        "timestamp_utc": None,
        "verdict": report.get("verdict"),
        "risk": report.get("risk"),
        "confidence": report.get("confidence"),
        "confidence_score": report.get("confidence_score"),
        "report_path": None,
    }


def _risk_history_for_component(
    component_name: str,
    component: dict[str, Any],
    memory_records: list[dict[str, Any]],
    report_snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    requirement_ids = {str(item.get("id")) for item in component["requirements"] if item.get("id")}
    records = [report_snapshot]
    for record in memory_records:
        if record.get("record_type") != "analysis":
            continue
        components = set(_string_list(record.get("affected_components")))
        requirements = set(_string_list(record.get("affected_requirements")))
        if components or requirements:
            matches_component = component_name in components
            matches_requirement = bool(requirement_ids & requirements)
            if not matches_component and not matches_requirement:
                continue
        records.append(_memory_risk_record(record))
    return _dedupe_records(records)


def _risk_records(
    memory_records: list[dict[str, Any]],
    report_snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    records = [report_snapshot]
    for record in memory_records:
        if record.get("record_type") == "analysis":
            records.append(_memory_risk_record(record))
    return _dedupe_records(records)


def _memory_risk_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "record_type": record.get("record_type"),
        "timestamp_utc": record.get("timestamp_utc"),
        "verdict": record.get("verdict"),
        "risk": record.get("risk"),
        "confidence": record.get("confidence"),
        "confidence_score": record.get("confidence_score"),
        "report_path": record.get("report_path"),
    }


def _gate_history(memory_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for record in memory_records:
        if record.get("record_type") != "gate":
            continue
        records.append(
            {
                "timestamp_utc": record.get("timestamp_utc"),
                "gate_status": record.get("gate_status"),
                "gate_exit_code": record.get("gate_exit_code"),
                "verdict": record.get("verdict"),
                "risk": record.get("risk"),
                "report_path": record.get("report_path"),
                "reasons": _string_list(record.get("reasons")),
            }
        )
    return sorted(records, key=lambda item: str(item.get("timestamp_utc") or ""), reverse=True)


def _summary(
    report: dict[str, Any],
    memory_records: list[dict[str, Any]],
    component_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    gate_count = sum(1 for item in memory_records if item.get("record_type") == "gate")
    analysis_count = sum(1 for item in memory_records if item.get("record_type") == "analysis")
    return {
        "verdict": report.get("verdict"),
        "risk": report.get("risk"),
        "confidence": report.get("confidence"),
        "confidence_score": report.get("confidence_score"),
        "component_count": len(component_index),
        "requirement_count": sum(len(item["requirements"]) for item in component_index.values()),
        "test_count": len(_tests(component_index)),
        "failure_count": sum(len(item["failures"]) for item in component_index.values()),
        "memory_analysis_records": analysis_count,
        "memory_gate_records": gate_count,
    }


def _tests(component_index: dict[str, dict[str, Any]]) -> list[str]:
    tests: set[str] = set()
    for item in component_index.values():
        tests.update(str(test) for test in item["tests"])
    return sorted(tests)


def _empty_component_bucket() -> dict[str, Any]:
    return {
        "requirements": [],
        "tests": [],
        "failures": [],
        "threshold_evidence": [],
        "risk_history": [],
        "gate_history": [],
    }


def _sort_component_bucket(component: dict[str, Any]) -> None:
    component["requirements"] = sorted(component["requirements"], key=lambda item: str(item.get("id") or ""))
    component["tests"] = sorted(set(component["tests"]))
    component["failures"] = sorted(component["failures"], key=lambda item: str(item.get("test_id") or item.get("id") or ""))
    component["threshold_evidence"] = sorted(
        component["threshold_evidence"],
        key=lambda item: (str(item.get("requirement_id") or ""), str(item.get("metric") or "")),
    )
    component["risk_history"] = sorted(
        component["risk_history"],
        key=lambda item: str(item.get("timestamp_utc") or ""),
        reverse=True,
    )


def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for record in records:
        key = (
            str(record.get("record_type")),
            str(record.get("timestamp_utc")),
            str(record.get("report_path")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    else:
        values = value if isinstance(value, list | tuple | set) else [value]
    return sorted({str(item).strip() for item in values if str(item).strip()})
