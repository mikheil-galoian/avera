#!/usr/bin/env bash
# Reproduce every AVERA benchmark case in one command.
#
#   ./benchmark/reproduce.sh            # run all cases
#   ./benchmark/reproduce.sh <case-id>  # run one case
#
# Each case ships the two JUnit result sets (baseline = good code, current = bad
# code) and the expected AVERA verdict. We run `avera check` on them — AVERA gets
# ONLY the result diff, no hint where the bug is — and compare to case.json.
# Exit 0 only if every case matches its expected verdict + gate.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${AVERA_PY:-python3}"
CASES_DIR="$ROOT/benchmark/cases"
FILTER="${1:-}"
fail=0

for dir in "$CASES_DIR"/*/; do
  id="$(basename "$dir")"
  [ -n "$FILTER" ] && [ "$FILTER" != "$id" ] && continue
  exp_verdict=$(PYTHONPATH="$ROOT/src" "$PY" -c "import json;print(json.load(open('$dir/case.json'))['expected']['verdict'])")
  exp_gate=$(PYTHONPATH="$ROOT/src" "$PY" -c "import json;print(json.load(open('$dir/case.json'))['expected']['gate_status'])")
  got=$(PYTHONPATH="$ROOT/src" "$PY" -m avera check \
        --baseline "$dir/baseline.xml" --current "$dir/current.xml" --json)
  got_verdict=$(echo "$got" | "$PY" -c "import sys,json;print(json.load(sys.stdin)['verdict'])")
  got_gate=$(echo "$got" | "$PY" -c "import sys,json;print(json.load(sys.stdin)['gate_status'])")
  if [ "$got_verdict" = "$exp_verdict" ] && [ "$got_gate" = "$exp_gate" ]; then
    echo "PASS  $id  -> $got_verdict / $got_gate"
  else
    echo "FAIL  $id  expected $exp_verdict/$exp_gate, got $got_verdict/$got_gate"
    fail=1
  fi
done

exit $fail
