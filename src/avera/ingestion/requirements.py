"""Load requirements from requirements.csv."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from avera.ingestion._helpers import PathLike, require_text, tuple_of_text
from avera.models.requirements import Requirement


REQUIRED_FIELDS = ("id", "component", "requirement", "metric", "operator", "threshold")
KNOWN_FIELDS = REQUIRED_FIELDS + ("safety_level", "next_checks")


def load_requirements(path: PathLike) -> list[Requirement]:
    """Load a requirements CSV into normalized Requirement models."""

    artifact = Path(path)
    with artifact.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"Requirements CSV has no header: {artifact}")

        missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
        if missing:
            raise ValueError(f"Requirements CSV missing fields {missing}: {artifact}")

        requirements: list[Requirement] = []
        for row_number, row in enumerate(reader, start=2):
            source = f"{artifact}:{row_number}"
            requirements.append(_requirement_from_row(row, source))

    return requirements


def _requirement_from_row(row: dict[str, Any], source: str) -> Requirement:
    threshold_text = require_text(row, "threshold", source)
    try:
        threshold: float | str = float(threshold_text)
    except ValueError:
        threshold = threshold_text

    metadata = {
        key: value
        for key, value in row.items()
        if key not in KNOWN_FIELDS and value not in (None, "")
    }

    return Requirement(
        id=require_text(row, "id", source),
        component=require_text(row, "component", source),
        requirement=require_text(row, "requirement", source),
        metric=require_text(row, "metric", source),
        operator=require_text(row, "operator", source),
        threshold=threshold,
        safety_level=str(row.get("safety_level") or "").strip(),
        next_checks=tuple_of_text(row.get("next_checks")),
        metadata=metadata,
    )
