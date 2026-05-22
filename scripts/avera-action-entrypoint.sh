#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# AVERA GitHub Marketplace Action — entrypoint wrapper
#
# Runs `avera analyze` against a given evidence pack, parses the
# resulting report, exports GitHub Action outputs, writes a
# step summary, and exits non-zero based on the configured
# failure policy.
#
# Invocation order for each input:
#   1. INPUT_<NAME>  — set by GitHub Actions from `with:` fields
#   2. positional arg — fallback for raw `docker run` invocation
# ─────────────────────────────────────────────────────────────
set -euo pipefail

PROJECT_PATH="${INPUT_PROJECT_PATH:-${1:-}}"
OUTPUT_PATH="${INPUT_OUTPUT_PATH:-${2:-avera-reports}}"
FAIL_ON_RELEASE_BLOCKING="${INPUT_FAIL_ON_RELEASE_BLOCKING:-${3:-true}}"
FAIL_ON_REGRESSION="${INPUT_FAIL_ON_REGRESSION:-${4:-false}}"
EXPECTED_VERDICT="${INPUT_EXPECTED_VERDICT:-${5:-}}"

# ── Validate inputs ──────────────────────────────────────────
if [ -z "$PROJECT_PATH" ]; then
  echo "::error::AVERA: project_path is required"
  exit 1
fi

if [ ! -d "$PROJECT_PATH" ]; then
  echo "::error::AVERA: project_path does not exist: $PROJECT_PATH"
  exit 1
fi

mkdir -p "$OUTPUT_PATH"

echo "──────────────────────────────────────────"
echo "AVERA Change Verification"
echo "──────────────────────────────────────────"
echo "Project:           $PROJECT_PATH"
echo "Output:            $OUTPUT_PATH"
echo "Fail on blocking:  $FAIL_ON_RELEASE_BLOCKING"
echo "Fail on regress:   $FAIL_ON_REGRESSION"
if [ -n "$EXPECTED_VERDICT" ]; then
  echo "Expected verdict:  $EXPECTED_VERDICT"
fi
echo "──────────────────────────────────────────"

# ── Run analysis ─────────────────────────────────────────────
# Pin --memory to the output directory so the analysis works
# regardless of whether the evidence pack mount is read-only.
avera analyze \
  --project "$PROJECT_PATH" \
  --out "$OUTPUT_PATH" \
  --memory "$OUTPUT_PATH/avera-memory.jsonl"

REPORT_JSON="$OUTPUT_PATH/avera-report.json"
if [ ! -f "$REPORT_JSON" ]; then
  echo "::error::AVERA: report not produced at $REPORT_JSON"
  exit 1
fi

# ── Parse report ─────────────────────────────────────────────
read -r VERDICT RISK CONFIDENCE < <(
  python3 - "$REPORT_JSON" <<'PY'
import json, sys
report = json.load(open(sys.argv[1]))
print(report.get("verdict", "unknown"),
      report.get("risk", "unknown"),
      report.get("confidence", "unknown"))
PY
)

echo "──────────────────────────────────────────"
echo "VERDICT:     $VERDICT"
echo "RISK:        $RISK"
echo "CONFIDENCE:  $CONFIDENCE"
echo "──────────────────────────────────────────"

# ── Export GitHub Action outputs ─────────────────────────────
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "verdict=$VERDICT"
    echo "risk=$RISK"
    echo "confidence=$CONFIDENCE"
    echo "report_path=$REPORT_JSON"
  } >> "$GITHUB_OUTPUT"
fi

# ── Write step summary ───────────────────────────────────────
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "## AVERA Change Verification"
    echo ""
    echo "| Field      | Value           |"
    echo "|------------|-----------------|"
    echo "| Verdict    | \`$VERDICT\`    |"
    echo "| Risk       | \`$RISK\`       |"
    echo "| Confidence | \`$CONFIDENCE\` |"
    echo ""
    echo "**Project:** \`$PROJECT_PATH\`"
    echo ""
    echo "Report artifact: \`$REPORT_JSON\`"
  } >> "$GITHUB_STEP_SUMMARY"
fi

# ── Expected-verdict assertion ───────────────────────────────
if [ -n "$EXPECTED_VERDICT" ] && [ "$VERDICT" != "$EXPECTED_VERDICT" ]; then
  echo "::error::AVERA: expected verdict '$EXPECTED_VERDICT' but got '$VERDICT'"
  exit 1
fi

# ── Failure policy ───────────────────────────────────────────
if [ "$RISK" = "release_blocking" ] && [ "$FAIL_ON_RELEASE_BLOCKING" = "true" ]; then
  echo "::error::AVERA: release-blocking risk detected — blocking the workflow"
  exit 1
fi

if [ "$VERDICT" = "confirmed_regression" ] && [ "$FAIL_ON_REGRESSION" = "true" ]; then
  echo "::error::AVERA: confirmed_regression and fail_on_regression=true"
  exit 1
fi

echo "AVERA gate passed: $VERDICT / $RISK / $CONFIDENCE"
