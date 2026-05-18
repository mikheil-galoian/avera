"""Build deterministic traceability indexes from AVERA evidence."""

from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "avera.traceability_index.v0.1"


def build_traceability_index(
    report: dict[str, Any],
    memory_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a stable public traceability index from report and memory records."""

    memory_records = list(memory_records or [])

    component_map: dict[str, dict[str, Any]] = {}
    requirement_map: dict[str, dict[str, Any]] = {}
    test_map: dict[str, dict[str, Any]] = {}
    risk_map: dict[str, dict[str, Any]] = {}
    gate_map: dict[str, dict[str, Any]] = {}

    current_components = _string_list(report.get("affected_components") or report.get("affected_component"))
    current_requirements = _normalize_requirements(report.get("affected_requirements") or [])
    current_failures = _normalize_failures(report)
    current_thresholds = _normalize_thresholds(report.get("threshold_evidence") or [])

    for component_name in current_components:
        _component_entry(component_map, component_name)

    for requirement in current_requirements:
        req_id = requirement["id"]
        component_name = requirement["component"]
        _component_entry(component_map, component_name)["requirements"].add(req_id)
        _requirement_entry(requirement_map, req_id, requirement)["components"].add(component_name)

    for failure in current_failures:
        test_id = failure["test_id"]
        component_name = failure["component"]
        requirement_id = failure["requirement_id"]

        component = _component_entry(component_map, component_name)
        component["tests"].add(test_id)
        component["failures"].append(failure)

        test = _test_entry(test_map, test_id)
        test["components"].add(component_name)
        if requirement_id:
            test["requirements"].add(requirement_id)
            _requirement_entry(requirement_map, requirement_id)["tests"].add(test_id)

    for threshold in current_thresholds:
        requirement_id = threshold.get("requirement_id")
        component_name = _component_for_requirement(requirement_id, requirement_map)
        component = _component_entry(component_map, component_name)
        component["threshold_evidence"].append(threshold)

        test_id = str(threshold.get("test_id") or "").strip()
        if test_id:
            component["tests"].add(test_id)
            test = _test_entry(test_map, test_id)
            test["components"].add(component_name)
            if requirement_id:
                test["requirements"].add(str(requirement_id))
                _requirement_entry(requirement_map, str(requirement_id))["tests"].add(test_id)

    current_risk = str(report.get("risk") or "unknown")
    _risk_entry(
        risk_map,
        current_risk,
        {
            "timestamp_utc": None,
            "verdict": report.get("verdict"),
            "confidence": report.get("confidence"),
            "confidence_score": report.get("confidence_score"),
            "report_path": None,
            "record_type": "current_report",
        },
    )

    for record in memory_records:
        _ingest_memory_record(
            record,
            component_map=component_map,
            requirement_map=requirement_map,
            test_map=test_map,
            risk_map=risk_map,
            gate_map=gate_map,
        )

    components = _finalize_components(component_map, risk_map, gate_map)
    requirements = _finalize_requirements(requirement_map)
    tests = _finalize_tests(test_map)
    risks = _finalize_risks(risk_map)
    gates = _finalize_gates(gate_map)

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "verdict": report.get("verdict"),
            "risk": report.get("risk"),
            "confidence": report.get("confidence"),
            "confidence_score": report.get("confidence_score"),
            "component_count": len(components),
            "requirement_count": len(requirements),
            "test_count": len(tests),
            "failure_count": sum(len(item["failures"]) for item in components),
            "memory_analysis_records": sum(1 for item in memory_records if item.get("record_type") == "analysis"),
            "memory_gate_records": sum(1 for item in memory_records if item.get("record_type") == "gate"),
        },
        "components": components,
        "requirements": requirements,
        "tests": tests,
        "risks": risks,
        "gates": gates,
    }


def _ingest_memory_record(
    record: dict[str, Any],
    *,
    component_map: dict[str, dict[str, Any]],
    requirement_map: dict[str, dict[str, Any]],
    test_map: dict[str, dict[str, Any]],
    risk_map: dict[str, dict[str, Any]],
    gate_map: dict[str, dict[str, Any]],
) -> None:
    components = _string_list(record.get("affected_components"))
    requirements = _normalize_requirements(record.get("affected_requirements") or [])
    failures = _normalize_record_failures(record)
    tests_from_record = _string_list(record.get("affected_tests"))

    for component_name in components:
        _component_entry(component_map, component_name)

    for requirement in requirements:
        req_id = requirement["id"]
        component_name = requirement["component"]
        if component_name == "unknown_component" and components:
            component_name = components[0]
            requirement["component"] = component_name
        _component_entry(component_map, component_name)["requirements"].add(req_id)
        _requirement_entry(requirement_map, req_id, requirement)["components"].add(component_name)

    for failure in failures:
        test_id = failure["test_id"]
        component_name = failure["component"]
        requirement_id = failure["requirement_id"]
        component = _component_entry(component_map, component_name)
        component["tests"].add(test_id)
        component["failures"].append(failure)
        test = _test_entry(test_map, test_id)
        test["components"].add(component_name)
        if requirement_id:
            test["requirements"].add(requirement_id)
            _requirement_entry(requirement_map, requirement_id)["tests"].add(test_id)

    for test_id in tests_from_record:
        test = _test_entry(test_map, test_id)
        for component_name in components:
            _component_entry(component_map, component_name)["tests"].add(test_id)
            test["components"].add(component_name)
        for requirement in requirements:
            req_id = requirement["id"]
            test["requirements"].add(req_id)
            _requirement_entry(requirement_map, req_id)["tests"].add(test_id)

    risk = str(record.get("risk") or "unknown")
    _risk_entry(
        risk_map,
        risk,
        {
            "timestamp_utc": record.get("timestamp_utc"),
            "verdict": record.get("verdict"),
            "confidence": record.get("confidence"),
            "confidence_score": record.get("confidence_score"),
            "report_path": record.get("report_path"),
            "record_type": record.get("record_type"),
        },
    )

    if record.get("record_type") == "gate":
        gate_status = str(record.get("gate_status") or "unknown")
        entry = gate_map.setdefault(
            gate_status,
            {
                "gate_status": gate_status,
                "status": gate_status,
                "gate_exit_codes": set(),
                "records": [],
            },
        )
        if record.get("gate_exit_code") is not None:
            entry["gate_exit_codes"].add(int(record["gate_exit_code"]))
        entry["records"].append(
            {
                "timestamp_utc": record.get("timestamp_utc"),
                "verdict": record.get("verdict"),
                "risk": record.get("risk"),
                "report_path": record.get("report_path"),
                "reasons": _string_list(record.get("reasons")),
            }
        )


def _component_entry(component_map: dict[str, dict[str, Any]], component_name: str) -> dict[str, Any]:
    return component_map.setdefault(
        component_name,
        {
            "component": component_name,
            "requirements": set(),
            "tests": set(),
            "failures": [],
            "threshold_evidence": [],
            "risk_history": [],
            "gate_history": [],
        },
    )


def _requirement_entry(
    requirement_map: dict[str, dict[str, Any]],
    requirement_id: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = requirement_map.setdefault(
        requirement_id,
        {
            "requirement": requirement_id,
            "components": set(),
            "tests": set(),
        },
    )
    if seed:
        if seed.get("component"):
            entry["components"].add(str(seed["component"]))
        for key in ("metric", "safety_level", "requirement"):
            if key in seed and seed.get(key) is not None:
                entry[key] = seed.get(key)
    return entry


def _test_entry(test_map: dict[str, dict[str, Any]], test_id: str) -> dict[str, Any]:
    return test_map.setdefault(
        test_id,
        {
            "test": test_id,
            "components": set(),
            "requirements": set(),
        },
    )


def _risk_entry(risk_map: dict[str, dict[str, Any]], risk: str, record: dict[str, Any]) -> None:
    entry = risk_map.setdefault(risk, {"risk": risk, "records": []})
    entry["records"].append(record)


def _component_for_requirement(
    requirement_id: Any,
    requirement_map: dict[str, dict[str, Any]],
) -> str:
    wanted = str(requirement_id or "").strip()
    if not wanted:
        return "unknown_component"
    requirement = requirement_map.get(wanted)
    if not requirement:
        return "unknown_component"
    components = sorted(requirement["components"])
    return components[0] if components else "unknown_component"


def _normalize_requirements(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in value or []:
        if isinstance(item, dict):
            req_id = str(item.get("id") or "").strip()
            if not req_id:
                continue
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
            text = str(item).strip()
            if text:
                records.append({"id": text, "component": "unknown_component"})
    return records


def _normalize_failures(report: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for category in ("introduced_failures", "preexisting_failures"):
        for item in report.get(category) or []:
            failure = _failure_record(item, category)
            if failure:
                failures.append(failure)
    return failures


def _normalize_record_failures(record: dict[str, Any]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for category in ("introduced_failures", "preexisting_failures"):
        for item in record.get(category) or []:
            failure = _failure_record(item, category)
            if failure:
                failures.append(failure)
    return failures


def _failure_record(item: Any, category: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        test_id = str(item).strip()
        return {"test_id": test_id, "component": "unknown_component", "requirement_id": None, "category": category} if test_id else None
    test_id = str(item.get("test_id") or item.get("id") or "").strip()
    if not test_id:
        return None
    requirement_id = item.get("requirement_id")
    return {
        **dict(item),
        "test_id": test_id,
        "component": str(item.get("component") or "unknown_component"),
        "requirement_id": str(requirement_id).strip() if requirement_id else None,
        "category": category,
    }


def _normalize_thresholds(value: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)]


def _finalize_components(
    component_map: dict[str, dict[str, Any]],
    risk_map: dict[str, dict[str, Any]],
    gate_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    risks = _finalize_risks(risk_map)
    gates = _finalize_gates(gate_map)
    items: list[dict[str, Any]] = []
    for name in sorted(component_map):
        item = component_map[name]
        items.append(
            {
                "component": name,
                "requirements": sorted(item["requirements"]),
                "tests": sorted(item["tests"]),
                "failures": sorted(item["failures"], key=lambda row: row["test_id"]),
                "threshold_evidence": sorted(
                    item["threshold_evidence"],
                    key=lambda row: (str(row.get("requirement_id") or ""), str(row.get("metric") or "")),
                ),
                "risk_history": risks,
                "gate_history": gates,
            }
        )
    return items


def _finalize_requirements(requirement_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for req_id in sorted(requirement_map):
        item = requirement_map[req_id]
        result = {
            "requirement": req_id,
            "components": sorted(item["components"]),
            "tests": sorted(item["tests"]),
        }
        for key in ("metric", "safety_level", "requirement"):
            if key in item and item.get(key) is not None:
                result[key] = item[key]
        items.append(result)
    return items


def _finalize_tests(test_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for test_id in sorted(test_map):
        item = test_map[test_id]
        items.append(
            {
                "test": test_id,
                "components": sorted(item["components"]),
                "requirements": sorted(item["requirements"]),
            }
        )
    return items


def _finalize_risks(risk_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for risk in sorted(risk_map):
        entry = risk_map[risk]
        items.append(
            {
                "risk": risk,
                "records": sorted(
                    entry["records"],
                    key=lambda row: str(row.get("timestamp_utc") or ""),
                    reverse=True,
                ),
            }
        )
    return items


def _finalize_gates(gate_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for status in sorted(gate_map):
        entry = gate_map[status]
        items.append(
            {
                "gate_status": status,
                "status": status,
                "gate_exit_codes": sorted(entry["gate_exit_codes"]),
                "records": sorted(
                    entry["records"],
                    key=lambda row: str(row.get("timestamp_utc") or ""),
                    reverse=True,
                ),
            }
        )
    return items


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
