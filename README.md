# AVERA

**A deterministic regression gate for code changes.** Green CI proves nothing *failed* — AVERA proves nothing *regressed*.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://avera-production.up.railway.app)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)

> AVERA compares a baseline test run against the current one and blocks a release only when there is **proof of an introduced regression** — a test that passed before and fails now — with a tamper-evident evidence trail behind the verdict. Local-first, deterministic, **no LLM in the decision**.

---

## 30-second try (zero config)

Install from source (AVERA is not yet on PyPI), then point it at two JUnit files —
verdict + gate out, no project setup, no requirements file:

```bash
git clone https://github.com/tc7kxsszs5-cloud/avera && cd avera
pip install -e .

avera check --baseline main.xml --current pr.xml
#
# AVERA Check
# Verdict:  confirmed_regression
# Introduced failures (1): pkg.tests.test_thing
# Gate [general.v1]: block         (exit 1 — fails the CI step)
```

Works with anything that emits **JUnit / xUnit XML** (pytest, jest, go test, JUnit, …). Add `--json` for machines; the exit code drops into any pipeline.

> **First trial on a noisy repo? Use `--report-only`** (advisory mode): it prints the verdict but always exits 0, so the build is never failed. On a single diff a flaky test that flips pass→fail looks identical to a real regression — advisory mode lets you see what AVERA flags without a false block costing trust. Switch to the hard gate once you trust it. (Action: `report_only: true`.)

---

## Does it actually work? Reproduce it yourself.

AVERA ships a public **blind-replay benchmark** of real regressions. AVERA is given *only* the before/after test results — no hint where the bug is — and must catch it.

```bash
AVERA_PY=python3 ./benchmark/reproduce.sh
# PASS  toolz-f0831e7  -> confirmed_regression / block
```

