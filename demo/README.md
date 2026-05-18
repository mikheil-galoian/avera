# AVERA Demo Shell

The demo is now organized as a small local package instead of a single large
Streamlit file.

## Layout

- `app.py` - tiny Streamlit entrypoint
- `avera_demo/app.py` - bootstraps the shell
- `avera_demo/artifacts.py` - scenario resolution and artifact loading
- `avera_demo/models.py` - local data structures for the shell
- `avera_demo/runner.py` - optional local analyze action
- `avera_demo/views.py` - Streamlit rendering for the MVP surface

## MVP Focus

This shell stays intentionally local-first and artifact-driven:

- loads prepared fixture and report artifacts from disk
- highlights workspace readiness and missing evidence
- separates overview, evidence, traceability, workspace, and raw artifact views
- preserves the existing local `analyze` action without moving product logic into the UI

## Run

Fastest path from the project root:

```bash
./start_demo.sh
```

Recommended diagnostic path before a live showing:

```bash
.venv/bin/python scripts/runtime_doctor.py
```

Start directly on the working ADAS scenario:

```bash
DEMO_SCENARIO=adas-pedestrian-detection-regression ./start_demo.sh
```

Manual path if you already have the optional demo dependency:

```bash
PYTHONPATH=src streamlit run demo/app.py
```

Runtime note:

- the project `.venv` is the supported demo path
- `Python 3.14` is acceptable for core/test work, but the Streamlit shell may cold-start slowly there
- when the shell path is unstable, the static ADAS presentation fallback is:
  - `docs/AVERA_ADAS_SHOWCASE.html`

The default scenario remains:

`fixtures/bms-fast-charge`

Also available as a working second domain:

`fixtures/adas-pedestrian-detection-regression`
