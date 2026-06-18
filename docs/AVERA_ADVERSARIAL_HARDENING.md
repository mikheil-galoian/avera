# AVERA — Adversarial Hardening Report

**Date:** 18 June 2026
**Method:** 5 independent adversarial auditors attacked the core, each trying to
break one load-bearing invariant with **runnable repros** (no fabrication). Real
holes were found and either fixed-and-tested or scheduled with a design. The point
is not to claim the core is unbreakable — no software is — but that it is
**continuously self-attacked and every hole is tracked**.

Domains the core must serve: automotive (ISO 26262), aviation (DO-178C), railway
(EN 50128), medical (IEC 62304) — 20 fixtures across 7 subsystem families.

## Summary table

| # | Subsystem | Hole | Severity | Status |
|---|---|---|---|---|
| G1 | Gate | NaN/inf/bool confidence passes the gate | HIGH | **FIXED** |
| G2 | Gate | unknown / mis-cased risk treated as safest → pass | HIGH | **FIXED** |
| G3 | Gate | non-string (list) verdict bypasses block | MED | **FIXED** |
| C1 | Comparator | unusual failure status (`crash`,`segfault`,`panic`,``) hides a regression | HIGH | **FIXED** |
| C2 | Comparator | non-pass baseline (`xfail`,…) then fail not surfaced; orphaned `possible_failure` | HIGH | **FIXED** |
| K1 | Classifier | introduced failure could yield a pass-like verdict | HIGH | **FIXED** (backstop) |
| M1 | Manifest | root commits only to *listed* artifacts → silent omission | MED | **FIXED** |
| A4 | Audit log | `verify_chain` trusts arbitrary top-level fields | MED | **FIXED** |
| A1 | Audit log | no external anchor → chain fully rewritable | CRITICAL | **FIXED** (keyed HMAC mode) |
| A2 | Audit log | truncation undetected | HIGH | **FIXED** (anchor) |
| A3 | Audit log | forged record can be appended (no key) | HIGH | **FIXED** (keyed HMAC mode) |
| A5 | Audit log | multi-process concurrency corrupts chain | MED | **FIXED** (file lock) |
| S1 | Sign-off | `verify_artifacts=False` severs binding | MED | **FIXED** (fail-closed) |
| K3 | Classifier | `passed→timeout` → environment_failure while introduced≠∅ (contradiction) | HIGH | **FIXED** (env must explain all) |
| K4 | Adapters | single-file JUnit duplicate id, fail-then-pass dropped | HIGH | **FIXED** (shared merge) |
| K5 | Adapters | CSV `_combine_status` ranks unknown = passed, order-dependent | MED | **FIXED** (fail-closed taxonomy) |
| Gp | Gate/policy | policy with bad `risk_rank`/`max_allowed_risk` silently degrades | MED | **FIXED** (validation) |
| Pol | Policy resolution | env/cwd can change which builtin policy file loads | MED | **FIXED** (package-dir first) |
| M2/M3 | Manifest | path re-point & summary fields outside the root | LOW | noted |

What **held** under attack (verified): gate arithmetic/boundary determinism;
manifest content-addressing + machine-independence + recompute-on-verify; audit
adjacent-record linkage, canonicalisation, single-instance concurrency; sign-off
state machine (no skipping/terminal-exit) and the default `verify_artifacts=True`
binding incl. disk-tamper and root-forgery; classifier determinism and happy path.

## Fixed in this pass (with locking tests)

- **Gate fails closed** (`gates/policy.py`): inputs are normalised; unknown/mis-cased
  risk → maximum severity; non-finite/bool confidence never satisfies the minimum;
  non-string verdict → safe fallback. Tests: `tests/test_gate_failclosed.py`.
- **Comparator fails closed** (`compare/baseline_comparator.py`): three-bucket model
  pass / failure / inconclusive. Any non-pass, non-inconclusive status is a failure
  (open vocabulary); a current failure under a non-pass baseline is surfaced; the
  orphaned `possible_failure` is gone. `inconclusive`/`unknown` map to
  insufficient-evidence, not failure. Tests: `tests/test_comparator_failclosed.py`.
