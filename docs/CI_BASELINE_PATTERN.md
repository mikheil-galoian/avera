# Getting the baseline in CI

`avera check` needs **two** test-result files: the current run (your PR) and a
**baseline** (the known-good run, usually `main`). Your CI already produces the
current one; this doc shows the three practical ways to get the baseline.

## Pattern A — run both refs in one job (simplest, always correct)

Run the suite once on the base branch and once on the PR head, in the same job.
No caching, no cross-run state. Slower (two test runs) but bulletproof. See the
ready example: [`examples/github-action-zero-config.yml`](../examples/github-action-zero-config.yml).

```yaml
# checkout base, run tests -> baseline.xml
git fetch origin ${{ github.base_ref }}
git checkout ${{ github.base_ref }}
pytest --junitxml=baseline.xml || true
# checkout PR head, run tests -> current.xml
git checkout ${{ github.sha }}
pytest --junitxml=current.xml || true
avera check --baseline baseline.xml --current current.xml
```

Note the `|| true`: a failing baseline or current run must still produce its XML so
AVERA can diff them — let AVERA decide pass/block, not the raw pytest exit code.

## Pattern B — cached baseline from the last `main` run (faster)

Have `main`'s CI upload its `baseline.xml` as an artifact (or cache); the PR job
downloads the most recent one instead of re-running `main`. One test run per PR.
Trade-off: the baseline is as fresh as the last `main` build, not the exact merge
base — fine for most teams.

```yaml
# in the main-branch workflow:
- uses: actions/upload-artifact@v4
  with: { name: avera-baseline, path: junit.xml }

# in the PR workflow:
- uses: dawidd6/action-download-artifact@v6
  with: { workflow: main.yml, name: avera-baseline, path: baseline/ }
- run: pytest --junitxml=current.xml || true
- run: avera check --baseline baseline/junit.xml --current current.xml
```

## Pattern C — nightly baseline (large suites)

For suites too slow to run per-PR, a scheduled nightly job on `main` publishes the
baseline; PRs diff against it. Cheapest, coarsest — the baseline can be up to a day
old, so a regression introduced and reverted within the day can be missed.

## Which to use

| Suite size | Recommended |
|---|---|
| Small / fast | **A** (run both — always exact) |
| Medium | **B** (cached from main) |
| Very large / slow | **C** (nightly) |

Start with **A**. It is the only one with no staleness window; move to B/C only when
the double run actually hurts.
