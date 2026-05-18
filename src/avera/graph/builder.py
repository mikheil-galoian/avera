"""Build an evidence graph from an AVERA risk assessment.

The graph is intentionally plain Python data so it can be serialized, tested,
and consumed by reports or future visualization layers without new runtime
dependencies.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


SCHEMA_VERSION = "evidence_graph.v0.3"


def build_evidence_graph(
    assessment: Any,
    change_description: str | None = None,
) -> dict[str, Any]:
    """Return an evidence graph for a risk assessment or compatible dict."""

    data = _to_dict(assessment)

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    seen_nodes: set[str] = set()
    seen_edges: set[tuple[str, str, str]] = set()

    def add_node(node: dict[str, Any]) -> str:
        node_id = node["id"]
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append(node)
        return node_id

    def add_edge(source: str, target: str, relation: str) -> None:
        key = (source, target, relation)
        if source in seen_nodes and target in seen_nodes and key not in seen_edges:
            seen_edges.add(key)
            edges.append({"source": source, "target": target, "relation": relation})

    change_id = add_node(
        _node(
            "change",
            "change",
            "Change under assessment",
            description=change_description,
        )
    )

    risk_id = add_node(
        _node(
            "risk",
            "risk",
            str(data.get("risk") or "unknown"),
            verdict=data.get("verdict"),
            confidence=data.get("confidence"),
        )
    )
    add_edge(change_id, risk_id, "classified_as")

    recommendation_ids = _add_recommendations(data, add_node)
    for recommendation_id in recommendation_ids:
        add_edge(risk_id, recommendation_id, "recommends")

    rule_ids = _add_named_items(data, add_node, "rules_triggered", "rule")
    for rule_id in rule_ids:
        add_edge(rule_id, risk_id, "supports")

    confidence_factor_ids = _add_named_items(data, add_node, "confidence_factors", "confidence_factor")
    for factor_id in confidence_factor_ids:
        add_edge(factor_id, risk_id, "informs_confidence")

    risk_driver_ids = _add_named_items(data, add_node, "risk_drivers", "risk_driver")
    for driver_id in risk_driver_ids:
        add_edge(driver_id, risk_id, "drives_risk")

    component_ids = _add_components(data, add_node)
    for component_id in component_ids.values():
        add_edge(change_id, component_id, "affects_component")
        add_edge(component_id, risk_id, "contributes_to")

    requirement_ids, requirement_components = _add_requirements(data, add_node)
    for requirement_id, requirement_node_id in requirement_ids.items():
        add_edge(requirement_node_id, risk_id, "informs")
        component = requirement_components.get(requirement_id)
        if component and component in component_ids:
            add_edge(component_ids[component], requirement_node_id, "governed_by")

    file_ids = _add_files(data, add_node)
    for file_id in file_ids.values():
        add_edge(change_id, file_id, "touches_file")
        for component_id in component_ids.values():
            add_edge(file_id, component_id, "maps_to_component")

    failure_ids = _add_failures(data, add_node)
    for failure_id, failure in failure_ids.items():
        add_edge(change_id, failure_id, "observed_in")
        add_edge(failure_id, risk_id, "supports")
        component = _get(failure, "component")
        if component and component in component_ids:
            add_edge(failure_id, component_ids[str(component)], "occurs_in")

    threshold_ids = _add_threshold_evidence(data, add_node)
    for threshold_id, evidence in threshold_ids.items():
        add_edge(threshold_id, risk_id, "supports")
        requirement_id = str(_get(evidence, "requirement_id", ""))
        if requirement_id and requirement_id in requirement_ids:
            add_edge(threshold_id, requirement_ids[requirement_id], "evaluates")
        test_id = str(_get(evidence, "test_id", ""))
        failure_node_id = _failure_node_id(test_id)
        if failure_node_id in seen_nodes:
            add_edge(failure_node_id, threshold_id, "contains_metric")

    signal_summary_ids = _add_signal_summaries(data, add_node)
    for signal_summary_id, signal_summary in signal_summary_ids.items():
        add_edge(signal_summary_id, risk_id, "supports")

        test_id = str(_get(signal_summary, "test_id", ""))
        failure_node_id = _failure_node_id(test_id)
        if test_id and failure_node_id in seen_nodes:
            add_edge(signal_summary_id, failure_node_id, "summarizes_test")

        for threshold_id, evidence in threshold_ids.items():
            if _threshold_matches_signal_summary(evidence, signal_summary):
                add_edge(signal_summary_id, threshold_id, "supports_threshold")

    summary = {
        "verdict": data.get("verdict"),
        "risk": data.get("risk"),
        "confidence": data.get("confidence"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "components": len(component_ids),
        "requirements": len(requirement_ids),
        "files": len(file_ids),
        "tests_or_failures": len(failure_ids),
        "threshold_evidence": len(threshold_ids),
        "signal_summaries": len(signal_summary_ids),
        "recommendations": len(recommendation_ids),
        "rules": len(rule_ids),
        "confidence_factors": len(confidence_factor_ids),
        "risk_drivers": len(risk_driver_ids),
        "evidence_summary": list(data.get("evidence_summary") or []),
        "comparison_summary": dict(data.get("comparison_summary") or {}),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "nodes": nodes,
        "edges": edges,
        "summary": summary,
    }


def _add_components(data: dict[str, Any], add_node: Any) -> dict[str, str]:
    component_names = _string_list(
        data.get("affected_components")
        or ([data["affected_component"]] if data.get("affected_component") else [])
    )
    return {
        name: add_node(_node(_component_node_id(name), "component", name))
        for name in component_names
    }


def _add_requirements(
    data: dict[str, Any],
    add_node: Any,
) -> tuple[dict[str, str], dict[str, str]]:
    requirements: dict[str, str] = {}
    requirement_components: dict[str, str] = {}
    for item in data.get("affected_requirements") or []:
        if isinstance(item, dict):
            requirement_id = str(item.get("id") or "").strip()
            if not requirement_id:
                continue
            component = str(item.get("component") or "").strip()
            if component:
                requirement_components[requirement_id] = component
            requirements[requirement_id] = add_node(
                _node(
                    _requirement_node_id(requirement_id),
                    "requirement",
                    requirement_id,
                    component=component,
                    requirement=item.get("requirement"),
                    metric=item.get("metric"),
                    operator=item.get("operator"),
                    threshold=item.get("threshold"),
                    safety_level=item.get("safety_level"),
                )
            )
        else:
            requirement_id = str(item).strip()
            if requirement_id:
                requirements[requirement_id] = add_node(
                    _node(_requirement_node_id(requirement_id), "requirement", requirement_id)
                )
    return requirements, requirement_components


def _add_files(data: dict[str, Any], add_node: Any) -> dict[str, str]:
    files = _string_list(data.get("affected_files") or data.get("changed_files") or [])
    return {
        path: add_node(_node(_file_node_id(path), "file", path, path=path))
        for path in files
    }


def _add_failures(data: dict[str, Any], add_node: Any) -> dict[str, Any]:
    failures: dict[str, Any] = {}
    for category in ("introduced_failures", "preexisting_failures"):
        for item in data.get(category) or []:
            test_id = str(_get(item, "test_id", _get(item, "id", "unknown-test")))
            node_id = _failure_node_id(test_id)
            failures[node_id] = item
            add_node(
                _node(
                    node_id,
                    "test_failure",
                    test_id,
                    category=category,
                    status=_get(item, "status"),
                    component=_get(item, "component"),
                    baseline_status=_get(item, "baseline_status"),
                    current_status=_get(item, "current_status"),
                )
            )
    return failures


def _add_threshold_evidence(data: dict[str, Any], add_node: Any) -> dict[str, Any]:
    evidence_by_node: dict[str, Any] = {}
    raw_evidence = data.get("threshold_evidence") or data.get("evidence") or []

    if isinstance(raw_evidence, dict):
        raw_evidence = [
            {"metric": metric, **dict(values)}
            for metric, values in raw_evidence.items()
            if isinstance(values, dict)
        ]

    for index, item in enumerate(raw_evidence):
        metric = str(_get(item, "metric", f"metric-{index}"))
        requirement_id = str(_get(item, "requirement_id", ""))
        test_id = str(_get(item, "test_id", ""))
        node_id = _threshold_node_id(requirement_id, metric, test_id, index)
        evidence_by_node[node_id] = item
        add_node(
            _node(
                node_id,
                "threshold_evidence",
                metric,
                requirement_id=requirement_id or None,
                test_id=test_id or None,
                baseline_value=_get(item, "baseline_value", _get(item, "baseline")),
                current_value=_get(item, "current_value", _get(item, "current")),
                operator=_get(item, "operator"),
                threshold=_get(item, "threshold"),
                baseline_passed=_get(item, "baseline_passed"),
                current_passed=_get(item, "current_passed"),
            )
        )
    return evidence_by_node


def _add_signal_summaries(data: dict[str, Any], add_node: Any) -> dict[str, Any]:
    summaries_by_node: dict[str, Any] = {}

    for index, item in enumerate(_normalize_signal_summaries(data.get("signal_summary") or [])):
        test_id = str(_get(item, "test_id", ""))
        signal = str(_get(item, "signal", f"signal-{index}"))
        node_id = _signal_summary_node_id(test_id, signal, index)
        summaries_by_node[node_id] = item
        add_node(
            _node(
                node_id,
                "signal_summary",
                signal,
                test_id=test_id or None,
                scenario_id=_get(item, "scenario_id"),
                signal=signal,
                unit=_get(item, "unit"),
                min=_get(item, "min"),
                max=_get(item, "max"),
                last=_get(item, "last"),
                count=_get(item, "count"),
            )
        )

    return summaries_by_node


def _normalize_signal_summaries(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list | tuple):
        return [item for item in value if item]
    if isinstance(value, dict):
        records: list[Any] = []
        for key in sorted(value):
            item = value[key]
            if isinstance(item, dict):
                record = dict(item)
                record.setdefault("signal", str(key))
                records.append(record)
            elif item:
                records.append({"signal": str(key), "last": item})
        return records
    return [value]


def _threshold_matches_signal_summary(evidence: Any, signal_summary: Any) -> bool:
    threshold_metric = str(_get(evidence, "metric", "")).strip()
    signal = str(_get(signal_summary, "signal", "")).strip()
    if not threshold_metric or not signal or threshold_metric != signal:
        return False

    threshold_test_id = str(_get(evidence, "test_id", "")).strip()
    signal_test_id = str(_get(signal_summary, "test_id", "")).strip()
    return not threshold_test_id or not signal_test_id or threshold_test_id == signal_test_id


def _add_recommendations(data: dict[str, Any], add_node: Any) -> list[str]:
    recommendations = _string_list(
        data.get("recommended_next_checks") or data.get("recommendations") or []
    )
    return [
        add_node(_node(_recommendation_node_id(item), "recommendation", item, check=item))
        for item in recommendations
    ]


def _add_named_items(
    data: dict[str, Any],
    add_node: Any,
    field_name: str,
    node_type: str,
) -> list[str]:
    values = _string_list(data.get(field_name) or [])
    return [
        add_node(_node(_named_node_id(node_type, item), node_type, item, value=item))
        for item in values
    ]


def _node(node_id: str, node_type: str, label: str, **properties: Any) -> dict[str, Any]:
    clean_properties = {
        key: _jsonable(value)
        for key, value in properties.items()
        if value not in (None, "", [], {})
    }
    node = {"id": node_id, "type": node_type, "label": label}
    if clean_properties:
        node["properties"] = clean_properties
    return node


def _to_dict(value: Any) -> dict[str, Any]:
    jsonable = _jsonable(value)
    return jsonable if isinstance(jsonable, dict) else {"assessment": jsonable}


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return _jsonable(vars(value))
    return value


def _get(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    else:
        values = list(value) if isinstance(value, list | tuple | set) else [value]
    return sorted({str(item).strip() for item in values if str(item).strip()})


def _safe_id(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace(":", "_")
    )


def _component_node_id(name: str) -> str:
    return f"component:{_safe_id(name)}"


def _requirement_node_id(requirement_id: str) -> str:
    return f"requirement:{_safe_id(requirement_id)}"


def _file_node_id(path: str) -> str:
    return f"file:{_safe_id(path)}"


def _failure_node_id(test_id: str) -> str:
    return f"test_failure:{_safe_id(test_id)}"


def _threshold_node_id(requirement_id: str, metric: str, test_id: str, index: int) -> str:
    parts = [part for part in (requirement_id, metric, test_id) if part]
    if not parts:
        parts = [str(index)]
    return f"threshold_evidence:{_safe_id(':'.join(parts))}"


def _signal_summary_node_id(test_id: str, signal: str, index: int) -> str:
    parts = [part for part in (test_id, signal) if part]
    if not parts:
        parts = [str(index)]
    return f"signal_summary:{_safe_id(':'.join(parts))}"


def _recommendation_node_id(check: str) -> str:
    return f"recommendation:{_safe_id(check)}"


def _named_node_id(node_type: str, value: str) -> str:
    return f"{node_type}:{_safe_id(value)}"
