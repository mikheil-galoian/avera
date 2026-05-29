# AVERA GitHub Action Release Checklist

## Before creating the release

- `action.yml` is present
- `Dockerfile.action` is present
- `action-entrypoint.sh` is present
- `.github/workflows/avera-action-smoke.yml` is present
- `README.md` includes GitHub Action usage
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
