#!/bin/sh
# Thin wrapper around `avera action-run`.
#
# GitHub provides each action input as an INPUT_<NAME> environment variable and
# sets GITHUB_WORKSPACE / GITHUB_OUTPUT. The real logic — emitting all canonical
# artifacts and CI outputs, plus fail conditions — lives in `avera action-run`
# (unit-tested in tests/test_cli_action_run.py).
set -eu

cd "${GITHUB_WORKSPACE:-$PWD}"

# Zero-config mode: two JUnit files in -> verdict + gate out. No evidence pack.
# Triggered when both `baseline` and `current` inputs are provided.
if [ -n "${INPUT_BASELINE:-}" ] && [ -n "${INPUT_CURRENT:-}" ]; then
  CHECK_POLICY_ARG=""
  if [ -n "${INPUT_POLICY:-}" ]; then
    CHECK_POLICY_ARG="--policy ${INPUT_POLICY}"
  fi
  REPORT_ONLY_ARG=""
  case "${INPUT_REPORT_ONLY:-false}" in
    true|TRUE|1|yes) REPORT_ONLY_ARG="--report-only" ;;
  esac
  # shellcheck disable=SC2086
  exec python -m avera check \
    --baseline "${INPUT_BASELINE}" \
    --current "${INPUT_CURRENT}" \
    --github-output "${GITHUB_OUTPUT:-/dev/null}" \
    ${CHECK_POLICY_ARG} ${REPORT_ONLY_ARG}
  # `avera check` exits non-zero when the gate blocks -> fails the CI step.
fi

if [ -z "${INPUT_PROJECT_PATH:-}" ]; then
  echo "AVERA Action error: provide either baseline+current (zero-config) or project_path (full evidence pack)." >&2
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
  --fail-on-gate "${INPUT_FAIL_ON_GATE:-true}" \
  --expected-verdict "${INPUT_EXPECTED_VERDICT:-}" \
  ${POLICY_ARG}
