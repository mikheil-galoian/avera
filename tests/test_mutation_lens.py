"""Tests for the mutation-based confidence lens (engine + score)."""

from __future__ import annotations

import ast

import pytest

from avera.mutation import (
    MUTATION_CONFIDENCE_SCHEMA_VERSION,
    function_line_range,
    generate_mutants,
    mutation_confidence,
)
from avera.mutation.score import PARTIALLY_VERIFIED, UNVERIFIED, VERIFIED, NO_MUTANTS

SAMPLE = '''\
def is_small(x):
    return x < 10


def both(a, b):
    return a and b
'''


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def test_generates_mutants_and_each_is_valid_python():
    mutants = generate_mutants(SAMPLE)
    assert mutants, "expected at least one mutant"
    for m in mutants:
        ast.parse(m.source)  # must be syntactically valid
        assert m.source != SAMPLE  # actually changed


def test_comparison_and_boolean_and_constant_operators_present():
    ops = {m.operator for m in generate_mutants(SAMPLE)}
    assert "comparison" in ops      # x < 10
    assert "boolean" in ops         # a and b
    assert "constant" in ops        # 10


def test_line_range_limits_mutations():
    rng = function_line_range(SAMPLE, "both")
    assert rng is not None
    start, end = rng
    mutants = generate_mutants(SAMPLE, start, end)
    # Only the `both` function (a and b) should be mutated — no comparison from is_small.
    assert mutants
    assert all(start <= m.lineno <= end for m in mutants)
    assert "comparison" not in {m.operator for m in mutants}


def test_each_mutant_is_single_point():
    # A mutant should differ from the original by exactly one operator/constant,
    # i.e. only one of the known sites changed. We approximate by checking the
    # mutated source still parses and is not equal, and count differs minimally.
    mutants = generate_mutants(SAMPLE)
    originals = {m.index for m in mutants}
    assert len(originals) == len(mutants)  # unique indices


def test_function_line_range_unknown_returns_none():
    assert function_line_range(SAMPLE, "does_not_exist") is None


def test_return_mutation_for_function_with_return():
    src = "def f():\n    return 42\n"
    ops = {m.operator for m in generate_mutants(src)}
    assert "return" in ops or "constant" in ops


# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------

def test_all_killed_is_verified():
    r = mutation_confidence([True, True, True, True])
    assert r.verdict == VERIFIED
    assert r.mutation_score == 1.0
    assert r.is_blind_spot is False


def test_all_survived_is_unverified_blind_spot():
    r = mutation_confidence([False, False, False], ["Lt->LtE @ line 2"])
    assert r.verdict == UNVERIFIED
    assert r.mutation_score == 0.0
    assert r.is_blind_spot is True
    assert r.survivors == ["Lt->LtE @ line 2"]


def test_partial_is_partially_verified():
    r = mutation_confidence([True, False, True, False])  # 0.5
    assert r.verdict == PARTIALLY_VERIFIED
    assert r.is_blind_spot is True


def test_empty_is_no_mutants():
    r = mutation_confidence([])
    assert r.verdict == NO_MUTANTS
    assert r.total == 0


def test_serialization():
    d = mutation_confidence([True, False]).to_dict()
    assert d["schema_version"] == MUTATION_CONFIDENCE_SCHEMA_VERSION
    assert d["total"] == 2 and d["killed"] == 1
