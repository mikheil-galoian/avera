#!/usr/bin/env bash
# PostToolUse hook: format + autofix Python files after Edit/Write.
#
# Claude Code passes the tool event as JSON on stdin. We extract the edited
# file path and, if it is a .py file, run `ruff format` and `ruff check --fix`
# on just that file. Non-Python edits are ignored. The hook never blocks the
# edit — it exits 0 even if ruff reports issues it could not auto-fix.

set -euo pipefail

# Resolve the project root (two levels up from .claude/hooks/) so the hook
# works regardless of the process working directory.
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$HOOK_DIR/../.." && pwd)"

# Read the hook payload from stdin and pull out tool_input.file_path.
payload="$(cat)"
file_path="$(
  python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    print("")
    sys.exit(0)
print((data.get("tool_input") or {}).get("file_path") or "")
' <<<"$payload"
)"

# Nothing to do if there is no path, it is not Python, or it no longer exists.
[ -n "$file_path" ] || exit 0
case "$file_path" in
  *.py) ;;
  *) exit 0 ;;
esac
[ -f "$file_path" ] || exit 0

# Use the project venv's ruff (this config lives in main/, so PROJECT_ROOT is
# the main/ dir and the venv is main/.venv). Fall back to whatever is on PATH.
if [ -x "$PROJECT_ROOT/.venv/bin/ruff" ]; then
  RUFF="$PROJECT_ROOT/.venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then
  RUFF="ruff"
else
  echo "ruff-format hook: ruff not found; skipping $file_path" >&2
  exit 0
fi

"$RUFF" format "$file_path" >&2 || true
"$RUFF" check --fix "$file_path" >&2 || true
exit 0
