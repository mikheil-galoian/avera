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

Or try the **hosted demo** instantly — no install required:
👉 [https://avera-production.up.railway.app](https://avera-production.up.railway.app)

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
- **Evidence pack** — structured output for compliance review and DER/auditor handoff
- **REST API** — `POST /analyze` endpoint for CI/CD integration
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

## REST API

```bash
# Start the API server
avera-api

# Analyze a change
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"project_path": "fixtures/bms-fast-charge"}'
```

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
