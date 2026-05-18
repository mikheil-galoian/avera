"""Shared ingestion helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PathLike = str | Path


def read_json_object(path: PathLike) -> dict[str, Any]:
    artifact = Path(path)
    try:
        with artifact.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {artifact}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {artifact}")
    return data


def require_text(record: dict[str, Any], field: str, source: str) -> str:
    value = record.get(field)
    if value is None or str(value).strip() == "":
        raise ValueError(f"Missing required field '{field}' in {source}")
    return str(value).strip()


def tuple_of_text(value: Any) -> tuple[str, ...]:
    if value is None or value == "":
        return ()
    if isinstance(value, str):
        separators = (";", "|")
        values = [value]
        for separator in separators:
            if separator in value:
                values = value.split(separator)
                break
        return tuple(item.strip() for item in values if item.strip())
    if isinstance(value, list | tuple):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return (str(value).strip(),)
