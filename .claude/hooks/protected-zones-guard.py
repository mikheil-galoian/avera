#!/usr/bin/env python3
"""
AVERA — Protected Zones Guard (PreToolUse hook)
Blocks Edit/Write calls targeting protected paths unless explicitly overridden.
Exit 2 = block, Exit 0 = allow.
"""
import json
import os
import re
import sys

PROTECTED_PATTERNS = [
    r"(^|/)fixtures/",
    r"(^|/)policies/.*\.json$",
    r"(^|/)\.env(\.|$)",
    r"(^|/)expected_outcomes\.json$",
]

OVERRIDE_ENV_VAR = "AVERA_ALLOW_PROTECTED_EDIT"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("protected-zones-guard: bad stdin JSON, allowing", file=sys.stderr)
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    if os.environ.get(OVERRIDE_ENV_VAR) == "1":
        sys.exit(0)

    for pattern in PROTECTED_PATTERNS:
        if re.search(pattern, file_path):
            print(
                f"BLOCKED: '{file_path}' matches protected zone pattern '{pattern}'.\n"
                f"Governed by AGENTS.md Allowed Zones policy (fail-closed rule).\n"
                f"If human-approved, set {OVERRIDE_ENV_VAR}=1 or edit outside Claude Code.",
                file=sys.stderr,
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
