"""Mutation-based confidence lens for AVERA.

Answers a question a pass/fail gate cannot: *would the tests actually catch a
regression in the changed code?* It injects small, single-point mutations into the
changed region, and a separate runner checks whether the test suite kills each
mutant. Surviving mutants in changed code mean that region is **not truly verified
by tests** — a blind spot, even when the suite is green.

This directly targets the gap found by the discovery harness: real regressions that
slip past tests (see docs/AVERA_DISCOVERY_FINDINGS.md).

The engine here is pure (AST in, mutant sources out) so it is deterministic and
unit-testable. Running the tests against mutants is the caller's job; feed the
kill/survive results to :func:`mutation_confidence`.
"""

from .engine import (
    Mutant,
    function_line_range,
    generate_mutants,
)
from .score import (
    MUTATION_CONFIDENCE_SCHEMA_VERSION,
    MutationConfidence,
    mutation_confidence,
)

__all__ = [
    "Mutant",
    "generate_mutants",
    "function_line_range",
    "MutationConfidence",
    "mutation_confidence",
    "MUTATION_CONFIDENCE_SCHEMA_VERSION",
]
