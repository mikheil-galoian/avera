# AVERA — Blind-Replay Harness

A falsification engine: take a **real revert from a real repo**, reconstruct the
regression, and run AVERA **blind** on the result diff — it sees only the two
JUnit result sets, never the bad commit, never where the bug is. The valuable
outcome is not a green demo; it is a case where AVERA *fails* to catch a real
regression — a true finding to fix.

Script: [`scripts/blind_replay.py`](../scripts/blind_replay.py).

## How it works

```
good state    = revert applied   (bug fixed)      -> baseline JUnit
current state = revert undone     (bug re-applied) -> current  JUnit
AVERA(baseline, current) -> verdict + gate, with no hint where the bug is
```

```bash
python scripts/blind_replay.py <repo_url> <revert_commit_sha> \
    --tests <pytest target> \
    --good <baseline ref>            # optional; see "two framings"
    --runner /path/to/python-with-pytest
```

Each run appends one JSON line to `reports/blind_corpus.jsonl` with an `outcome`:
`caught` · `missed` · `slipped` · `setup_failed`.

## Two honest framings (this matters)

The baseline ref decides *which question* you ask:

1. **Default (baseline = the revert commit).** Reproduces the project's
   **historical** test coverage at that moment — *did their own tests catch it?*
2. **`--good <merge/fix sha>` (baseline includes the regression test).** Asks
   *does AVERA block once a test expresses the bug?*

Both are true and both are recorded. A regression that has no test expressing it
is `slipped` — **not** catchable from results alone; that is the mutation-lens's
job, not a failure of the gate. Conflating the two would be dishonest.

## First real case — toolz `f0831e7` ("Faster isiterable…")

Same commit, both framings, verbatim from the harness:

| Framing | baseline | outcome | verdict | gate (general→railway) |
|---|---|---|---|---|
| Historical (revert commit) | `5a3b8b14` | **slipped** | expected_change | pass / review×4 |
| Test-included (merge) | `386c750` | **caught** | confirmed_regression | **block ×5** |

Reading: at the time, toolz's own suite did **not** express the `isiterable`
regression, so it slipped past CI (this is the discovery finding in
`AVERA_DISCOVERY_FINDINGS.md`). Once a test expresses it, AVERA — given only the
result diff — independently identifies the introduced failure
(`test_isiterable`, pass→fail), rules `confirmed_regression`, and **blocks under
every domain policy**. No hint where the bug was.

## Running it across many repos (continuous)

The engine is per-repo; a corpus is built by running it over a stream of revert
PRs (find them via the GitHub search API: merged PRs with `Revert` in the title).
Honest constraints, not yet automated:

- **Runnable repos only.** A third-party suite needs its deps/env; many won't set
  up. `setup_failed` rows are logged, not hidden.
- **Arbitrary code execution.** Running someone's test suite is RCE — do it only
  on trusted repos, ideally sandboxed. This is the blocker to "run it constantly"
  unattended.
- **Rate limits.** Unauthenticated GitHub search is throttled; a token is needed
  for volume.
- **Two outcome classes.** Expect a mix of `caught` (test expresses it) and
  `slipped` (it didn't) — both are signal; report the split, never just the wins.

The corpus doubles as (a) a growing set of **real outreach cases** and (b) a
**standing regression benchmark** for AVERA itself: any future `missed` is the
next thing to fix. Per the development doctrine, automation/scheduling is added
when the manual corpus shows it pays off — pulled by need, not built ahead.
