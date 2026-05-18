"""Artifact loaders for AVERA evidence inputs."""

from avera.ingestion.component_map import load_component_map
from avera.ingestion.requirements import load_requirements
from avera.ingestion.verification_results import load_verification_results

__all__ = [
    "load_component_map",
    "load_requirements",
    "load_verification_results",
]
