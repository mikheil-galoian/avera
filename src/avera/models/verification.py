"""Models for baseline and current verification evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestResult:
    """Single test or simulation result within a verification run."""

    id: str
    status: str
    component: str = ""
    metrics: dict[str, int | float | str | bool | None] = field(default_factory=dict)
    evidence: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationRun:
    """A baseline or current verification run loaded from JSON."""

    run_id: str
    stage: str
    tests: tuple[TestResult, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_test_id(self) -> dict[str, TestResult]:
        """Return test results keyed by test id."""

        return {test.id: test for test in self.tests}
