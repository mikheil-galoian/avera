"""AST-based single-point mutation generator (domain-neutral).

Mutation testing is the software form of **fault injection** — a method explicitly
recognised by ISO 26262 (automotive) and DO-178C (aviation) for demonstrating that a
verification suite is actually capable of detecting faults. The same engine serves
ordinary software CI and safety-critical verification: it injects one controlled
fault at a time into a changed region and lets a runner check whether the tests
catch it.

The engine is pure and deterministic: source in, mutant source variants out. It
mutates only nodes within a given line range (the changed region), one fault per
mutant. Requires Python 3.9+ (``ast.unparse``).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class Mutant:
    """One single-point mutant of a source file."""

    index: int
    operator: str        # e.g. "comparison", "boolean", "constant", "arithmetic", "return"
    description: str      # human-readable, e.g. "Lt -> LtE @ line 42"
    lineno: int
    source: str          # full mutated module source


# ---------------------------------------------------------------------------
# Operator tables
# ---------------------------------------------------------------------------

_COMPARE_SWAP: dict[type, type] = {
    ast.Lt: ast.LtE, ast.LtE: ast.Lt,
    ast.Gt: ast.GtE, ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
}

_BINOP_SWAP: dict[type, type] = {
    ast.Add: ast.Sub, ast.Sub: ast.Add,
    ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult,
}

_BOOLOP_SWAP: dict[type, type] = {ast.And: ast.Or, ast.Or: ast.And}


def _line_in_range(node: ast.AST, start: int, end: int) -> bool:
    ln = getattr(node, "lineno", None)
    return ln is not None and start <= ln <= end


def _describe_for(node: ast.AST) -> list[tuple[str, str]]:
    """Return (operator, label) pairs describing each available mutation for a node.

    The actual transform is re-derived in :func:`generate_mutants` by node identity,
    so this only needs to enumerate *how many* and *what kind*.
    """
    out: list[tuple[str, str]] = []
    if isinstance(node, ast.Compare) and node.ops:
        op = type(node.ops[0])
        if op in _COMPARE_SWAP:
            out.append(("comparison", f"{op.__name__} -> {_COMPARE_SWAP[op].__name__}"))
    elif isinstance(node, ast.BinOp) and type(node.op) in _BINOP_SWAP:
        op = type(node.op)
        out.append(("arithmetic", f"{op.__name__} -> {_BINOP_SWAP[op].__name__}"))
    elif isinstance(node, ast.BoolOp) and type(node.op) in _BOOLOP_SWAP:
        op = type(node.op)
        out.append(("boolean", f"{op.__name__} -> {_BOOLOP_SWAP[op].__name__}"))
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            out.append(("constant", f"{node.value} -> {not node.value}"))
        elif isinstance(node.value, int):
            out.append(("constant", f"{node.value} -> {node.value + 1}"))
    elif isinstance(node, ast.Return) and node.value is not None:
        out.append(("return", "return <expr> -> return None"))
    return out


def _apply(node: ast.AST, operator: str) -> None:
    """Apply the (single) mutation of the given operator kind to node, in place."""
    if operator == "comparison":
        node.ops[0] = _COMPARE_SWAP[type(node.ops[0])]()  # type: ignore[attr-defined]
    elif operator == "arithmetic":
        node.op = _BINOP_SWAP[type(node.op)]()  # type: ignore[attr-defined]
    elif operator == "boolean":
        node.op = _BOOLOP_SWAP[type(node.op)]()  # type: ignore[attr-defined]
    elif operator == "constant":
        value = node.value  # type: ignore[attr-defined]
        node.value = (not value) if isinstance(value, bool) else value + 1  # type: ignore[attr-defined]
    elif operator == "return":
        node.value = ast.Constant(value=None)  # type: ignore[attr-defined]


def function_line_range(source: str, name: str) -> tuple[int, int] | None:
    """Return the (start, end) line range of a top-level-or-nested function by name."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            end = getattr(node, "end_lineno", node.lineno)
            return node.lineno, int(end)
    return None


def generate_mutants(
    source: str,
    start_line: int = 1,
    end_line: int | None = None,
) -> list[Mutant]:
    """Generate one mutant per available single-point mutation in the line range.

    Deterministic: ``ast.walk`` order is stable for identical source, so each mutant
    re-parses the source and applies exactly one mutation at a stable node index.
    """
    if end_line is None:
        end_line = max((1, source.count("\n") + 1))

    base = ast.parse(source)
    # Enumerate (node_index, operator) sites in stable walk order.
    sites: list[tuple[int, str, str]] = []
    for idx, node in enumerate(ast.walk(base)):
        if not _line_in_range(node, start_line, end_line):
            continue
        for operator, label in _describe_for(node):
            sites.append((idx, operator, label))

    mutants: list[Mutant] = []
    for mut_index, (node_index, operator, label) in enumerate(sites):
        tree = ast.parse(source)
        target = list(ast.walk(tree))[node_index]
        lineno = int(getattr(target, "lineno", start_line))
        _apply(target, operator)
        ast.fix_missing_locations(tree)
        mutants.append(
            Mutant(
                index=mut_index,
                operator=operator,
                description=f"{label} @ line {lineno}",
                lineno=lineno,
                source=ast.unparse(tree),
            )
        )
    return mutants
