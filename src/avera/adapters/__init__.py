"""Adapters for external engineering artifacts."""

from avera.adapters.canoe import CANoeAdapter, adapt_canoe_asc, adapt_canoe_xml
from avera.adapters.interface import AdapterRegistry, RequirementsAdapter, VerificationAdapter
from avera.adapters.junit import JUnitXmlAdapter, adapt_junit_xml, adapt_junit_xml_batch
from avera.adapters.logs import LogCsvAdapter, adapt_log_csv
from avera.adapters.requirements import RequirementsCsvAdapter, adapt_requirements_csv
from avera.adapters.simulation import SimulationCsvAdapter, adapt_simulation_csv

__all__ = [
    # Functional API (backward-compatible)
    "adapt_junit_xml",
    "adapt_junit_xml_batch",
    "adapt_log_csv",
    "adapt_requirements_csv",
    "adapt_simulation_csv",
    "adapt_canoe_xml",
    "adapt_canoe_asc",
    # Class adapters
    "JUnitXmlAdapter",
    "LogCsvAdapter",
    "SimulationCsvAdapter",
    "RequirementsCsvAdapter",
    "CANoeAdapter",
    # SDK interface
    "VerificationAdapter",
    "RequirementsAdapter",
    "AdapterRegistry",
]
