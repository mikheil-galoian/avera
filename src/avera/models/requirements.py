"""Models for requirement evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Requirement:
    """A normalized requirement row from an automotive requirements export."""

    id: str
    component: str
    requirement: str
    metric: str
    operator: str
    threshold: float | str
    safety_level: str = ""
    next_checks: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
