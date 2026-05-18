"""Markdown report generation for AVERA."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def write_markdown_report(assessment: Any, path: str | Path) -> Path:
    """Write a human-readable AVERA risk report."""

    output_path = Path(path)
    _atomic_write_text(output_path, render_markdown_report(assessment))
    return output_path


def render_markdown_report(assessment: Any) -> str:
    """Render an assessment to Markdown."""

    verdict = _get(assessment, "verdict", "insufficient_evidence")
    risk = _get(assessment, "risk", "unknown")
    confidence = _get(assessment, "confidence", "low")
    confidence_score = _get(assessment, "confidence_score")

    lines = [
        "# AVERA Change Impact Report",
        "",
        "## Verdict",
        "",
        f"- Verdict: `{verdict}`",
        f"- Risk: `{risk}`",
        f"- Confidence: `{confidence}`",
        *_confidence_score_line(confidence_score),
        "",
    ]

    _section(lines, "Affected Requirements", _requirements(_get(assessment, "affected_requirements", [])))
    _section(lines, "Affected Components", _simple_items(_get(assessment, "affected_components", [])))
    _section(lines, "Affected Files", _simple_items(_get(assessment, "affected_files", [])))
    _section(lines, "Introduced Failures", _failures(_get(assessment, "introduced_failures", [])))
    _section(lines, "Preexisting Failures", _failures(_get(assessment, "preexisting_failures", [])))
    _section(lines, "Threshold Evidence", _thresholds(_get(assessment, "threshold_evidence", [])))
    _section(lines, "Evidence Summary", _simple_items(_get(assessment, "evidence_summary", [])))
    _section(lines, "Rules Triggered", _simple_items(_get(assessment, "rules_triggered", [])))
    _section(lines, "Confidence Factors", _simple_items(_get(assessment, "confidence_factors", [])))
    _section(lines, "Risk Drivers", _simple_items(_get(assessment, "risk_drivers", [])))
    _section(lines, "Signal Summary", _signal_summaries(_get(assessment, "signal_summary", [])))
    _section(lines, "Recommended Next Checks", _simple_items(_get(assessment, "recommended_next_checks", [])))

    return "\n".join(lines).rstrip() + "\n"


def _section(lines: list[str], title: str, items: list[str]) -> None:
    lines.extend([f"## {title}", ""])
    if items:
        lines.extend(items)
    else:
        lines.append("- None recorded.")
    lines.append("")


def _requirements(requirements: Any) -> list[str]:
    items: list[str] = []
    for req in requirements or []:
        req_id = _get(req, "id", "unknown-requirement")
        component = _get(req, "component")
        metric = _get(req, "metric")
        safety = _get(req, "safety_level")
        text = _get(req, "requirement")
        details = ", ".join(
            part for part in [
                f"component: {component}" if component else "",
                f"metric: `{metric}`" if metric else "",
                f"safety: `{safety}`" if safety else "",
            ]
            if part
        )
        suffix = f" ({details})" if details else ""
        label = f"- `{req_id}`{suffix}"
        if text:
            label += f": {text}"
        items.append(label)
    return items


def _failures(failures: Any) -> list[str]:
    items: list[str] = []
    for failure in failures or []:
        test_id = _get(failure, "test_id", _get(failure, "id", "unknown-test"))
        baseline = _get(failure, "baseline_status")
        current = _get(failure, "current_status")
        component = _get(failure, "component")
        line = f"- `{test_id}`: baseline `{baseline}`, current `{current}`"
        if component:
            line += f", component {component}"
        items.append(line + ".")
    return items


def _thresholds(thresholds: Any) -> list[str]:
    items: list[str] = []
    for item in thresholds or []:
        req_id = _get(item, "requirement_id", "unknown-requirement")
        metric = _get(item, "metric", "unknown-metric")
        operator = _get(item, "operator", "?")
        threshold = _get(item, "threshold", "?")
        baseline = _get(item, "baseline_value")
        current = _get(item, "current_value")
        baseline_passed = _get(item, "baseline_passed")
        current_passed = _get(item, "current_passed")
        items.append(
            f"- `{req_id}` / `{metric}`: baseline `{baseline}` "
            f"({'pass' if baseline_passed else 'fail' if baseline_passed is False else 'unknown'}), "
            f"current `{current}` "
            f"({'pass' if current_passed else 'fail' if current_passed is False else 'unknown'}), "
            f"threshold `{operator} {threshold}`."
        )
    return items


def _signal_summaries(summaries: Any) -> list[str]:
    items: list[str] = []
    for item in summaries or []:
        test_id = _get(item, "test_id", "unknown-test")
        signal = _get(item, "signal", "unknown-signal")
        unit = _get(item, "unit", "")
        items.append(
            f"- `{test_id}` / `{signal}`: min `{_get(item, 'min')}`, "
            f"max `{_get(item, 'max')}`, last `{_get(item, 'last')}` {unit}, "
            f"points `{_get(item, 'count')}`."
        )
    return items


def _confidence_score_line(value: Any) -> list[str]:
    if value is None:
        return []
    try:
        return [f"- Confidence score: `{float(value):.2f}`"]
    except (TypeError, ValueError):
        return [f"- Confidence score: `{value}`"]


def _simple_items(values: Any) -> list[str]:
    return [f"- {value}" for value in values or []]


def _get(item: Any, key: str, default: Any = None) -> Any:
    if item is None:
        return default
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(path)
