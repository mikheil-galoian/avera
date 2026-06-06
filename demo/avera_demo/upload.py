"""Minimal, safe artifact upload preview for the demo.

Scope is deliberately small and truthful: it accepts only a JUnit/xUnit XML file
or an AVERA verification-results JSON file, normalises it through the existing
adapters/parsers, and returns a read-only *preview* of the parsed verification
content. It never executes uploaded content and never mutates the workspace.

This is a demo preview, not a full ingestion product.
"""

from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from avera.adapters import adapt_junit_xml

ALLOWED_SUFFIXES = {".xml", ".json"}
MAX_PREVIEW_TESTS = 20


def _status_counts(tests: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for test in tests:
        if isinstance(test, dict):
            counter[str(test.get("status", "unknown"))] += 1
    return dict(sorted(counter.items()))


def _preview_from_tests(run_id: Any, stage: Any, tests: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "stage": stage,
        "test_count": len(tests),
        "statuses": _status_counts(tests),
        "tests": tests[:MAX_PREVIEW_TESTS],
    }


def preview_uploaded_evidence(
    filename: str, raw: bytes, *, stage: str = "current"
) -> dict[str, Any]:
    """Parse an uploaded JUnit XML or verification JSON file into a safe preview.

    Returns a dict::

        {"ok": bool, "kind": "junit_xml"|"verification_json"|None,
         "error": str|None, "preview": {...}|None}
    """
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return {
            "ok": False,
            "kind": None,
            "error": f"unsupported file type {suffix or '(none)'!r}; allowed: .xml (JUnit), .json (verification results)",
            "preview": None,
        }

    if not raw or not str(raw).strip():
        return {
            "ok": False,
            "kind": None,
            "error": "uploaded file is empty",
            "preview": None,
        }

    text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes | bytearray) else str(raw)
    if not text.strip():
        return {"ok": False, "kind": None, "error": "uploaded file is empty", "preview": None}

    if suffix == ".xml":
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False, encoding="utf-8") as fh:
                fh.write(text)
                tmp_path = fh.name
            run = adapt_junit_xml(tmp_path, run_id="demo-upload", stage=stage)
        except Exception as exc:  # malformed XML, etc.
            return {"ok": False, "kind": "junit_xml", "error": str(exc), "preview": None}
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
        tests = run.get("tests", []) if isinstance(run, dict) else []
        return {
            "ok": True,
            "kind": "junit_xml",
            "error": None,
            "preview": _preview_from_tests(run.get("runId"), run.get("stage"), tests),
        }

    # JSON verification results
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"ok": False, "kind": "verification_json", "error": f"invalid JSON: {exc}", "preview": None}

    if isinstance(data, dict):
        tests = data.get("tests")
        run_id, stage_val = data.get("runId"), data.get("stage")
    elif isinstance(data, list):
        tests, run_id, stage_val = data, None, None
    else:
        tests, run_id, stage_val = None, None, None

    if not isinstance(tests, list):
        return {
            "ok": False,
            "kind": "verification_json",
            "error": "expected an object with a 'tests' array or a list of test results",
            "preview": None,
        }

    non_objects = sum(1 for t in tests if not isinstance(t, dict))
    if non_objects:
        return {
            "ok": False,
            "kind": "verification_json",
            "error": f"{non_objects} of {len(tests)} test entries are not objects; each test must be a JSON object",
            "preview": None,
        }
    missing_id = sum(1 for t in tests if "id" not in t)
    if tests and missing_id == len(tests):
        return {
            "ok": False,
            "kind": "verification_json",
            "error": "no test entries contain an 'id' field; this does not look like AVERA verification results",
            "preview": None,
        }

    return {
        "ok": True,
        "kind": "verification_json",
        "error": None,
        "preview": _preview_from_tests(run_id, stage_val, tests),
    }
