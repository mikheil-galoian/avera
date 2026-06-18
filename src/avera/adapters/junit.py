"""Adapt JUnit / xUnit XML test artifacts into AVERA verification results.

Supported variations
--------------------
- ``<testsuites>`` wrapper around one or more ``<testsuite>`` elements
- Bare ``<testsuite>`` root (single-suite reports)
- Nested ``<testsuite>`` elements (e.g. Surefire, pytest-junit)
- ``<properties>`` / ``<property>`` on both suite and testcase levels
- ``<system-out>`` / ``<system-err>`` captured output appended to evidence
- Non-numeric ``time`` attributes handled gracefully
- Missing ``name`` / ``classname`` attributes defaulted safely

Batch support
-------------
:func:`adapt_junit_xml_batch` accepts an iterable of paths and merges all
test cases into a single AVERA verification-run dict.  When the same
``test_id`` appears in multiple files, the worst-status entry wins (error >
failed > inconclusive > skipped > passed) and metrics are merged (later
file's values override earlier ones).

Output schema
-------------
::

    {
        "runId":  str,
        "stage":  str,
        "tests":  list[dict],
        "metadata": dict,
    }

Each test dict::

    {
        "id":        str,           # classname.name or just name
        "component": str,           # classname or suite name
        "status":    str,           # passed | failed | error | skipped
        "metrics":   dict,          # duration_s + numeric <property> values
        "evidence":  str,           # failure / error message + system-out/err
        "metadata":  dict,          # suite, classname, property strings, etc.
    }
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

from avera.compare.baseline_comparator import status_severity


def _merge_into(merged: dict[str, dict[str, Any]], test: dict[str, Any]) -> None:
    """Merge *test* into *merged* by id, worst-status-wins (fail-closed).

    Used for duplicate test ids both within a single file (a retried test
    emitting fail-then-pass) and across files in a batch.
    """
    tid = test["id"]
    existing = merged.get(tid)
    if existing is None:
        merged[tid] = test
        return
    if status_severity(test["status"]) > status_severity(existing["status"]):
        existing["status"] = test["status"]
        existing["evidence"] = test["evidence"]
    existing["metrics"].update(test["metrics"])


# ---------------------------------------------------------------------------
# Public API — single file
# ---------------------------------------------------------------------------

def adapt_junit_xml(
    path: str | Path,
    *,
    run_id: str,
    stage: str,
) -> dict[str, Any]:
    """Convert a JUnit / xUnit XML file into an AVERA verification-run dict.

    Parameters
    ----------
    path:
        Path to the ``.xml`` file.
    run_id:
        AVERA run identifier string.
    stage:
        ``"baseline"`` or ``"current"``.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the XML is malformed or not a recognisable JUnit / xUnit format.
    """
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"JUnit XML report not found: {source}")

    try:
        root = ET.fromstring(source.read_text(encoding="utf-8", errors="replace"))
    except ET.ParseError as exc:
        raise ValueError(f"JUnit XML parse error in {source}: {exc}") from exc

    merged: dict[str, dict[str, Any]] = {}
    suites = _collect_suites(root)
    for suite in suites:
        suite_name = suite.attrib.get("name", "").strip()
        suite_props = _parse_properties(suite)
        for testcase in suite.findall(".//testcase"):
            _merge_into(merged, _adapt_testcase(testcase, suite_name, suite_props))
    tests = list(merged.values())

    return {
        "runId": run_id,
        "stage": stage,
        "tests": tests,
        "metadata": {
            "adapter": "junit_xml.v1",
            "source_format": "junit_xml",
            "source_path": str(source),
            "suite_count": len(suites),
            "test_count": len(tests),
        },
    }


# ---------------------------------------------------------------------------
# Public API — batch (multiple XML files → one verification-run)
# ---------------------------------------------------------------------------

def adapt_junit_xml_batch(
    paths: Iterable[str | Path],
    *,
    run_id: str,
    stage: str,
) -> dict[str, Any]:
    """Merge multiple JUnit XML reports into a single AVERA verification-run.

    Duplicates (same ``id``) are resolved by worst-status-wins; metrics are
    merged (later file overrides earlier for the same key).

    Parameters
    ----------
    paths:
        Iterable of paths to ``.xml`` files.
    run_id:
        AVERA run identifier string.
    stage:
        ``"baseline"`` or ``"current"``.

    Raises
    ------
    ValueError
        If *paths* is empty or all files are empty / malformed.
    FileNotFoundError
        If any individual path does not exist.
    """
    path_list = [Path(p) for p in paths]
    if not path_list:
        raise ValueError("adapt_junit_xml_batch: no paths provided")

    merged: dict[str, dict[str, Any]] = {}
    total_suites = 0
    source_paths: list[str] = []

    for source in path_list:
        single = adapt_junit_xml(source, run_id=run_id, stage=stage)
        total_suites += single["metadata"]["suite_count"]
        source_paths.append(str(source))
        for test in single["tests"]:
            _merge_into(merged, test)

    return {
        "runId": run_id,
        "stage": stage,
        "tests": list(merged.values()),
        "metadata": {
            "adapter": "junit_xml.v1",
            "source_format": "junit_xml",
            "source_paths": source_paths,
            "file_count": len(path_list),
            "suite_count": total_suites,
            "test_count": len(merged),
        },
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _collect_suites(root: ET.Element) -> list[ET.Element]:
    """Return the list of ``<testsuite>`` elements to iterate."""
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
        return suites if suites else [root]
    if root.tag == "testsuite":
        return [root]
    # Unknown root — treat as a single pseudo-suite
    return [root]


def _parse_properties(node: ET.Element) -> dict[str, str]:
    """Return ``{name: value}`` dict from ``<properties><property .../></properties>``."""
    props: dict[str, str] = {}
    container = node.find("properties")
    if container is None:
        return props
    for prop in container.findall("property"):
        name = (prop.attrib.get("name") or "").strip()
        value = (prop.attrib.get("value") or prop.text or "").strip()
        if name:
            props[name] = value
    return props


def _adapt_testcase(
    testcase: ET.Element,
    suite_name: str,
    suite_props: dict[str, str],
) -> dict[str, Any]:
    """Parse a single ``<testcase>`` element into an AVERA test dict."""

    classname = testcase.attrib.get("classname", "").strip()
    name = testcase.attrib.get("name", "").strip() or "unnamed_testcase"
    duration_raw = testcase.attrib.get("time", "").strip()

    test_id = ".".join(part for part in (classname, name) if part) or name
    component = classname or suite_name or "external_test_suite"

    # --- status + primary evidence ---
    status = "passed"
    evidence_parts: list[str] = []
    metadata: dict[str, Any] = {}
    metrics: dict[str, Any] = {}

    if suite_name:
        metadata["suite"] = suite_name
    if classname:
        metadata["classname"] = classname
    metadata["name"] = name

    # Duration
    if duration_raw:
        try:
            metrics["duration_s"] = float(duration_raw)
        except ValueError:
            metadata["duration_raw"] = duration_raw

    # Failure / error / skipped
    failure = testcase.find("failure")
    error = testcase.find("error")
    skipped = testcase.find("skipped")

    if failure is not None:
        status = "failed"
        ev = _node_evidence(failure)
        if ev:
            evidence_parts.append(ev)
        ftype = failure.attrib.get("type", "").strip()
        fmsg = failure.attrib.get("message", "").strip()
        if ftype:
            metadata["failure_type"] = ftype
        if fmsg:
            metadata["failure_message"] = fmsg
    elif error is not None:
        status = "error"
        ev = _node_evidence(error)
        if ev:
            evidence_parts.append(ev)
        etype = error.attrib.get("type", "").strip()
        emsg = error.attrib.get("message", "").strip()
        if etype:
            metadata["error_type"] = etype
        if emsg:
            metadata["error_message"] = emsg
    elif skipped is not None:
        status = "skipped"
        smsg = skipped.attrib.get("message", "").strip()
        if smsg:
            metadata["skipped_message"] = smsg
            evidence_parts.append(smsg)

    # <system-out> / <system-err> → appended to evidence
    for tag in ("system-out", "system-err"):
        elem = testcase.find(tag)
        if elem is not None:
            text = (elem.text or "").strip()
            if text:
                evidence_parts.append(f"[{tag}]\n{text}")

    # <properties> on the testcase itself
    tc_props = _parse_properties(testcase)
    _absorb_props(tc_props, metrics, metadata, prefix="prop_")

    # Suite-level properties → always stored as metadata strings (build info,
    # environment tags — not measurement values of this specific test case).
    for sp_name, sp_raw in suite_props.items():
        metadata[f"suite_prop_{sp_name}"] = sp_raw

    return {
        "id": test_id,
        "component": component,
        "status": status,
        "metrics": metrics,
        "evidence": "\n".join(evidence_parts),
        "metadata": {k: v for k, v in metadata.items() if v not in (None, "")},
    }


def _absorb_props(
    props: dict[str, str],
    metrics: dict[str, Any],
    metadata: dict[str, Any],
    prefix: str,
) -> None:
    """Put numeric property values into *metrics*, strings into *metadata*."""
    for name, raw in props.items():
        coerced = _coerce(raw)
        if isinstance(coerced, (int, float)):
            metrics[name] = coerced
        else:
            metadata[f"{prefix}{name}"] = raw


def _node_evidence(node: ET.Element) -> str:
    parts: list[str] = []
    message = node.attrib.get("message", "").strip()
    if message:
        parts.append(message)
    text = (node.text or "").strip()
    if text:
        parts.append(text)
    return "\n".join(parts)


def _coerce(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if any(c in raw for c in (".", "e", "E")):
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


# ---------------------------------------------------------------------------
# SDK-compatible class wrapper
# ---------------------------------------------------------------------------

from avera.adapters.interface import VerificationAdapter as _VA


class JUnitXmlAdapter(_VA):
    """VerificationAdapter for JUnit / xUnit XML reports.

    Dispatches to :func:`adapt_junit_xml` for single files and
    :func:`adapt_junit_xml_batch` for multiple files via :meth:`adapt_batch`.
    """

    name = "junit_xml"
    version = "1.1.0"
    source_format = "junit_xml"
    file_extensions = (".xml",)

    def adapt(self, path: Path, *, run_id: str, stage: str) -> dict[str, Any]:
        return adapt_junit_xml(path, run_id=run_id, stage=stage)

    def adapt_batch(
        self,
        paths: Iterable[str | Path],
        *,
        run_id: str,
        stage: str,
    ) -> dict[str, Any]:
        """Merge multiple JUnit XML files into one verification-run dict."""
        return adapt_junit_xml_batch(paths, run_id=run_id, stage=stage)

    def can_handle(self, path: Path) -> bool:
        if path.suffix.lower() != ".xml":
            return False
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:512]
            return "testsuite" in text.lower() or "testcase" in text.lower()
        except OSError:
            return False

    @property
    def metadata(self) -> dict[str, str]:
        return {
            "adapter": "junit_xml.1_1_0",
            "adapter_name": "junit_xml",
            "adapter_version": "1.1.0",
            "source_format": "junit_xml",
        }

    def __repr__(self) -> str:
        return "JUnitXmlAdapter(name='junit_xml', version='1.1.0')"
