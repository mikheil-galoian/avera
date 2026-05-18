"""Validate local AVERA evidence workspaces."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_FILES = (
    "requirements.csv",
    "component_map.json",
    "baseline_results.json",
    "current_results.json",
    "change_description.txt",
)

REQUIRED_REQUIREMENT_FIELDS = (
    "id",
    "component",
    "requirement",
    "metric",
    "operator",
    "threshold",
)


@dataclass(frozen=True)
class ValidationResult:
    path: str
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_files: tuple[str, ...] = REQUIRED_FILES


def validate_workspace(path: str | Path) -> ValidationResult:
    """Validate the minimal AVERA workspace contract."""

    workspace = Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    if not workspace.exists():
        return ValidationResult(
            path=str(workspace),
            ok=False,
            errors=[f"Workspace does not exist: {workspace}"],
            warnings=[],
        )

    if not workspace.is_dir():
        return ValidationResult(
            path=str(workspace),
            ok=False,
            errors=[f"Workspace is not a directory: {workspace}"],
            warnings=[],
        )

    for name in REQUIRED_FILES:
        if not (workspace / name).is_file():
            errors.append(f"Missing required file: {name}")

    if not errors:
        _validate_requirements(workspace / "requirements.csv", errors)
        _validate_json_object(workspace / "component_map.json", "component_map.json", errors)
        _validate_verification(workspace / "baseline_results.json", "baseline_results.json", errors)
        _validate_verification(workspace / "current_results.json", "current_results.json", errors)
        if not (workspace / "change_description.txt").read_text(encoding="utf-8").strip():
            warnings.append("change_description.txt is empty")

    return ValidationResult(
        path=str(workspace),
        ok=not errors,
        errors=errors,
        warnings=warnings,
    )


def _validate_requirements(path: Path, errors: list[str]) -> None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = [field for field in REQUIRED_REQUIREMENT_FIELDS if field not in fields]
            if missing:
                errors.append(f"requirements.csv missing columns: {', '.join(missing)}")
                return
            if not any(True for _ in reader):
                errors.append("requirements.csv has no requirement rows")
    except OSError as exc:
        errors.append(f"Could not read requirements.csv: {exc}")


def _validate_json_object(path: Path, label: str, errors: list[str]) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return None
    except OSError as exc:
        errors.append(f"Could not read {label}: {exc}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{label} must be a JSON object")
        return None
    return data


def _validate_verification(path: Path, label: str, errors: list[str]) -> None:
    data = _validate_json_object(path, label, errors)
    if data is None:
        return
    for field_name in ("runId", "stage", "tests"):
        if field_name not in data:
            errors.append(f"{label} missing field: {field_name}")
    tests = data.get("tests")
    if "tests" in data and not isinstance(tests, list):
        errors.append(f"{label} field tests must be an array")
    elif isinstance(tests, list) and not tests:
        errors.append(f"{label} tests array is empty")
