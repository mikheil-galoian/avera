# AVERA Examples

Drop-in workflow files for using AVERA in your own GitHub repository.

| File | Use when |
|------|----------|
| [`github-action-minimal.yml`](./github-action-minimal.yml) | You just want AVERA to block PRs on release-blocking risk. Two steps total. |
| [`github-action-usage.yml`](./github-action-usage.yml) | You want AVERA to comment the verdict on each PR and upload the evidence pack as an artifact. |

To use, copy one of the files into `.github/workflows/` in your repository and adjust `project_path` to point at your evidence pack directory.

See the [AVERA README](../README.md) for the evidence pack contract (baseline/current verification results, `requirements.csv`, `component_map.json`, `change_description.txt`).
