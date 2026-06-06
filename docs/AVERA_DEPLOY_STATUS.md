# AVERA Deployment Status

**Date:** 7 June 2026
**Status:** Production-usability reference (no deploy files overwritten)

This document records what each deploy artifact is used for, so the build/deploy
surface stays honest. It does not change deploy behaviour.

## What runs where

| Target | Source of truth | Entrypoint | Notes |
|---|---|---|---|
| **Railway demo preview** | `railway.toml` (builder = `NIXPACKS`) → `nixpacks.toml` | `streamlit run demo/app.py` on `$PORT` | The live site is a **demo preview** of the Streamlit shell. Health: `/_stcore/health`, timeout 120s. |
| **CLI image** | `Dockerfile.cli` (multi-stage, Python 3.12) | `ENTRYPOINT ["avera"]` | "Try without installing Python". Also bundles `scripts/avera-action-entrypoint.sh` as `/usr/local/bin/avera-action`. Published as `ghcr.io/.../avera-cli`. |
| **API image** | `Dockerfile.api` (multi-stage, Python 3.12) | `uvicorn avera_api.main:app` on `:8000` | The deployed REST API is **`avera_api.main`**. Endpoints: `/health`, `/analyze/path`, `/analyze/inline`, `/evidence-pack`. Health: `/health`. |
| **GitHub Action** | `action.yml` → `Dockerfile.action` | `action-entrypoint.sh` → `avera action-run` | Emits all 9 canonical artifacts + 8 outputs. Core install only. |
| **Demo container (alt)** | `Dockerfile.demo` (Python 3.11) | `streamlit run demo/app.py` on `:8501` | A self-contained Streamlit container for Render/Fly/Docker. **Not used by the Railway deploy**, which builds via NIXPACKS. |

## Honest naming

- The Railway site is a **demo preview**, not a full self-service product. The
  demo upload path is a **preview** (JUnit XML / verification JSON parsing only;
  see `demo/avera_demo/upload.py`).
- The gate is **deterministic**; AI assistance is **optional and
  evidence-grounded** (`src/avera/copilot/`). AVERA does not decide releases.

## Stale / duplicated / legacy (flagged, not removed)

These are noted for cleanup; this slice does not delete them.

- `Dockerfile.bak` — backup file, untracked. Safe to delete.
- `src/avera/api/app.py` — a **secondary/legacy** API surface (single `/analyze`).
  The deployed API is `avera_api.main`. Keep one; today the deployed one is
  `avera_api.main`.
- `scripts/avera-action-entrypoint.sh` vs `action-entrypoint.sh` — two action
  wrappers. As of the action hardening, `action.yml` uses `Dockerfile.action` +
  `action-entrypoint.sh` (→ `avera action-run`). The older
  `scripts/avera-action-entrypoint.sh` is still bundled by `Dockerfile.cli` for
  interactive use but is no longer the Marketplace Action path.
- `Dockerfile.demo` vs `nixpacks.toml` — two demo build paths. The live Railway
  deploy uses NIXPACKS; `Dockerfile.demo` is the portable-container alternative.

## Local-only / uncommitted (do not deploy from these)

- `railway.toml`, `nixpacks.toml`, `.dockerignore` currently have **local
  uncommitted modifications** (deploy tuning). These are intentionally left out
  of the production-usability commit; review and commit them separately.
- `reports/` is generated output and is not part of any commit.

## Verify locally

```bash
# CLI image
docker build -f Dockerfile.cli -t avera-cli .
docker run --rm -v "$PWD/fixtures/bms-fast-charge:/workspace:ro" avera-cli \
  analyze --project /workspace --out /tmp/reports

# API image
docker build -f Dockerfile.api -t avera-api .
docker run --rm -p 8000:8000 avera-api
# then: curl -s localhost:8000/health

# GitHub Action (logic, no Docker)
PYTHONPATH=src python -m avera action-run \
  --project fixtures/bms-fast-charge --output /tmp/avera-reports \
  --fail-on-release-blocking false
```
