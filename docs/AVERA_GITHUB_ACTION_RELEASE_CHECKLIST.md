# AVERA GitHub Action Release Checklist

## What the action does (v0.1)

The action runs `avera action-run`, which executes the full deterministic
pipeline and:

- **emits all 9 canonical artifacts** into `output_path`:
  `avera-report.json`, `avera-report.md`, `avera-evidence-graph.json`,
  `avera-traceability-index.json`, `avera-decision.json`,
  `avera-trend-index.json`, `avera-workspace-pack.json`,
  `avera-evidence-manifest.json`, `avera-audit.jsonl`
- **sets 8 step outputs**: `verdict`, `risk`, `confidence`, `gate_status`,
  `report_path`, `manifest_path`, `integrity_root`, `audit_log_path`
- **fails the job** on `release_blocking` risk (default), optionally on any
  `confirmed_regression`, and on an `expected_verdict` mismatch

Inputs (underscored): `project_path` (required), `output_path`, `policy`,
`fail_on_release_blocking`, `fail_on_regression`, `expected_verdict`.

## Before creating the release

- `action.yml` declares all 8 outputs and uses `Dockerfile.action`
- `Dockerfile.action` is present (core install, no API extra)
- `action-entrypoint.sh` is a thin wrapper over `avera action-run`
- `.github/workflows/avera-action-smoke.yml` asserts all 9 artifacts + outputs
- `README.md` includes GitHub Action usage with underscored input names
- `pytest tests/test_cli_action_run.py` passes (action logic, no Docker needed)
- local `demo-refresh` smoke path works

## GitHub release steps

1. Push the current branch
2. Open GitHub repository
3. Click `Draft a release`
4. Create tag: `v0.1.0`
5. Release title: `AVERA GitHub Action v0.1.0`
6. Paste the release text from `docs/AVERA_GITHUB_ACTION_V0_1_0_RELEASE.md`
7. Publish release

## After release

- verify `uses: averaeng/avera@v0.1.0` is the example shown in `README.md`
- confirm the action appears correctly on the repository page
- optionally publish to GitHub Marketplace later

## Important scope boundary

This release closes the reusable GitHub Action packaging question.

It does not yet mean:

- organic marketplace distribution is solved
- external adoption is solved
- the action has broad real-world artifact coverage beyond the current stable path
