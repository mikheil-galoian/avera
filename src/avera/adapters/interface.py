"""Adapter SDK interface for AVERA.

Defines the abstract contracts every adapter must satisfy and provides a
central registry so the CLI and core pipeline can discover adapters by file
extension or explicit name.

Architecture
------------
Two abstract base classes cover the two adapter categories in AVERA:

``VerificationAdapter``
    Converts external test artifacts (JUnit XML, CANoe reports, simulation
    CSVs, log CSVs …) into AVERA verification-run dictionaries that can be
    saved as ``baseline_results.json`` / ``current_results.json``.

``RequirementsAdapter``
    Converts external requirement exports (CSV, ReqIF, DOORS-export …) into
    the AVERA requirements list format consumed by the classifier.

Both ABCs expose a ``can_handle(path)`` heuristic so the ``AdapterRegistry``
can auto-select the right adapter for a given file, and a ``metadata``
property that returns a stable identifier dict for embedding in reports.

Usage::

    from avera.adapters.interface import AdapterRegistry

    registry = AdapterRegistry.default()
    adapter  = registry.find_verification_adapter("test_report.xml")
    result   = adapter.adapt(Path("test_report.xml"), run_id="run-1", stage="current")
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Sentinel — marks an unset optional value distinctly from None
# ---------------------------------------------------------------------------

_UNSET: object = object()


# ---------------------------------------------------------------------------
# VerificationAdapter
# ---------------------------------------------------------------------------

class VerificationAdapter(abc.ABC):
    """Base class for adapters that produce AVERA verification-run dicts.

    Subclasses must set ``name``, ``version``, and ``source_format`` as class
    attributes and implement :meth:`adapt`.  They may override
    :meth:`can_handle` for smarter extension / content detection.

    Class attributes
    ----------------
    name : str
        Short, stable adapter identifier (e.g. ``"junit_xml"``).
    version : str
        Semantic version string (e.g. ``"1.0.0"``).
    source_format : str
        Human-readable format label embedded in report metadata.
    file_extensions : tuple[str, ...]
        File-name suffixes this adapter can handle (lower-case, with dot).
        Used by the default :meth:`can_handle` implementation.
    """

    name: str = ""
    version: str = "0.1.0"
    source_format: str = ""
    file_extensions: tuple[str, ...] = ()

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def adapt(
        self,
        path: Path,
        *,
        run_id: str,
        stage: str,
    ) -> dict[str, Any]:
        """Convert *path* into an AVERA verification-run dictionary.

        Parameters
        ----------
        path:
            Path to the source artifact.
        run_id:
            Identifier for this run (e.g. ``"baseline-v2.4.0"``).
        stage:
            Pipeline stage label — typically ``"baseline"`` or ``"current"``.

        Returns
        -------
        dict
            AVERA verification-run dict with keys ``runId``, ``stage``,
            ``tests`` and ``metadata``.

        Raises
        ------
        ValueError
            If the file is malformed, missing required fields, or empty.
        FileNotFoundError
            If *path* does not exist.
        """

    # ------------------------------------------------------------------
    # Optional override
    # ------------------------------------------------------------------

    def can_handle(self, path: Path) -> bool:
        """Return ``True`` if this adapter can process *path*.

        Default implementation checks whether the file suffix (lower-case)
        is in :attr:`file_extensions`.  Subclasses may override to inspect
        file content for disambiguation.
        """
        if not self.file_extensions:
            return False
        return path.suffix.lower() in self.file_extensions

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def metadata(self) -> dict[str, str]:
        """Return a stable metadata dict for embedding in reports."""
        return {
            "adapter": f"{self.name}.{self.version.replace('.', '_')}",
            "adapter_name": self.name,
            "adapter_version": self.version,
            "source_format": self.source_format,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, version={self.version!r})"


# ---------------------------------------------------------------------------
# RequirementsAdapter
# ---------------------------------------------------------------------------

class RequirementsAdapter(abc.ABC):
    """Base class for adapters that produce AVERA requirements lists.

    Subclasses implement :meth:`adapt_requirements` which returns a list of
    requirement dicts matching the canonical AVERA requirements schema:
    ``id``, ``title``, ``metric``, ``operator``, ``threshold``,
    ``safety_level``, ``component``, ``next_checks``.
    """

    name: str = ""
    version: str = "0.1.0"
    source_format: str = ""
    file_extensions: tuple[str, ...] = ()

    @abc.abstractmethod
    def adapt_requirements(self, path: Path) -> list[dict[str, Any]]:
        """Convert *path* into a list of AVERA requirement dicts.

        Returns
        -------
        list[dict]
            Each dict must contain at minimum ``id``.  Canonical optional
            fields: ``title``, ``metric``, ``operator``, ``threshold``,
            ``safety_level``, ``component``, ``next_checks``.

        Raises
        ------
        ValueError
            If the file is malformed or missing required columns.
        FileNotFoundError
            If *path* does not exist.
        """

    def can_handle(self, path: Path) -> bool:
        if not self.file_extensions:
            return False
        return path.suffix.lower() in self.file_extensions

    @property
    def metadata(self) -> dict[str, str]:
        return {
            "adapter": f"{self.name}.{self.version.replace('.', '_')}",
            "adapter_name": self.name,
            "adapter_version": self.version,
            "source_format": self.source_format,
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r}, version={self.version!r})"


# ---------------------------------------------------------------------------
# AdapterRegistry
# ---------------------------------------------------------------------------

class AdapterRegistry:
    """Central registry for :class:`VerificationAdapter` and
    :class:`RequirementsAdapter` instances.

    Adapters are stored by name.  :meth:`find_verification_adapter` and
    :meth:`find_requirements_adapter` walk registered adapters in insertion
    order and return the first whose :meth:`can_handle` returns ``True``.

    Usage::

        registry = AdapterRegistry()
        registry.register(JUnitXmlAdapter())
        registry.register(CANoeAdapter())

        adapter = registry.find_verification_adapter(Path("report.xml"))
        result  = adapter.adapt(path, run_id="r1", stage="current")
    """

    def __init__(self) -> None:
        self._verification: dict[str, VerificationAdapter] = {}
        self._requirements: dict[str, RequirementsAdapter] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        adapter: VerificationAdapter | RequirementsAdapter,
        *,
        overwrite: bool = False,
    ) -> None:
        """Register *adapter* by its :attr:`~VerificationAdapter.name`.

        Parameters
        ----------
        adapter:
            Adapter instance to register.
        overwrite:
            If ``False`` (default) and an adapter with the same name already
            exists, raises ``ValueError``.  Set to ``True`` to replace.
        """
        if isinstance(adapter, VerificationAdapter):
            store = self._verification
        elif isinstance(adapter, RequirementsAdapter):
            store = self._requirements  # type: ignore[assignment]
        else:
            raise TypeError(
                f"adapter must be VerificationAdapter or RequirementsAdapter, "
                f"got {type(adapter).__name__}"
            )

        if not adapter.name:
            raise ValueError("adapter.name must not be empty")

        if adapter.name in store and not overwrite:
            raise ValueError(
                f"An adapter named {adapter.name!r} is already registered. "
                "Pass overwrite=True to replace it."
            )
        store[adapter.name] = adapter  # type: ignore[assignment]

    def unregister(self, name: str) -> None:
        """Remove an adapter by name (either category)."""
        self._verification.pop(name, None)
        self._requirements.pop(name, None)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def find_verification_adapter(
        self,
        path: str | Path,
        *,
        name: str | None = None,
    ) -> VerificationAdapter:
        """Return the best-matching verification adapter for *path*.

        Parameters
        ----------
        path:
            Source artifact path used for :meth:`~VerificationAdapter.can_handle`.
        name:
            If provided, look up directly by adapter name instead of
            auto-detecting.

        Raises
        ------
        LookupError
            If no suitable adapter is found.
        """
        return self._find(self._verification, Path(path), name=name)  # type: ignore[return-value]

    def find_requirements_adapter(
        self,
        path: str | Path,
        *,
        name: str | None = None,
    ) -> RequirementsAdapter:
        """Return the best-matching requirements adapter for *path*."""
        return self._find(self._requirements, Path(path), name=name)  # type: ignore[return-value]

    def list_verification_adapters(self) -> list[str]:
        """Return names of all registered verification adapters."""
        return list(self._verification)

    def list_requirements_adapters(self) -> list[str]:
        """Return names of all registered requirements adapters."""
        return list(self._requirements)

    # ------------------------------------------------------------------
    # Default registry — ships with the built-in adapters
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> AdapterRegistry:
        """Return a registry pre-populated with all built-in adapters."""
        from avera.adapters.junit import JUnitXmlAdapter
        from avera.adapters.logs import LogCsvAdapter
        from avera.adapters.simulation import SimulationCsvAdapter
        from avera.adapters.requirements import RequirementsCsvAdapter
        from avera.adapters.canoe import CANoeAdapter

        registry = cls()
        registry.register(JUnitXmlAdapter())
        registry.register(LogCsvAdapter())
        registry.register(SimulationCsvAdapter())
        registry.register(CANoeAdapter())
        registry.register(RequirementsCsvAdapter())
        return registry

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _find(
        self,
        store: dict[str, Any],
        path: Path,
        *,
        name: str | None,
    ) -> Any:
        if name is not None:
            adapter = store.get(name)
            if adapter is None:
                available = ", ".join(store) or "(none)"
                raise LookupError(
                    f"No adapter named {name!r}. Available: {available}"
                )
            return adapter

        for adapter in store.values():
            if adapter.can_handle(path):
                return adapter

        available = ", ".join(store) or "(none)"
        raise LookupError(
            f"No adapter can handle {path.name!r}. "
            f"Registered adapters: {available}. "
            "Pass name= to select explicitly."
        )
