# AVERA — Mutation-Based Confidence Lens

**Date:** 18 June 2026
**Status:** Implemented + demonstrated on real code
**Module:** `src/avera/mutation/`

## Why this lens

The discovery harness (`docs/AVERA_DISCOVERY_FINDINGS.md`) showed the hard case:
real regressions that slip past a project's own tests. A pass/fail gate cannot see
them — there is no failing test to consume.

This lens answers the prior question directly: **would the tests catch a fault in
the changed code at all?** It injects one controlled fault at a time into the
changed region and checks whether the test suite kills it. Surviving faults mean
that region is **not actually verified** — a blind spot, even when the suite is
green.

## This is fault injection — recognised in regulated domains

Mutation testing is the software form of **fault injection**, an explicitly
recognised verification method in:

- **ISO 26262** (automotive) — fault injection to demonstrate diagnostic/test coverage
- **DO-178C** (aviation) — structural coverage and robustness testing
- **IEC 62304** (medical) and **EN 50128** (railway) — test adequacy evidence

So the lens is **domain-neutral**: the same engine serves ordinary software CI and
safety-critical verification. The output is one more evidence signal feeding
AVERA's deterministic gate and signed evidence chain.

## How it works

1. Parse the changed file; restrict to the changed region (a function or line range).
2. Generate one **single-point mutant** per available site (AST-level):
   comparison swaps (`<`↔`<=`, `==`↔`!=`), arithmetic (`+`↔`-`), boolean (`and`↔`or`),
   constants (`True`↔`False`, `n`→`n+1`), `return <expr>`→`return None`.
3. A runner applies each mutant and runs the test suite.
4. `mutation_confidence(killed_flags)` → score = killed/total, with a deterministic
   verdict: `verified` (≥0.8), `partially_verified` (≥0.5), `unverified` (<0.5),
   `no_mutants`.

The engine (`engine.py`) is pure and deterministic — unit-tested in
`tests/test_mutation_lens.py`. Running tests against mutants is the caller's job.

## Real demonstration (pytoolz/toolz)

Ran the lens against toolz's **own** test suite on several real functions:

| Function | Mutants | Killed | Score | Verdict | Survivor |
|---|---|---|---|---|---|
| `isiterable` | 4 | 4 | 1.00 | verified | — |
| `tail` | 2 | 2 | 1.00 | verified | — |
| `take_nth` | 2 | 2 | 1.00 | verified | — |
| `topk` | 3 | 3 | 1.00 | verified | — |
| `random_sample` | 2 | 1 | 0.50 | **partially_verified** | `Lt -> LtE @ line 1057` |

**Real blind spot found:** in `random_sample`, changing `<` to `<=` on the
probability threshold kills **no** test — the suite does not pin that boundary. A
green run is therefore not evidence that boundary is correct. Meanwhile the lens
correctly confirms the other four functions are well verified. It distinguishes
tested from under-tested code on real data — which a pass/fail gate cannot.

## Public API

```python
from avera.mutation import (
    function_line_range,   # (start, end) for a function by name
    generate_mutants,      # source[, start, end] -> [Mutant]
    mutation_confidence,   # [killed: bool] -> MutationConfidence(score, verdict, survivors)
)
```

## Status / caveats

- Single-point AST mutations measure **test adequacy** of a region; they do not
  reproduce arbitrary multi-line rewrites (a structural regression is a separate
  signal — see the diff/behavioural lens on the roadmap).
- Running tests per mutant has a cost; scope to the changed region and the relevant
  test module for speed.
- Operator set is intentionally small and correct; it can grow (string/None swaps,
  off-by-one on slices) measured against the real-revert corpus.
