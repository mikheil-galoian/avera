"""JSON report generation for AVERA."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def write_json_report(assessment: Any, path: str | Path) -> Path:
    """Write an AVERA assessment as deterministic, readable JSON."""

    output_path = Path(path)
    payload = json.dumps(assessment_to_dict(assessment), indent=2, sort_keys=True) + "\n"
    _atomic_write_text(output_path, payload)
    return output_path


def assessment_to_dict(assessment: Any) -> dict[str, Any]:
    """Convert a risk assessment or compatible object into JSON-safe data."""

    data = _to_jsonable(assessment)
    return data if isinstance(data, dict) else {"assessment": data}


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_to_jsonable(item) for item in value]
    if hasattr(value, "__dict__"):
        return _to_jsonable(vars(value))
    return value


def _atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(path)
