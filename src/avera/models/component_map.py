"""Models for source/component traceability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ComponentMapEntry:
    """Mapping from an engineering artifact path to owned evidence."""

    path: str
    component: str
    requirements: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