That case is commit `f0831e7` in the real [`pytoolz/toolz`](https://github.com/pytoolz/toolz) library (later reverted in PR #551). Given only the two result sets, AVERA independently identified the introduced failure (`test_isiterable`, pass→fail), ruled `confirmed_regression`, and returned `gate=block` under every domain policy. See [`benchmark/`](benchmark/) — and add your own case.

---

## The problem it closes

A passing CI run only proves *no expressed test failed* — not that nothing regressed. When prod breaks after a green merge, there is no machine-checkable record of **what** regressed or **why the merge was allowed**; teams reconstruct it by hand after an incident.

With AI agents now generating PRs faster than anyone can review them, "the suite was green" and "that test is just flaky" are exactly how genuine pass→fail regressions slip through. AVERA gives the reviewer a deterministic separator — **proven introduced regression vs everything else** — and a tamper-evident trail behind every gate decision.

---

## What AVERA does **not** do

Stated plainly, because overclaiming is the failure mode this project avoids:

- It does **not** catch a regression that **no test exercises** — that needs fault-injection / mutation analysis, not the gate.
- It does **not** decide **flaky vs real** — that stays a human call.
- It does **not** decide your release — it produces auditable evidence; a human signs off. No LLM in the decision path.
- It is **not** a certified/qualified tool. Its output is designed to be **independently re-checkable** by a human (inspectable manifest, hash-chained audit, re-derivable integrity root).

---

## Supported domains & standards

The same deterministic engine, calibrated per domain via policy-as-data. Verdict assignment is a [proven-total decision table](docs/AVERA_VERDICT_SPECIFICATION.md).

| Domain | Standard | Status |
|--------|----------|--------|
| Software / CI / DevOps | plain pass/fail CI, AI-PR triage | ✅ |
| Automotive (ADAS, BMS) | ISO 26262 | ✅ |
| Aviation (avionics) | DO-178C | ✅ |
| Railway (signaling, control) | CENELEC EN 50128 | ✅ |
| Medical devices | IEC 62304 / ISO 14971 | ✅ |
| Space / flight software | NASA NPR 7150.2 / NASA-STD-8739.8 | ✅ |

Pick a policy with `--policy <name>` (`general`, `automotive`, `aviation`, `railway`, `medical`, `space`, `ai_agent`).

---

## Core capabilities

- **Zero-config check** — `avera check` (two JUnit files → verdict + gate), for plain pass/fail CI.
- **Regression triage** — baseline vs current comparison; fail-closed classification (unknown status → treated as failure, never hidden).
- **Deterministic gate** — policy-as-data per domain; same inputs → same verdict → same evidence root, on any machine.
- **Evidence manifest** — content-addressed `integrity_root` binding the whole artifact set.
- **Immutable audit log** — SHA-256 hash-chained, with an optional keyed (HMAC) tamper-evident mode.
- **Sign-off** — bound to the manifest root; fails closed if verification is skipped.
- **Requirement coverage proof** — traceable from change → test → requirement (regulated domains).
- **REST API & GitHub Action** — for CI/CD integration (see below).

---

## Architecture

```
src/avera/
├── adapters/   — artifact format adapters (JUnit, CSV, simulation, logs, CANoe)
├── compare/    — baseline vs current comparison (fail-closed status taxonomy)
├── classify/   — regression classification + proven-total verdict spec
├── gates/      — deterministic gate, policy-as-data (policies/*.json)
├── evidence/   — content-addressed evidence manifest (integrity_root)
├── audit/      — hash-chained SHA-256 audit log (optional keyed HMAC)
├── signoff/    — sign-off state machine bound to the manifest root
├── domains/    — per-domain profiles (avionics, powertrain, space, …)
├── mutation/   — fault-injection / mutation-based confidence lens
└── api/        — FastAPI REST endpoint

benchmark/      — public blind-replay regression benchmark (reproduce.sh)
fixtures/       — reference scenarios across domains
docs/           — verdict spec, hardening report, dev principles, GTM
tests/          — unit + cross-domain fixtures + exhaustive verdict-spec proof
```

---

## Quick start (full evidence pack)

```bash
git clone https://github.com/tc7kxsszs5-cloud/avera
cd avera
pip install -e ".[demo]"

# Run the live demo shell
./start_demo.sh                      # → http://localhost:8501

# Or analyze a full evidence pack
avera analyze --project fixtures/bms-fast-charge --out reports
```

Or try the **hosted demo preview** — no install:
👉 [https://avera-production.up.railway.app](https://avera-production.up.railway.app)
(Read-only preview of the Streamlit shell — not full self-service.)

---

## GitHub Action

AVERA ships as a reusable GitHub Action, in two modes.

**Zero-config** — gate plain pass/fail CI with two JUnit files, no evidence pack:

```yaml
# .github/workflows/avera-verify.yml
name: AVERA
on: [pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: tc7kxsszs5-cloud/avera@v1
        with:
          baseline: main-junit.xml   # known-good results (e.g. from main)
          current: pr-junit.xml      # this PR's results
          policy: general            # or space / automotive / aviation / …
      # The job fails when the gate blocks (a confirmed regression).
```

Full working example (runs base + PR, then gates): [`examples/github-action-zero-config.yml`](examples/github-action-zero-config.yml). How to produce the baseline in CI (run-both / cached / nightly): [`docs/CI_BASELINE_PATTERN.md`](docs/CI_BASELINE_PATTERN.md). Verified on pytest, jest, and go JUnit output (`tests/test_format_breadth.py`).

**Full evidence pack** — the canonical artifact set for regulated review:

```yaml
      - uses: actions/checkout@v4
      - uses: tc7kxsszs5-cloud/avera@v1
        with:
          project_path: evidence/my-change
          fail_on_release_blocking: 'true'
```

**Inputs:** `project_path` (required), `output_path`, `policy`, `fail_on_release_blocking`, `fail_on_regression`, `expected_verdict`.
**Outputs:** `verdict`, `risk`, `confidence`, `gate_status`, `report_path`, `manifest_path`, `integrity_root`, `audit_log_path`.

Examples: [`examples/github-action-usage.yml`](examples/github-action-usage.yml), [`examples/github-action-minimal.yml`](examples/github-action-minimal.yml).

---

## REST API

Served with `uvicorn avera_api.main:app`.

```bash
uvicorn avera_api.main:app --host 0.0.0.0 --port 8000

# Full canonical artifact set + deterministic gate status + integrity_root
curl -X POST http://localhost:8000/evidence-pack \
  -H "Content-Type: application/json" \
  -d '{"project": "fixtures/bms-fast-charge", "policy": "automotive"}'
```

`/evidence-pack` returns `verdict`, `risk`, `confidence`, the deterministic `gate_status`, the evidence-manifest `integrity_root`, a decision summary, and the on-disk paths of every canonical artifact.

---

## Docker

```bash
docker pull ghcr.io/tc7kxsszs5-cloud/avera-cli:latest
docker run --rm \
  -v "$PWD/fixtures/bms-fast-charge:/workspace" \
  -v "$PWD/reports:/reports" \
  ghcr.io/tc7kxsszs5-cloud/avera-cli:latest \
  analyze --project /workspace --out /reports --memory /reports/avera-memory.jsonl
```

Multi-arch (`linux/amd64`, `linux/arm64`). Pinned tags: `latest`, `vX.Y.Z`, `sha-<short>`.

---

## Design partner program

Looking for engineering teams — running ordinary CI, or in automotive, aviation, railway, medical, or space — who want a narrow pilot with their own artifacts.

**The pilot is simple:** one software change · one artifact family you already export · one 2-week review session. No infrastructure changes, no process disruption.

📩 Contact: [mgaloyan79@gmail.com](mailto:mgaloyan79@gmail.com) · 🔗 Demo: [avera-production.up.railway.app](https://avera-production.up.railway.app)

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

*AVERA Engineering — engineering truth, preserved as evidence.*
