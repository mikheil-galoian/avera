"""Simple query helpers over AVERA traceability indexes and packs."""

from __future__ import annotations

from typing import Any


def query_component(traceability: dict[str, Any], name: str) -> dict[str, Any] | None:
    return _find(traceability.get("components"), "component", name)


def query_requirement(traceability: dict[str, Any], requirement_id: str) -> dict[str, Any] | None:
    return _find(traceability.get("requirements"), "requirement", requirement_id)


def query_test(traceability: dict[str, Any], test_id: str) -> dict[str, Any] | None:
    return _find(traceability.get("tests"), "test", test_id)


def query_risk(traceability: dict[str, Any], risk: str) -> dict[str, Any] | None:
    return _find(traceability.get("risks"), "risk", risk)


def query_gate_status(traceability: dict[str, Any], status: str) -> dict[str, Any] | None:
    return _find(traceability.get("gates"), "gate_status", status)


def _find(items: Any, key: str, wanted: str) -> dict[str, Any] | None:
    for item in items or []:
        if isinstance(item, dict) and str(item.get(key) or "") == wanted:
            return item
    return None
