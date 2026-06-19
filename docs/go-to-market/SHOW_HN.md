# Show HN post — ready to paste

> Publish at https://news.ycombinator.com/submit. Title ≤ 80 chars. Keep the body
> short; put detail in the first comment (post it yourself right after submitting).
> Lead with the finding, not the pitch — this audience punishes overclaiming.

## Title

```
Show HN: AVERA – a deterministic check that proves no regression was introduced
```

## URL

```
https://github.com/tc7kxsszs5-cloud/avera
```

## Text (the "tell us more" field)

```
A green CI run only proves no expressed test *failed* — not that nothing
*regressed*. When prod breaks after a green merge, there's no machine-checkable
record of what regressed or why the merge was allowed. With AI agents opening PRs
faster than anyone reviews them, "the suite was green" and "that test is just
flaky" are how real regressions slip through.

AVERA is a small, local, deterministic gate. It diffs a baseline test run against
the current one and flags only failures that are *newly introduced* (a test that
passed before and fails now), then blocks — with a tamper-evident evidence trail.
No LLM in the decision; nothing leaves your machine.

I tried to falsify it, not flatter it. There's a public blind-replay benchmark:
on a real reverted commit in the `toolz` library (f0831e7), AVERA gets ONLY the
before/after test results — no hint where the bug is — and has to catch it. One
command reproduces it:

    git clone https://github.com/tc7kxsszs5-cloud/avera && cd avera
    pip install -e .
    ./benchmark/reproduce.sh
    # PASS  toolz-f0831e7  -> confirmed_regression / block

Honest about the limits (in the README too): AVERA catches a regression only once
a test expresses it — same scope as your own suite. It doesn't decide flaky-vs-real
(that stays human), and it isn't a certified tool. I'd genuinely value people
trying to break the idea or the benchmark.
```

## First comment (post immediately after submitting)

```
A bit more on how it works and where it fits:

- Input is just JUnit/xUnit XML (pytest, jest, go test, …), so it drops into
  existing CI with no toolchain change: `avera check --baseline main.xml
  --current pr.xml` → verdict + gate + exit code. There's a zero-config GitHub
  Action mode too (baseline+current inputs).

- The verdict is a *proven-total decision table* (enumerated over its whole input
  space), not an accreting pile of if-statements — so "is this a regression" is a
  deterministic, reproducible function, and the same evidence always yields the
  same integrity hash.

- It started as a regulated-domain tool (ISO 26262 / DO-178C / IEC 62304 / EN
  50128 / NASA NPR 7150.2), which is why there's an evidence manifest + hash-
  chained audit log + sign-off under the verdict. But the wedge is plain CI.

- What it deliberately does NOT do: catch a regression no test exercises (that's
  fault-injection / mutation analysis), adjudicate flaky-vs-real, or decide your
  release. It produces auditable evidence; a human signs off.

Repo + benchmark: https://github.com/tc7kxsszs5-cloud/avera — happy to answer
anything, and especially interested in cases where it misses.
```
