# AVERA

**AI Change Verification & Evidence Architecture for Safety-Critical Systems**

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://avera-production.up.railway.app)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)

> **AVERA** turns engineering change artifacts into structured, traceable verification evidence — ready for release review, audit, and compliance handoff.

🔗 **Live demo:** [https://avera-production.up.railway.app](https://avera-production.up.railway.app)

---

## The Problem

When a software change touches safety-relevant functions, assembling the evidence trail for release review is manual, fragmented, and hard to audit.

Engineers spend hours collecting test logs, JUnit/xUnit reports, simulation outputs, and requirement traceability data from different tools — then manually formatting it into something a reviewer can trust.

**AVERA automates that assembly.**

---

## What AVERA Does

AVERA ingests your existing engineering artifacts and normalizes them into one structured, traceable evidence pack per change:

| Input | Output |
|-------|--------|
| Verification log CSV | Change-level regression triage |
| JUnit / xUnit XML | Pass/fail delta vs. baseline |
| Simulation CSV | Requirement coverage proof |
| Requirements export | SHA-256 audit log (immutable) |
| Change description | Structured evidence pack for review |

No toolchain changes. No hosted infrastructure required. Fully local and auditable.

---

## Supported Domains & Standards

| Domain | Standard | Status |
|--------|----------|--------|
| Automotive (ADAS, BMS) | ISO 26262 | ✅ Production |
| Railway (signaling, control) | CENELEC EN 50128 | ✅ Production |
| Aviation (avionics) | DO-178C | ✅ Production |
| Medical devices | IEC 62304 / ISO 14971 | ✅ Production |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/averaeng/avera
cd avera
pip install -e ".[demo]"

# Run the live demo shell
./start_demo.sh
# → opens at http://localhost:8501

# Or run analysis directly
PYTHONPATH=src python3 -m avera analyze \
  --project fixtures/bms-fast-charge \
  --out reports
```

Or try the **hosted demo preview** instantly — no install required:
👉 [https://avera-production.up.railway.app](https://avera-production.up.railway.app)
(A read-only preview of the Streamlit shell, including a safe JUnit/JSON upload preview — not full self-service.)

---

## Demo Scenarios

| Scenario | Domain | What It Shows |
|----------|--------|---------------|
| `bms-fast-charge` | Automotive / BMS | Thermal regression evidence, ISO 26262 ASIL-B |
| `adas-pedestrian-detection-regression` | Automotive / ADAS | Simulation delta, requirement coverage proof |
| `fadec-overspeed-regression` | Aviation | DO-178C evidence pack, baseline vs. current |

---

## Core Capabilities

- **Regression triage** — baseline vs. current comparison, pass/fail delta classification
- **Requirement coverage proof** — traceable from change to test to requirement
- **Artifact normalization** — JUnit/xUnit, CSV, simulation outputs, requirements exports
- **Immutable audit log** — SHA-256 hash-chained evidence chain
- **Evidence manifest** — content-addressed `integrity_root` binding the whole artifact set
- **Deterministic gate** — policy-as-data (per-domain); optional evidence-grounded AI assistance that returns "insufficient evidence" when unsupported. AVERA does not decide releases.
- **Evidence pack** — structured output for compliance review and DER/auditor handoff
- **REST API** — `/analyze/path`, `/analyze/inline`, and `/evidence-pack` (full artifact set) for CI/CD integration
- **Adapter SDK** — plug in CANoe/CAPL, custom artifact formats

---

## Architecture

```
src/avera/
├── core/          — change analysis, risk classification
├── compare/       — baseline vs. current comparison
├── classify/      — regression and impact classification
├── adapters/      — artifact format adapters (JUnit, CANoe, CSV)
├── audit/         — immutable SHA-256 audit log
├── coverage/      — requirement coverage checker
├── reporters/     — evidence pack formatters
└── api/           — FastAPI REST endpoint

demo/              — Streamlit interactive shell
fixtures/          — reference scenarios (BMS, ADAS, FADEC)
tests/             — 63 passing tests
```

---

## Installation

```bash
# Core engine
pip install avera

# With demo shell
pip install "avera[demo]"

# With REST API
pip install "avera[api]"

# Full development setup
pip install -e ".[demo,api,dev]"
```

**Requirements:** Python 3.11+

---

## Docker

Run AVERA without installing Python:

```bash
# Pull the latest CLI image
docker pull ghcr.io/tc7kxsszs5-cloud/avera-cli:latest

# Analyze an evidence pack
docker run --rm \
  -v "$PWD/fixtures/bms-fast-charge:/workspace" \
  -v "$PWD/reports:/reports" \
  ghcr.io/tc7kxsszs5-cloud/avera-cli:latest \
  analyze --project /workspace --out /reports \
  --memory /reports/avera-memory.jsonl
```

Multi-arch image (`linux/amd64`, `linux/arm64`). Pinned tags: `latest`, `vX.Y.Z`, `sha-<short>`.

> The evidence pack mount can be read-only (`:ro`) if you also pass `--memory /reports/avera-memory.jsonl` so the engineering-memory ledger lands in the writable reports volume.

---

## REST API

Deployed app: `avera_api.main` (served with `uvicorn avera_api.main:app`).

```bash
# Start the API server
uvicorn avera_api.main:app --host 0.0.0.0 --port 8000

# Assessment report only (backward compatible)
curl -X POST http://localhost:8000/analyze/path \
  -H "Content-Type: application/json" \
  -d '{"project": "fixtures/bms-fast-charge"}'

# Full canonical artifact set (report, graph, traceability, decision, trend,
# workspace pack, evidence manifest + integrity_root, audit log) + gate status
curl -X POST http://localhost:8000/evidence-pack \
  -H "Content-Type: application/json" \
  -d '{"project": "fixtures/bms-fast-charge", "policy": "automotive"}'
```

`/evidence-pack` returns `verdict`, `risk`, `confidence`, the deterministic
`gate_status`, the evidence-manifest `integrity_root`, a decision summary, and
the on-disk paths of every canonical artifact.

---

## GitHub Action

AVERA ships as a reusable GitHub Action. Add one step to your workflow and AVERA runs the full deterministic pipeline on every PR, emits the complete canonical evidence set, and fails the job when a safety-critical regression is detected.

```yaml
# .github/workflows/avera-verify.yml
name: AVERA
on: [pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: tc7kxsszs5-cloud/avera@v1
        with:
          project_path: evidence/my-change
          fail_on_release_blocking: 'true'
```

**Inputs:** `project_path` (required), `output_path`, `policy`, `fail_on_release_blocking`, `fail_on_regression`, `expected_verdict`.
**Outputs:** `verdict`, `risk`, `confidence`, `gate_status`, `report_path`, `manifest_path`, `integrity_root`, `audit_log_path`.

The action writes all 9 canonical artifacts (`avera-report.json`, `avera-report.md`, `avera-evidence-graph.json`, `avera-traceability-index.json`, `avera-decision.json`, `avera-trend-index.json`, `avera-workspace-pack.json`, `avera-evidence-manifest.json`, `avera-audit.jsonl`) into `output_path`.

Full example with PR comments and artifact upload: [`examples/github-action-usage.yml`](examples/github-action-usage.yml). Minimal two-step variant: [`examples/github-action-minimal.yml`](examples/github-action-minimal.yml).

---

## Design Partner Program

We are looking for engineering teams in automotive, aviation, railway, or medical devices who want to run a narrow pilot with their own artifacts.

**The pilot is simple:**
- One software change
- One artifact family you already export
- One 2-week evidence review session

No infrastructure changes. No process disruption.

📩 Contact: [mgaloyan79@gmail.com](mailto:mgaloyan79@gmail.com)
🔗 Demo: [https://avera-production.up.railway.app](https://avera-production.up.railway.app)

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

*AVERA Engineering — engineering truth, preserved as evidence*
