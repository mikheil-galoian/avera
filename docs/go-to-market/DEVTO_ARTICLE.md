# dev.to article — ready to paste

> Publish at https://dev.to/new. Suggested tags: `testing`, `devops`, `ci`,
> `python`. This is the evergreen, SEO-friendly version; Show HN can link to it.

---

**Title:** Green CI proves nothing failed. Here's a deterministic check that proves nothing regressed.

---

Your CI is green. The PR merges. Prod breaks anyway.

A passing test suite proves exactly one thing: **no test that exists, failed.** It
does not prove that nothing *regressed*. The two are different, and the gap is
where real incidents live — especially now that AI agents open PRs faster than
anyone can review them, and "that test is just flaky" has become a reflex.

When something that worked before breaks after a green merge, there is usually no
machine-checkable record of **what** regressed or **why the merge was allowed**.
Someone reconstructs it by hand, after the incident.

## The idea: gate on *introduced* failures, deterministically

[AVERA](https://github.com/tc7kxsszs5-cloud/avera) is a small, local, deterministic
gate. It compares a **baseline** test run (known-good, e.g. `main`) against the
**current** one (the PR), and flags only the failures that are *newly introduced*
— a test that **passed before and fails now**. That's the difference between "a
test is red" and "this change broke something."

```bash
avera check --baseline main.xml --current pr.xml
# Verdict:  confirmed_regression
# Introduced failures (1): pkg.tests.test_thing
# Gate [general.v1]: block        (exit 1 — fails the CI step)
```

Input is plain JUnit/xUnit XML (pytest, jest, go test, JUnit…), so it drops into
existing CI with no toolchain change. No LLM is involved in the decision; nothing
leaves your machine.

## Don't trust me — reproduce it

Claims about determinism are cheap. So there's a public **blind-replay benchmark**:
take a *real* reverted commit from an open-source project, give AVERA only the
before/after test results — **no hint where the bug is** — and see if it catches it.

The seed case is commit `f0831e7` in [`pytoolz/toolz`](https://github.com/pytoolz/toolz)
(later reverted in PR #551). One command:

```bash
git clone https://github.com/tc7kxsszs5-cloud/avera && cd avera
pip install -e .
./benchmark/reproduce.sh
# PASS  toolz-f0831e7  -> confirmed_regression / block
```

Given only the result diff, AVERA independently identifies the introduced failure
(`test_isiterable`, pass→fail), rules `confirmed_regression`, and blocks under
every domain policy. You can run it yourself — that *is* the credibility mechanism.

## What makes the verdict trustworthy

- **A proven-total decision table.** "Is this a regression?" is a deterministic
  function over a small set of predicates, enumerated over its entire input space
  in tests — not an accreting pile of `if`s where edge cases hide.
- **Fail-closed.** An unknown or malformed status is treated as a failure, never
  silently passed. A gate must never green-light on ambiguous evidence.
- **A tamper-evident trail.** Behind the verdict: a content-addressed evidence
  manifest, a hash-chained audit log, and a sign-off bound to that manifest. Same
  inputs → same verdict → same integrity hash, on any machine.

(That trail is why AVERA also ships domain policies for ISO 26262, DO-178C, IEC
62304, EN 50128, and NASA NPR 7150.2 — but the everyday wedge is plain CI.)

## What it deliberately does *not* do

Stated plainly, because overclaiming is the failure mode here:

- It does **not** catch a regression that **no test exercises** — that needs
  fault-injection / mutation analysis, not the gate. (Same blind spot as your own
  suite.)
- It does **not** adjudicate **flaky vs real** — that stays a human call.
- It does **not** decide your release. It produces auditable evidence; a human
  signs off. No model in the decision path.

## Try it / break it

```bash
git clone https://github.com/tc7kxsszs5-cloud/avera && cd avera
pip install -e .
avera check --baseline your-main.xml --current your-pr.xml
```

The most useful thing you can send back is a case where it **misses** a real
regression — that's a finding, and the benchmark is built to grow on exactly those.

Repo + benchmark: <https://github.com/tc7kxsszs5-cloud/avera>
