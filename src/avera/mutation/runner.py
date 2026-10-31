"""Run the mutation lens against a real test command.

For each single-point mutant of the changed region, the source file is replaced
in place, the caller's test command is run, and the mutant is recorded as
*killed* (the command failed or timed out) or *survived* (it still passed). The
original bytes are always restored, including on errors and Ctrl-C. A process
killed with SIGKILL cannot restore — run on a clean git tree.

Two honesty guards fail closed instead of reporting a score:

- the test command must pass on the untouched source (a red baseline would
  make every "kill" meaningless);
- a *null mutant* — the module re-serialised by ``ast.unparse`` with no
  mutation — must also pass, so a kill is caused by the fault, not formatting.

Bytecode caching is disabled for every run: a same-size mutant written within
the same second as the previous run would otherwise execute a stale ``.pyc``
of different code and falsely survive.

A hanging mutant counts as killed, as in standard mutation testing: CI would
time the suite out and fail.
"""

from __future__ import annotations

import ast
import os
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .engine import function_line_range, generate_mutants
from .score import MutationConfidence, mutation_confidence


class MutationLensError(RuntimeError):
    """The lens refused to produce a score (the measurement would be misleading)."""


@dataclass(frozen=True)
class MutantOutcome:
    index: int
    operator: str
    description: str
    lineno: int
    killed: bool
    timed_out: bool

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "operator": self.operator,
            "description": self.description,
            "lineno": self.lineno,
            "killed": self.killed,
            "timed_out": self.timed_out,
        }


@dataclass(frozen=True)
class MutationLensReport:
    source_path: str
    function: str | None
    test_command: list[str]
    confidence: MutationConfidence
    outcomes: list[MutantOutcome] = field(default_factory=list)
    line_range: tuple[int, int] | None = None

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "function": self.function,
            "line_range": list(self.line_range) if self.line_range else None,
            "test_command": list(self.test_command),
            "confidence": self.confidence.to_dict(),
            "outcomes": [o.to_dict() for o in self.outcomes],
        }


def _null_mutant(source: str) -> str:
    return ast.unparse(ast.parse(source))


def _run_tests(
    command: Sequence[str], cwd: str | Path | None, env: dict[str, str], timeout: float
) -> tuple[bool, bool]:
    """Run the test command once. Returns (passed, timed_out)."""
    try:
        result = subprocess.run(
            list(command),
            check=False,
            cwd=cwd,
            env=env,
            timeout=timeout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return False, True
    return result.returncode == 0, False


def run_mutation_lens(
    source_path: str | Path,
    test_command: Sequence[str],
    *,
    function: str | None = None,
    line_range: tuple[int, int] | None = None,
    cwd: str | Path | None = None,
    timeout: float = 120.0,
) -> MutationLensReport:
    """Mutate ``source_path`` and measure what the tests catch.

    Scope is the whole file by default. ``function`` scopes to one named
    function (as before); ``line_range`` scopes to an explicit ``(start,
    end)`` 1-indexed inclusive range instead — e.g. the lines a diff touched,
    for change-targeted mutation (EP-10). Passing both is rejected rather
    than silently picking one.
    """
    if function is not None and line_range is not None:
        raise MutationLensError("pass function= or line_range=, not both")
    if line_range is not None and line_range[0] > line_range[1]:
        raise MutationLensError(f"invalid line_range {line_range}: start must be <= end")

    path = Path(source_path)
    original = path.read_bytes()
    text = original.decode("utf-8")

    resolved_range: tuple[int, int] | None
    if function is not None:
        rng = function_line_range(text, function)
        if rng is None:
            raise MutationLensError(f"function {function!r} not found in {path}")
        resolved_range = rng
        mutants = generate_mutants(text, rng[0], rng[1])
    elif line_range is not None:
        resolved_range = line_range
        mutants = generate_mutants(text, line_range[0], line_range[1])
    else:
        resolved_range = None
        mutants = generate_mutants(text)

    with tempfile.TemporaryDirectory(prefix="avera-mutation-pyc-") as pyc_dir:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX=pyc_dir)

        passed, _ = _run_tests(test_command, cwd, env, timeout)
        if not passed:
            raise MutationLensError(
                "baseline: the test command does not pass on the unmodified source; "
                "a mutation score would be meaningless"
            )

        outcomes: list[MutantOutcome] = []
        try:
            path.write_bytes(_null_mutant(text).encode("utf-8"))
            passed, _ = _run_tests(test_command, cwd, env, timeout)
            if not passed:
                raise MutationLensError(
                    "null mutant failed: ast.unparse changed this module's behaviour, "
                    "so kills could not be attributed to the injected faults"
                )

            for mutant in mutants:
                path.write_bytes(mutant.source.encode("utf-8"))
                passed, timed_out = _run_tests(test_command, cwd, env, timeout)
                outcomes.append(
                    MutantOutcome(
                        index=mutant.index,
                        operator=mutant.operator,
                        description=mutant.description,
                        lineno=mutant.lineno,
                        killed=not passed,
                        timed_out=timed_out,
                    )
                )
        finally:
            path.write_bytes(original)

    confidence = mutation_confidence(
        [o.killed for o in outcomes],
        [o.description for o in outcomes if not o.killed],
    )
    return MutationLensReport(
        source_path=str(path),
        function=function,
        test_command=list(test_command),
        confidence=confidence,
        outcomes=outcomes,
        line_range=resolved_range,
    )
