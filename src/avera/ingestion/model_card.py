"""Load AI model card artifacts for AVERA reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_model_card(path: str | Path) -> dict[str, Any]:
    """Load an AI model card JSON and return metadata for embedding in a report.

    The model card describes the AI model being changed: version, hash,
    architecture, certification status, and change history.

    Args:
        path: Path to a model_card_*.json artifact.

    Returns:
        Dict of model metadata fields. Returns empty dict if file does not exist.
    """
    artifact = Path(path)
    if not artifact.exists():
        return {}

    with artifact.open(encoding="utf-8") as f:
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
