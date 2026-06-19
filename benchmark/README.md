# AVERA Regression-Replay Benchmark

A small, growing set of **real, public regressions** that AVERA classifies
deterministically — built so anyone can reproduce the result themselves in one
command. Determinism is AVERA's core claim; a repo you can *run* proves it, prose
only asserts it.

```bash
AVERA_PY=python3 ./benchmark/reproduce.sh
# PASS  toolz-f0831e7  -> confirmed_regression / block
```

## How a case works

Each case under `cases/<id>/` ships:
- `baseline.xml` — JUnit results from the **good** code (a known-good run).
- `current.xml` — JUnit results from the **bad** code (the regression re-applied).
- `case.json` — provenance + the expected AVERA verdict and gate decision.

`reproduce.sh` runs `avera check` on the two result sets and compares to the
expected outcome. AVERA receives **only the result diff** — never the bad commit,
never a hint where the bug is. It must independently identify the introduced
failure (a test green on baseline, red now), rule `confirmed_regression`, and
return `gate=block`.

This is a *blind* test: we try to falsify AVERA, not to flatter it. The most
valuable future case is one AVERA *misses* — that is a real finding to fix.

## Cases

| id | project | bug | outcome |
|----|---------|-----|---------|
| `toolz-f0831e7` | [pytoolz/toolz](https://github.com/pytoolz/toolz) | `f0831e7` "Faster isiterable…" (reverted in PR #551) | **caught** → `confirmed_regression` / `block` under every domain policy |

### Honest framing (read this)

For `toolz-f0831e7`: historically this bug **slipped past toolz's own CI** because
no test expressed it yet — the catching test was added in the revert PR. AVERA
catches it **once a test expresses the bug**, exactly like the project's own suite
would. AVERA does **not** catch a regression that no test exercises — that is the
job of fault-injection / mutation analysis, not of the gate. We state this plainly
because overclaiming is the failure mode this benchmark exists to avoid.

## Reproducing a case from source (optional, heavier)

`baseline.xml`/`current.xml` are committed so the AVERA verdict reproduces with no
external code execution. To regenerate them from the project's own source, see
[`scripts/blind_replay.py`](../scripts/blind_replay.py) — note that this clones
and runs a third-party test suite (arbitrary code execution); do it only on repos
you trust, ideally sandboxed.

## Contributing a case

Open a PR adding `cases/<id>/{baseline.xml,current.xml,case.json}`. Cases must be
real (provenance in `case.json`), and `reproduce.sh` must pass. Misses are
welcome — they make AVERA better.
