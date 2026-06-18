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
| A1 | Audit log | no external anchor → chain fully rewritable | CRITICAL | **SCHEDULED** |
| A2 | Audit log | truncation undetected | HIGH | **SCHEDULED** |
| A3 | Audit log | forged record can be appended (no key) | HIGH | **SCHEDULED** |
| A5 | Audit log | multi-process concurrency corrupts chain | MED | **SCHEDULED** |
| K3 | Classifier | `passed→timeout` → environment_failure while introduced≠∅ (contradiction) | HIGH | **SCHEDULED** |
| K4 | Adapters | single-file JUnit duplicate id, fail-then-pass dropped | HIGH | **SCHEDULED** |
| K5 | Adapters | CSV `_combine_status` ranks unknown = passed, order-dependent | MED | **SCHEDULED** |
| S1 | Sign-off | `verify_artifacts=False` severs binding; root check trusts manifest field | MED | **SCHEDULED** |
| Gp | Gate/policy | policy with bad `risk_rank`/`max_allowed_risk` silently degrades | MED | **SCHEDULED** |
| Pol | Policy resolution | env/cwd can change which builtin policy file loads | MED | **SCHEDULED** |
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

**A1–A3,A5 Audit log — the biggest item.** The chain is currently self-consistent
only: an attacker with file write access can re-stitch the whole log from genesis,
truncate the tail, or append forged records, because there is no secret/anchor.
Design to close: (1) keyed **HMAC-SHA256** per record using a key held outside the
file (env/KMS), or per-checkpoint asymmetric signatures; (2) persist a monotonic
HEAD/count in a separate trust store and require the last record to match it
(truncation); (3) process-global file lock (`fcntl.flock`) + server-side atomic
`seq`. Until then the audit log is tamper-*evident against accidental edits and
adjacent tampering*, not against a privileged attacker — stated plainly.

**K3 env-vs-introduced ordering.** `passed→timeout` is currently classed
environment_failure even when an introduced failure exists. Needs a deliberate
policy: when is a timeout environmental vs a real regression? Touching it shifts the
`bms-environment-failure` fixture contract, so it requires a decision, not a quick flip.

**K4/K5 adapter status merging.** Single-file JUnit and CSV adapters should use the
same worst-status-wins, fail-closed merge as the batch JUnit path; centralise one
status taxonomy shared by comparator + all adapters.

**S1 sign-off toggle.** Make `verify_artifacts` fail-closed (skipping verification
must not yield `ok=True`) and re-derive the manifest root for the binding check
rather than trusting the manifest's self-declared `integrity_root` field.

**Gp/Pol policy validation & resolution.** `policy_from_dict` should reject a
`max_allowed_risk` absent from `risk_rank`, a `risk_rank` missing levels, and
non-finite `min_confidence_score`; builtin-policy resolution should be pinned
(package data or recorded resolved-path + content hash) so env/cwd cannot swap it.

## Standing principle

Every core invariant gets an adversarial auditor; new holes become tracked rows
here with severity and a fix or a dated plan. "Defensible" means **audited and
transparent**, not "assumed perfect".
