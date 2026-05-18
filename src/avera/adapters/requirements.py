"""Adapt richer requirements exports into the stable AVERA requirements CSV shape."""

from __future__ import annotations

import csv
from pathlib import Path


REQUIRED_TARGET_FIELDS = ("id", "component", "requirement", "metric", "operator", "threshold")
FIELD_ALIASES = {
    "id": ("id", "requirement_id"),
    "component": ("component", "module"),
    "requirement": ("requirement", "title"),
    "metric": ("metric", "threshold_signal"),
    "operator": ("operator", "threshold_operator"),
    "threshold": ("threshold", "threshold_value"),
    "safety_level": ("safety_level", "safety_relevance"),
    "next_checks": ("next_checks", "next_check"),
}


def adapt_requirements_csv(path: str | Path) -> list[dict[str, str]]:
    """Convert a richer requirements export into normalized AVERA requirement rows."""

    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        if not fieldnames:
            raise ValueError(f"Requirements export has no header: {source}")

        rows = list(reader)

    normalized = [_normalize_row(row, source, index + 2) for index, row in enumerate(rows)]
    if not normalized:
        raise ValueError(f"Requirements export has no rows: {source}")
    return normalized


def write_adapted_requirements(path: str | Path, rows: list[dict[str, str]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    extra_fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in REQUIRED_TARGET_FIELDS and key not in ("safety_level", "next_checks") and key not in extra_fields:
                extra_fields.append(key)

    fieldnames = list(REQUIRED_TARGET_FIELDS) + ["safety_level", "next_checks"] + extra_fields
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _normalize_row(row: dict[str, str], source: Path, row_number: int) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for target, aliases in FIELD_ALIASES.items():
        value = _first_value(row, aliases)
        if target in REQUIRED_TARGET_FIELDS and not value:
            raise ValueError(
                f"Requirements export missing value for {target} at {source}:{row_number}"
            )
        normalized[target] = value

    mapped_keys = {alias for aliases in FIELD_ALIASES.values() for alias in aliases}
    for key, value in row.items():
        if key in mapped_keys or value in (None, ""):
            continue
        normalized[key] = str(value).strip()
    return normalized


def _first_value(row: dict[str, str], aliases: tuple[str, ...]) -> str:
    for key in aliases:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


# ---------------------------------------------------------------------------
# SDK-compatible class wrapper
# ---------------------------------------------------------------------------

from avera.adapters.interface import RequirementsAdapter as _RA
class RequirementsCsvAdapter(_RA):
    """RequirementsAdapter wrapper for :func:`adapt_requirements_csv`."""

    name = "requirements_csv"
    version = "1.0.0"
    source_format = "requirements_csv"
    file_extensions = (".csv",)

    def adapt_requirements(self, path: Path) -> list:
        return adapt_requirements_csv(path)

    def can_handle(self, path: Path) -> bool:
        if path.suffix.lower() != ".csv":
            return False
        try:
            header = path.read_text(encoding="utf-8-sig", errors="replace").split("\n")[0]
            return ("requirement_id" in header or "id" in header) and "threshold" in header
        except OSError:
            return False

    @property
    def metadata(self) -> dict:
        return {"adapter": "requirements_csv.1_0_0", "adapter_name": "requirements_csv",
                "adapter_version": "1.0.0", "source_format": "requirements_csv"}

    def __repr__(self) -> str:
        return "RequirementsCsvAdapter(name='requirements_csv', version='1.0.0')"
