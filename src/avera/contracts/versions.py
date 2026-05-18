"""AVERA artifact schema version registry.

This module is the single source of truth for all artifact schema versions.
It provides backward-compatibility guarantees and deprecation tracking.

Rules:
- Schema versions are immutable once published to PyPI.
- A schema version may be deprecated but never removed for a minimum of 90 days.
- Breaking changes require a new schema_version string.
- Additive changes (new optional fields) are backward-compatible within the same version.

Usage::

    from avera.contracts.versions import CURRENT_VERSIONS, is_supported_version

    # Get the current version for a named artifact
    version = CURRENT_VERSIONS["report"]  # "1.0"

    # Check whether a version string appearing in an artifact is still supported
    ok = is_supported_version("report", "1.0")   # True
    ok = is_supported_version("report", "0.9")   # False — too old
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


# ---------------------------------------------------------------------------
# Current schema versions — bump here when a breaking change is introduced.
# ---------------------------------------------------------------------------

CURRENT_VERSIONS: Final[dict[str, str]] = {
    "report": "1.0",
    "graph": "evidence_graph.0.3",
    "decision": "1.0",
    "trend": "1.0",
    "workspace_pack": "1.0",
    "traceability": "1.0",
    "memory_record": "1.0",
    "model_card": "1.0",
    "ai_evaluation": "1.0",
}


# ---------------------------------------------------------------------------
# Supported version ranges — any version string in this set is still valid.
# Versions removed from here are no longer accepted by the validation layer.
# ---------------------------------------------------------------------------

SUPPORTED_VERSIONS: Final[dict[str, frozenset[str]]] = {
    "report": frozenset({"1.0"}),
    "graph": frozenset({"evidence_graph.0.3", "evidence_graph.0.2", "evidence_graph.0.1"}),
    "decision": frozenset({"1.0"}),
    "trend": frozenset({"1.0"}),
    "workspace_pack": frozenset({"1.0"}),
    "traceability": frozenset({"1.0"}),
    "memory_record": frozenset({"1.0"}),
    "model_card": frozenset({"1.0"}),
    "ai_evaluation": frozenset({"1.0"}),
}


# ---------------------------------------------------------------------------
# Deprecated versions — still accepted but emit a warning.
# Key: (artifact_name, schema_version)
# Value: message explaining the deprecation and migration path.
# ---------------------------------------------------------------------------

DEPRECATED_VERSIONS: Final[dict[tuple[str, str], str]] = {
    ("graph", "evidence_graph.0.1"): (
        "evidence_graph.0.1 is deprecated. "
        "Migrate to evidence_graph.0.3: add 'rules', 'confidence_factors', 'risk_drivers' nodes."
    ),
    ("graph", "evidence_graph.0.2"): (
        "evidence_graph.0.2 is deprecated. "
        "Migrate to evidence_graph.0.3: add 'signal_summary' node type."
    ),
}


# ---------------------------------------------------------------------------
# Version info dataclass — returned by get_version_info()
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VersionInfo:
    artifact_name: str
    schema_version: str
    is_current: bool
    is_supported: bool
    is_deprecated: bool
    deprecation_message: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_current_version(artifact_name: str) -> str:
    """Return the current schema version string for the named artifact.

    Args:
        artifact_name: One of the keys in CURRENT_VERSIONS.

    Returns:
        The current schema version string.

    Raises:
        KeyError: If the artifact name is not registered.
    """
    return CURRENT_VERSIONS[artifact_name]


def is_supported_version(artifact_name: str, schema_version: str) -> bool:
    """Return True if the schema_version is still accepted for this artifact.

    Args:
        artifact_name: One of the keys in SUPPORTED_VERSIONS.
        schema_version: The version string found in an artifact.

    Returns:
        True if the version is supported (including deprecated), False otherwise.
    """
    supported = SUPPORTED_VERSIONS.get(artifact_name, frozenset())
    return schema_version in supported


def is_deprecated_version(artifact_name: str, schema_version: str) -> bool:
    """Return True if the version is deprecated (still valid, but flagged).

    Args:
        artifact_name: Artifact type name.
        schema_version: The version string found in an artifact.

    Returns:
        True if the version is in the deprecation registry.
    """
    return (artifact_name, schema_version) in DEPRECATED_VERSIONS


def get_deprecation_message(artifact_name: str, schema_version: str) -> str:
    """Return the deprecation message for an artifact version, or empty string.

    Args:
        artifact_name: Artifact type name.
        schema_version: The version string found in an artifact.

    Returns:
        Deprecation message string, or "" if not deprecated.
    """
    return DEPRECATED_VERSIONS.get((artifact_name, schema_version), "")


def get_version_info(artifact_name: str, schema_version: str) -> VersionInfo:
    """Return a complete VersionInfo for an artifact + version combination.

    Args:
        artifact_name: Artifact type name.
        schema_version: The version string found in an artifact.

    Returns:
        VersionInfo with all compatibility flags populated.
    """
    current = CURRENT_VERSIONS.get(artifact_name, "")
    supported = is_supported_version(artifact_name, schema_version)
    deprecated = is_deprecated_version(artifact_name, schema_version)
    dep_message = get_deprecation_message(artifact_name, schema_version)

    return VersionInfo(
        artifact_name=artifact_name,
        schema_version=schema_version,
        is_current=(schema_version == current),
        is_supported=supported,
        is_deprecated=deprecated,
        deprecation_message=dep_message,
    )


def list_artifacts() -> list[str]:
    """Return the list of all registered artifact names."""
    return sorted(CURRENT_VERSIONS.keys())