- **Classifier backstop** (`classify/risk_classifier.py`): a non-empty
  `introduced_failures` can never be reported as `successful_change`/`expected_change`
  — it escalates to `confirmed_regression`.
- **Manifest commits to the full role surface** (`evidence/manifest.py`): the
  integrity root binds every canonical role with its `present` flag, so dropping a
  produced artifact changes the root and any sign-off bound to it detects the omission.
- **Audit verify fixed-schema** (`audit/log.py`): `verify_chain` recomputes each
  `self_hash` from an explicit key allowlist, so injected/renamed top-level fields fail.

All 20 fixtures and the affected unit suites stay green after these changes.

## Scheduled (honest — not yet closed)

**A1–A3, A5 Audit log — CLOSED (with deployment note).** Now implemented:
(1) optional keyed **HMAC-SHA256** (`AuditLog(path, key=...)` or `AVERA_AUDIT_KEY`)
— without the secret a forged record or full re-stitch is rejected; (2) opt-in
external anchor `verify_chain(expected_count=, expected_last_hash=)` detects
truncation/rollback; (3) cross-process `fcntl.flock` around the read-prev+write
critical section. Tests: `tests/test_audit_hardening.py`. **Deployment note:** the
strong guarantee requires a key + persisted anchor; the default unkeyed/anchorless
mode remains tamper-evident only against accidental/adjacent edits — set
`AVERA_AUDIT_KEY` and persist the head in production.

**S1 Sign-off — CLOSED.** `validate_signoff_against_manifest` now fails closed: when
`verify_artifacts=False` it records an error and `manifest_intact=False`, so skipping
verification can never yield `ok=True`. (`signoff/workflow.py`.)

**K3 env-vs-introduced ordering — CLOSED.** `environment_failure` is now returned
only when the environment signal is the *whole* story: no introduced threshold
regression AND every introduced pass→fail is itself explained by an environment
pattern. A lone `passed→timeout` still classifies as `environment_failure` (review,
fixture contract preserved); but a real introduced failure that is NOT an env
pattern can no longer be masked as flaky infra just because some other test timed
out — it falls through to `confirmed_regression`. Tests:
`tests/test_classifier_env_vs_regression.py`. (`classify/risk_classifier.py`.)

**K4/K5 adapter status merging — CLOSED.** A single fail-closed taxonomy now lives
in `compare/baseline_comparator.py::status_severity` (unknown/empty status ranks as
a *failure*, never tying with `passed`). It is shared by: the comparator's
`_index_tests` (duplicate ids across a run merge worst-status-wins), the JUnit
adapter (single-file *and* batch dedup via one `_merge_into`), and the CSV log
adapter (`_combine_status` now order-independent and fail-closed). Tests:
`tests/test_adapter_policy_hardening.py`.

**S1 sign-off toggle.** Make `verify_artifacts` fail-closed (skipping verification
must not yield `ok=True`) and re-derive the manifest root for the binding check
rather than trusting the manifest's self-declared `integrity_root` field.

**Gp/Pol policy validation & resolution — CLOSED.** `policy_from_dict` now rejects:
a `max_allowed_risk` absent from the effective `risk_rank`, non-integer rank values,
an empty `risk_rank`, an empty `policy_id`, and a non-finite or out-of-`[0,1]`
`min_confidence_score` (previously a `NaN` silently sent every report to review).
Built-in resolution tries the trusted package `policies/` dir *before*
`AVERA_POLICIES_DIR`/cwd, so a present built-in always loads from the shipped,
audited copy and the environment cannot swap it for a laxer one; env/cwd remain a
fallback only when the package copy is absent. (`gates/policy_loader.py`.)

## Standing principle

Every core invariant gets an adversarial auditor; new holes become tracked rows
here with severity and a fix or a dated plan. "Defensible" means **audited and
transparent**, not "assumed perfect".
