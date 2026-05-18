# AVERA

**Automotive Verification, Evidence & Risk Architecture**

AVERA is a standalone project direction for a long-term automotive engineering evidence platform.

It is designed to help automotive engineering teams connect:

- engineering changes
- requirements
- tests
- simulations
- signal traces
- risk
- compliance evidence
- production and field feedback

The first product direction is:

`AVERA Change Impact`

This first product should analyze automotive software or systems changes and produce a proof-backed report showing what changed, what requirements are affected, what evidence exists, what risk is present, and what should be verified next.

## Start Here

- [Start, Use, and Show Guide](docs/AVERA_START_USE_SHOW_GUIDE.md)
- [Project Index](docs/AVERA_INDEX.md)
- [Product Brief](docs/AVERA_PRODUCT_BRIEF.md)
- [Architecture](docs/AVERA_ARCHITECTURE.md)
- [MVP Plan](docs/AVERA_MVP_PLAN.md)
- [Roadmap](docs/AVERA_ROADMAP.md)
- [BMS Demo Scenario](docs/AVERA_DEMO_SCENARIO_BMS.md)

## Core Principle

`engineering truth, preserved as evidence`

## Local Prototype

The active implementation is a local Python evidence engine.

Canonical analysis command:

```bash
PYTHONPATH=src python3 -B -m avera analyze \
  --project fixtures/bms-fast-charge \
  --out reports
```

The first demo focuses on BMS fast-charge thermal regression evidence.

Validate an evidence workspace:

```bash
PYTHONPATH=src python3 -B -m avera validate-workspace fixtures/bms-fast-charge
```

Run all local fixtures:

```bash
python3 -B scripts/run_all_fixtures.py
```

Refresh the full canonical demo artifact chain:

```bash
PYTHONPATH=src python3 -B -m avera demo-refresh \
  --project fixtures/bms-fast-charge \
  --report-out reports/fixtures/bms-fast-charge \
  --memory reports/avera-memory.jsonl \
  --traceability-out reports/avera-traceability-index.json \
  --decision-out reports/avera-decision.json \
  --trend-out reports/avera-trend-index.json \
  --pack-out reports/avera-workspace-pack.json
```

Validate a stable artifact contract:

```bash
PYTHONPATH=src python3 -B -m avera validate-artifact \
  --artifact workspace_pack \
  --path reports/avera-workspace-pack.json \
  --bundle
```

Adapt JUnit / xUnit XML into an AVERA verification artifact:

```bash
PYTHONPATH=src python3 -B -m avera adapt-junit \
  --input sample-results.xml \
  --out current_results.json \
  --run-id local-run \
  --stage hil
```

## Demo Shell

A thin local demo shell now lives in:

`demo/app.py`

Recommended runtime path:

- use the project `.venv`
- run `./start_demo.sh` from the project root
- use `scripts/runtime_doctor.py` if the shell path looks unstable

Runtime guidance for this stage of AVERA:

- prefer the repository-managed `.venv` as the supported demo runtime
- treat `./start_demo.sh` as the canonical launch path
- expect the BMS scenario to be the default live-demo path
- expect the ADAS scenario to work through the same launcher, but allow for a
  slower cold-start when Streamlit initializes in the local environment
- if a live ADAS shell startup is slow during a meeting, use the prepared
  static fallback:
  [ADAS showcase](docs/AVERA_ADAS_SHOWCASE.html)

Fastest way to see the demo:

```bash
./start_demo.sh
```

What that launcher does:

- prefers the repository `.venv` when it already exists
- creates `.venv` if needed
- only auto-installs `streamlit` into the project `.venv` when `ALLOW_RUNTIME_INSTALL=1`
- uses the prepared `fixtures/bms-fast-charge` artifacts by default
- can switch directly to the working ADAS scenario through `DEMO_SCENARIO`
- starts the shell on `http://localhost:8501`
- warns when the selected runtime is `Python 3.14`
- enables a safer protobuf fallback for the shell when needed

Optional refresh when you want a fresh artifact chain before launching:

```bash
REFRESH_DEMO=1 ./start_demo.sh
```

Start directly on the working ADAS scenario:

```bash
DEMO_SCENARIO=adas-pedestrian-detection-regression ./start_demo.sh
```

Current launch expectation:

- `./start_demo.sh` is the expected operator path for design-partner demos
- the launcher should be allowed to create or reuse `.venv`
- the first shell view should come up on `http://localhost:8501`
- if the ADAS shell is slow to bind during a cold start, that should currently
  be treated as a local Streamlit/runtime quirk rather than an AVERA kernel
  failure
- the prepared ADAS HTML showcase is the approved fallback for presentation
  continuity

Fallback path when you want to keep the meeting moving:

1. show the live BMS shell
2. switch to the ADAS proof through the prepared static showcase
3. continue the conversation on cross-domain applicability, not on the local
   startup quirk

Manual path if you want to control the runtime yourself:

```bash
python3 -m pip install -e ".[demo]"
PYTHONPATH=src python3 -m streamlit run demo/app.py
```

Check the runtime before a shell/demo session:

```bash
.venv/bin/python scripts/runtime_doctor.py
```

## Verification

The current repeatable verification path is documented here:

- [Verification Guide](docs/AVERA_VERIFICATION_GUIDE.md)

The most practical operator path for starting, checking, using, and showing the
project is here:

- [Start, Use, and Show Guide](docs/AVERA_START_USE_SHOW_GUIDE.md)
