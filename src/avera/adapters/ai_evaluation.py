"""AI model evaluation adapter for AVERA.

Converts AI model evaluation results (scenario-based metrics) into
the standard AVERA verification_results format consumed by the kernel.

This adapter enables AVERA to analyze AI model changes — regressions,
improvements, and safety-critical failures — using the same pipeline
used for traditional software verification.

No kernel modifications required. Pure data translation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_ai_evaluation(path: Path) -> dict[str, Any]:
    """Load AI evaluation JSON and return AVERA-compatible verification_results.

    The AI evaluation format uses 'scenarios' with metric-based pass/fail.
    This adapter maps each scenario to a standard AVERA test entry.

    Args:
        path: Path to the AI evaluation JSON file.

    Returns:
        A dict in AVERA verification_results format with 'runId', 'stage',
        and 'tests' keys.

    Raises:
        FileNotFoundError: If the evaluation file does not exist.
        ValueError: If the evaluation file is missing required fields.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"AI evaluation file not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    _validate_ai_evaluation(data, path)

    tests = []
    for scenario in data.get("tests", []):
        test_entry = {
            "testId": scenario.get("testId", scenario.get("id", "")),
            "name": scenario.get("name", ""),
            "passed": bool(scenario.get("passed", False)),
            "component": scenario.get("component", ""),
            "requirement": scenario.get("requirement", ""),
            "stage": scenario.get("stage", data.get("stage", "sil")),
        }
        # Preserve metric evidence for threshold comparison downstream
        for field in ("metric", "value", "threshold", "operator"):
            if field in scenario:
                test_entry[field] = scenario[field]
        tests.append(test_entry)

    return {
        "runId": data.get("runId", ""),
        "stage": data.get("stage", "sil"),
        "modelVersion": data.get("modelVersion", ""),
        "tests": tests,
    }


def model_card_to_metadata(path: Path) -> dict[str, Any]:
    """Load an AI model card and return metadata for the AVERA report.

    Args:
        path: Path to model_card JSON file.

    Returns:
        Dict of model metadata fields suitable for embedding in a report.
        Returns empty dict if file does not exist.
    """
    path = Path(path)
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    return {
        "model_id": data.get("model_id", ""),
        "model_version": data.get("version", ""),
        "model_hash": data.get("model_hash", ""),
        "architecture": data.get("architecture", ""),
        "training_data_version": data.get("training_data_version", ""),
        "target_hardware": data.get("target_hardware", ""),
        "quantization": data.get("quantization", ""),
        "certification_status": data.get("certification_status", ""),
        "changes_from_baseline": data.get("changes_from_baseline", []),
    }


def _validate_ai_evaluation(data: dict, path: Path) -> None:
    """Validate required fields in an AI evaluation artifact."""
    required = ("runId", "stage", "tests")
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(
            f"AI evaluation file {path} is missing required fields: {missing}"
        )
    if not isinstance(data["tests"], list):
        raise ValueError(
            f"AI evaluation file {path}: 'tests' must be a list of scenarios"
        )
