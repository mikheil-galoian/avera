# AVERA Change Impact — stage decomposition

Status: **proposed, not started**. This is the planning artifact required before
building a new stage (see `PLANNING.md` in the user's global config). Owner
review happens here before any code is written.

## Problem

AVERA's gate today only sees **test results** (baseline vs current JUnit). It
correctly catches a regression once some test flips pass→fail. It is
structurally blind to the other, larger class of regression: changed code that
**no test exercises at all**. Industry data says this is most of the problem —
71% of confirmed production failures passed every existing CI check
(see `docs/AVERA_DISCOVERY_FINDINGS.md` and the go-to-market research). The
mutation lens (`T-13`, merged) can measure this, but only when a human points
it at a specific function by name — there is no automatic link between *what
changed*, *whether it's covered*, and *whether that coverage is any good*.

## Goal

Given a diff (two git refs, or a unified diff) **plus** a standard coverage
report, AVERA answers one honest question per change: **how much of what
changed is actually backed by evidence, and how strong is that evidence?**

Three tiers of evidence, cheapest first:

1. **Uncovered** — changed line, zero test touches it. No evidence either way.
2. **Covered** — a test executes the line, but execution isn't verification.
3. **Covered + mutation-verified** — the existing mutation lens (`T-13`) is run
   automatically, scoped to the changed+covered region, so "covered" is
   upgraded to "tests actually fail if this breaks."

## Non-goals (this stage)

- **Model-based ingestion** (SysML, Simulink, simulation schemas). Real, but
  needs a regulated-domain design partner to drive the actual schema — building
  it speculatively repeats the mistake the discovery harness was built to
  avoid. Deferred until requested.
- **Changing the `avera.check/v0` contract.** CounterProof already consumes it
  (`#12`/`#14`/`#18`); this stage ships as a **new, separate command** so the
  existing contract stays untouched and nothing already integrated can break.
- **Exhaustive mutation on every uncovered line.** Too slow to be zero-config.
  Mutation only runs where there is already a verdict to strengthen (covered
  lines), bounded by a budget.

## Non-functional constraint

AVERA's standard library-only, zero-dependency property is a real
differentiator (nothing to conflict with a CI image, nothing to audit in a
regulated supply chain). This stage must not add a runtime dependency: unified
diff parsing is plain text, LCOV is a line-oriented text format, Cobertura is
XML (`xml.etree`, stdlib). All in reach without a new import.

## Epics

### EP-09 — Change coverage mapping
Turn (diff, coverage report) into one deterministic number: what fraction of
the changed lines in this change are covered by *any* test.

- **US-09.1** — Parse a unified diff into per-file changed line ranges (added
  and modified lines in the new version; deleted lines carry nothing to
  cover).
- **US-09.2** — Parse a standard **LCOV** report (`lcov.info`) into per-file
  executed-line sets. LCOV is the common output of `pytest-cov`, Jest/Istanbul,
  Go (`go tool cover -func` convertible), grcov (Rust), and more.
- **US-09.3** — Parse a standard **Cobertura XML** report into the same shape.
  Cobertura covers JaCoCo (Java), `coverage.py --cobertura`, and several
  Node/Go exporters — between LCOV and Cobertura, nearly every common CI
  toolchain is reachable with zero new dependencies.
- **US-09.4** — Compute `coverage_of_change` per file and in aggregate
  (changed ∩ covered / changed), deterministic, with the uncovered line list
  as first-class output (not just a percentage — an auditor needs the lines).
  Fail closed: a file present in the diff but absent from the coverage report
  is "uncovered," never silently skipped.

### EP-10 — Change-targeted mutation (depends on EP-09, T-13)
Upgrade "covered" to "verified" without asking the user to name functions.

- **US-10.1** — Extend the existing mutation runner
  (`avera.mutation.run_mutation_lens`, from `T-13`) to accept an explicit
  `(start_line, end_line)` range, additive to the current `function=` name
  parameter — not a rewrite, the engine already mutates by line range
  internally (`generate_mutants(source, start_line, end_line)`).
- **US-10.2** — For each changed+covered region from EP-09, automatically run
  the mutation lens, bounded by a budget (max mutants / max seconds). Over
  budget → marked explicitly "not evaluated," never silently reported as
  either weak or strong evidence.
- **US-10.3** — Combine into one verdict: uncovered-line list,
  weak-evidence-line list (covered but mutation score below threshold), and an
  aggregate score — the same honest, fail-closed posture as the rest of AVERA.

### EP-11 — Command, policy, dogfood
Ship it as something a team can actually turn on.

- **US-11.1** — New policy fields (`coverage_of_change_min`,
  `mutation_score_of_change_min`) per domain, so regulated domains can set a
  stricter bar than plain CI by default.
- **US-11.2** — New CLI command, **`avera change-impact`** (name open to
  bikeshedding) — separate from `avera check`, so the stable v0 contract is
  never touched and adoption is incremental, not a breaking change to anyone
  already integrated.
- **US-11.3** — Dogfood on AVERA's own repository: AVERA's CI already produces
  both a diff (every PR) and a coverage report (the advisory coverage job in
  `quality.yml`) — the first real validation is AVERA pointed at itself.

## Architecture notes / risks

- **Coverage format dialects.** LCOV and Cobertura both have minor variants
  across tools. Parse only the standard directives (`LH`/`LF` for LCOV,
  `hits=` for Cobertura `<line>`), and fail closed on anything unrecognized —
  never guess.
- **Diff line semantics.** Unified diff hunk headers (`@@ -a,b +c,d @@`) are a
  stable, well-specified format; only the "new file" side matters here.
- **Mutation cost.** The existing runner already executes the real test suite
  once per mutant — that is the expensive part, not new here, but automatic
  triggering means the budget has to be real, not advisory, and "not
  evaluated" must be a distinct, visible state from "evaluated and weak."
- **No change to `avera.check/v0`.** This stage is additive at the repo level,
  not at the contract level — avoids re-opening the CounterProof negotiation.

## Tech debt flagged in advance

- EP-10's mutation budget (max mutants / seconds) starts as a reasonable
  constant; real tuning needs data from the dogfood run (`US-11.3`) before it
  should be treated as settled. Revisit after first real usage, not before.

## Backlog mapping

Tracked as `.taskmaster/tasks/tasks.json` ids **9** (EP-09), **10** (EP-10),
**11** (EP-11), each epic as one top-level task with its stories as subtasks —
same shape already used for tasks 1–8. No new backlog system introduced.
