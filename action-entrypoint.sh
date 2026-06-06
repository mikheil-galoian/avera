#!/bin/sh
# Thin wrapper around `avera action-run`.
#
# GitHub provides each action input as an INPUT_<NAME> environment variable and
# sets GITHUB_WORKSPACE / GITHUB_OUTPUT. The real logic — emitting all canonical
# artifacts and CI outputs, plus fail conditions — lives in `avera action-run`
# (unit-tested in tests/test_cli_action_run.py).
set -eu

cd "${GITHUB_WORKSPACE:-$PWD}"

if [ -z "${INPUT_PROJECT_PATH:-}" ]; then
  echo "AVERA Action error: project_path input is required." >&2
  exit 2
fi

POLICY_ARG=""
if [ -n "${INPUT_POLICY:-}" ]; then
  POLICY_ARG="--policy ${INPUT_POLICY}"
fi

# shellcheck disable=SC2086
exec python -m avera action-run \
  --project "${INPUT_PROJECT_PATH}" \
  --output "${INPUT_OUTPUT_PATH:-avera-reports}" \
  --fail-on-release-blocking "${INPUT_FAIL_ON_RELEASE_BLOCKING:-true}" \
  --fail-on-regression "${INPUT_FAIL_ON_REGRESSION:-false}" \
  --expected-verdict "${INPUT_EXPECTED_VERDICT:-}" \
  ${POLICY_ARG}
