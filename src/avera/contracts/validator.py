"""Validate stable AVERA artifact contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from avera.validation import validate_report


ARTIFACT_REQUIRED_FIELDS = {
    "graph": ("schema_version", "nodes", "edges", "summary"),
    "decision": (
        "schema_version",
        "action",
        "status",
        "category",
        "priority",
        "owner",
        "verdict",
        "risk",
        "confidence",
        "confidence_score",
        "rationale",
    ),
    "trend": (
        "schema_version",
        "summary",
        "verdict_history",
        "risk_history",
        "components",
        "requirements",
        "tests",
        "test_stability_buckets",
    ),
    "workspace_pack": (
        "schema_version",
        "workspace",
        "summary",
        "artifacts",
        "report",
        "graph",
        "memory_slice",
        "traceability",
        "decision",
        "trend",
        "manifest",
    ),
    "evidence_manifest": (
        "schema_version",
        "workspace",
        "generated_at_utc",
        "artifacts",
        "integrity_root",
        "completeness",
        "summary",
        "provenance",
    ),
}


@dataclass(frozen=True)
class ArtifactValidationResult:
    ok: bool
    artifact_name: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_fields: tuple[str, ...] = ()


def validate_artifact(name: str, payload: dict[str, Any]) -> ArtifactValidationResult:
    """Validate one stable AVERA artifact by name."""

    artifact_name = str(name).strip().lower()
    if artifact_name == "report":
        result = validate_report(payload)
        return ArtifactValidationResult(
            ok=result.ok,
            artifact_name="report",
            errors=list(result.errors),
            warnings=list(result.warnings),
            required_fields=result.required_fields,
        )

    required_fields = ARTIFACT_REQUIRED_FIELDS.get(artifact_name)
    if required_fields is None:
        return ArtifactValidationResult(
            ok=False,
            artifact_name=artifact_name,
            errors=[f"Unknown artifact contract: {artifact_name}"],
            warnings=[],
            required_fields=(),
        )

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return ArtifactValidationResult(
            ok=False,
            artifact_name=artifact_name,
            errors=["Artifact must be a JSON object"],
            warnings=[],
            required_fields=required_fields,
        )

    for field_name in required_fields:
        if field_name not in payload:
            errors.append(f"Missing required {artifact_name} field: {field_name}")

    schema_version = payload.get("schema_version")
    if schema_version is not None and not _uses_known_schema_namespace(str(schema_version)):
        warnings.append("schema_version does not use the avera.* namespace")

    if artifact_name == "graph":
        if "nodes" in payload and not isinstance(payload["nodes"], list):
            errors.append("Graph field nodes must be an array")
        if "edges" in payload and not isinstance(payload["edges"], list):
            errors.append("Graph field edges must be an array")
        if "summary" in payload and not isinstance(payload["summary"], dict):
            errors.append("Graph field summary must be an object")
    elif artifact_name == "decision":
        _expect_type(errors, payload, "action", str, "Decision field action must be a string")
        _expect_type(errors, payload, "status", str, "Decision field status must be a string")
        _expect_type(errors, payload, "rationale", list, "Decision field rationale must be an array")
    elif artifact_name == "trend":
        for field_name in (
            "verdict_history",
            "risk_history",
            "components",
            "requirements",
            "tests",
        ):
            _expect_type(errors, payload, field_name, list, f"Trend field {field_name} must be an array")
        if "summary" in payload and not isinstance(payload["summary"], dict):
            errors.append("Trend field summary must be an object")
        if "test_stability_buckets" in payload and not isinstance(payload["test_stability_buckets"], dict):
            errors.append("Trend field test_stability_buckets must be an object")
    elif artifact_name == "workspace_pack":
        for field_name in ("workspace", "summary", "artifacts", "report", "graph", "traceability", "decision", "trend", "manifest"):
            _expect_type(errors, payload, field_name, dict, f"Workspace pack field {field_name} must be an object")
        _expect_type(errors, payload, "memory_slice", list, "Workspace pack field memory_slice must be an array")
    elif artifact_name == "evidence_manifest":
        for field_name in ("workspace", "completeness", "summary", "provenance"):
            _expect_type(errors, payload, field_name, dict, f"Evidence manifest field {field_name} must be an object")
        _expect_type(errors, payload, "artifacts", list, "Evidence manifest field artifacts must be an array")
        _expect_type(errors, payload, "integrity_root", str, "Evidence manifest field integrity_root must be a string")
        _expect_type(errors, payload, "generated_at_utc", str, "Evidence manifest field generated_at_utc must be a string")

    return ArtifactValidationResult(
        ok=not errors,
        artifact_name=artifact_name,
        errors=errors,
        warnings=warnings,
        required_fields=required_fields,
    )


def validate_bundle(pack: dict[str, Any]) -> ArtifactValidationResult:
    """Validate a workspace pack and its embedded artifact summaries."""

    result = validate_artifact("workspace_pack", pack)
    errors = list(result.errors)
    warnings = list(result.warnings)

    if result.ok:
        _validate_pack_summary(errors, pack, "report", ("schema_version", "json_path", "verdict", "risk"))
        _validate_pack_summary(errors, pack, "graph", ("schema_version", "path", "summary"))
        _validate_pack_summary(errors, pack, "traceability", ("schema_version", "path", "summary"))
        _validate_pack_summary(errors, pack, "decision", ("schema_version", "path", "action", "category", "owner"))
        _validate_pack_summary(errors, pack, "trend", ("schema_version", "path", "summary"))

    return ArtifactValidationResult(
        ok=not errors,
        artifact_name="workspace_pack_bundle",
        errors=errors,
        warnings=warnings,
        required_fields=result.required_fields,
    )


def _expect_type(
    errors: list[str],
    payload: dict[str, Any],
    field_name: str,
    expected_type: type,
    message: str,
) -> None:
    if field_name in payload and not isinstance(payload[field_name], expected_type):
        errors.append(message)


def _validate_pack_summary(
    errors: list[str],
    pack: dict[str, Any],
    field_name: str,
    required_fields: tuple[str, ...],
) -> None:
    payload = pack.get(field_name)
    if not isinstance(payload, dict):
        errors.append(f"Workspace pack field {field_name} must be an object")
        return
    for nested_field in required_fields:
        if nested_field not in payload:
            errors.append(f"{field_name}: Missing required summary field: {nested_field}")


def _uses_known_schema_namespace(schema_version: str) -> bool:
    return schema_version.startswith("avera.") or schema_version.startswith("evidence_graph.")
