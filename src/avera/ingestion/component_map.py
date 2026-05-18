"""Load component_map.json traceability artifacts."""

from __future__ import annotations

from typing import Any

from avera.ingestion._helpers import PathLike, read_json_object, require_text, tuple_of_text
from avera.models.component_map import ComponentMapEntry


KNOWN_FIELDS = ("component", "requirements", "tests")


def load_component_map(path: PathLike) -> dict[str, ComponentMapEntry]:
    """Load component mappings keyed by source or artifact path."""

    data = read_json_object(path)
    raw_entries = data.get("mappings", data)
    if not isinstance(raw_entries, dict):
        raise ValueError(f"Component map must be an object keyed by path: {path}")

    entries: dict[str, ComponentMapEntry] = {}
    for artifact_path, value in raw_entries.items():
        if not isinstance(value, dict):
            raise ValueError(f"Component map entry must be an object: {artifact_path}")
        entry = _entry_from_mapping(str(artifact_path), value)
        entries[entry.path] = entry

    return entries


def _entry_from_mapping(path: str, value: dict[str, Any]) -> ComponentMapEntry:
    metadata = {
        key: item
        for key, item in value.items()
        if key not in KNOWN_FIELDS and item not in (None, "")
    }

    return ComponentMapEntry(
        path=path,
        component=require_text(value, "component", path),
        requirements=tuple_of_text(value.get("requirements")),
        tests=tuple_of_text(value.get("tests")),
        metadata=metadata,
    )
