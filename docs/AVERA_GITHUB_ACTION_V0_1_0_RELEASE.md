# AVERA GitHub Action v0.1.0

## Title

`AVERA GitHub Action v0.1.0`

## Release text

AVERA now ships with a reusable Docker-based GitHub Action surface for CI-shaped evidence verification runs.

### What is included

- `action.yml` reusable action definition
- `Dockerfile.action` containerized action runtime
- `action-entrypoint.sh` stable action entrypoint
- `.github/workflows/avera-action-smoke.yml` local smoke workflow for the action
- `README.md` GitHub Action usage section

### What the action does

The first AVERA GitHub Action release runs the existing `demo-refresh` artifact chain over a local fixture or workspace and produces:

- `avera-report.json`
- `avera-report.md`
- `avera-evidence-graph.json`
- `traceability index`
- `decision artifact`
- `trend artifact`
- `workspace pack`

### Primary use case

This release gives AVERA a reusable CI entrypoint so teams can run a proof-oriented evidence pass inside GitHub Actions without custom local setup.

### Example

```yaml
jobs:
  avera:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run AVERA
        id: avera
        uses: averaeng/avera@v0.1.0
        with:
          project-path: fixtures/bms-fast-charge
          output-dir: reports/action
```

### Notes

- This is the first reusable Action packaging layer for AVERA.
- It is intentionally narrow and stable.
- It sits on top of the existing local AVERA CLI path rather than introducing a parallel execution model.

## Suggested tag

`v0.1.0`
