# AVERA for Space Flight Software — the SWE-191 evidence, automatically

## The hook (verified, not aspirational)

NASA **SWE-191 — Software Regression Testing** requires that the project manager
*"plan and conduct software regression testing to **demonstrate that defects have
not been introduced** into previously integrated or tested software and have not
produced a security vulnerability,"* with evidence required for **all** software
modifications after the original test plan.
Source: [NASA Software Engineering Handbook, SWE-191](https://swehb.nasa.gov/display/SWEHBVD/SWE-191+-+Software+Regression+Testing) (NPR 7150.2).

That requirement — *demonstrate that no defect was introduced, with evidence, for
every change* — is **exactly AVERA's verdict**: a deterministic, evidence-backed
decision that a change introduced (or did not introduce) a regression.

## What AVERA produces for SWE-191

| SWE-191 needs | AVERA produces |
|---|---|
| Demonstrate no defect introduced by a change | `confirmed_regression` / clean verdict from a baseline-vs-current test diff — fail-closed |
| Evidence, for **every** modification | content-addressed **evidence manifest** (`integrity_root`) per change |
| Tamper-evident, auditable record | **hash-chained SHA-256 audit log** (optional keyed HMAC) + **sign-off** bound to the manifest |
| Calibrated to criticality (human-rated vs not) | **space policy** mapping NASA software **Class A–F** (`nasa-a … nasa-f`) onto the gate; Class A = strictest |

One command, on plain test output:

```bash
avera check --baseline before.xml --current after.xml --policy space
# Verdict: confirmed_regression
# Gate [space.v1]: block   (risk exceeds allowed — human-rated tier)
```

## Proof it actually catches a real regression (blind)

On commit `f0831e7` of the open-source `pytoolz/toolz` library, given **only** the
before/after test results — no hint where the bug was — AVERA independently
flagged the introduced failure (`test_isiterable`, pass→fail), ruled
`confirmed_regression`, and blocked under the space policy. Reproduce it yourself:
`./benchmark/reproduce.sh`. This is the SWE-191 demonstration, automated.

## The reachable entry point: cFS

NASA's **core Flight System (cFS)** is open-source on GitHub with public,
CI-shaped build/test artifacts — a uniquely reachable target for a regulated
domain. A concrete first step: run `avera check` across a cFS change's
before/after test results and show the SWE-191-style introduced-regression
evidence on real flight-heritage software. *(cFS specifics to confirm before
outreach.)*

## Honest limits (say these up front)

- AVERA demonstrates that **no test-expressed** regression was introduced — the
  same scope as the project's own suite. A regression that **no test exercises**
  is out of scope for the gate (that is fault-injection / mutation analysis).
- AVERA is a **verification aid whose output is independently re-checkable**, not
  a qualified tool. It supports the SWE-191 *objective*; it does not by itself
  make a project NPR 7150.2-compliant. Tool qualification/assurance remains the
  program's responsibility.
- It does not adjudicate flaky-vs-real — that stays a human call.

## One-line pitch

*"SWE-191 says: demonstrate, with evidence, that your change introduced no
regression. AVERA does exactly that — deterministically, locally, with a
tamper-evident trail — on the test output you already produce."*

---
Sources: [NASA SWEHB SWE-191](https://swehb.nasa.gov/display/SWEHBVD/SWE-191+-+Software+Regression+Testing) · NPR 7150.2 (NASA Software Engineering Requirements).
