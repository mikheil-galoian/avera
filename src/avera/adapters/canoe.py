"""Adapt Vector CANoe test-report artifacts into AVERA verification results.

Supported source formats
------------------------
1. **CANoe XML report** (``*.xml``) — the native test-execution report written
   by CANoe's Test Execution Environment (TEF).  Root element is
   ``<TestReport>`` or ``<TEF_Report>``.  Test cases appear as
   ``<TestCase>`` elements with ``Verdict``, ``Name``, and optional
   ``<Measurement>`` / ``<Signal>`` sub-elements.

2. **Vector ASC log** (``*.asc``) — the text-based CAN bus log written by
   Vector tools (CANalyzer, CANoe).  Each line starts with a timestamp and
   contains a CAN frame or an event.  AVERA reads test-result annotations
   embedded as diagnostic UDS responses or as comment lines matching the
   pattern ``// AVERA: <test_id> <status> [metric=value ...]``.

Both formats are common in automotive HIL/SIL validation environments
(ISO 26262, ASPICE) where CANoe drives the test bench.

Output
------
Both ``adapt_canoe_xml`` and ``adapt_canoe_asc`` return a standard AVERA
verification-run dict::

    {
        "runId":  str,
        "stage":  str,
        "tests":  list[dict],        # list of AVERA test-result dicts
        "metadata": dict,
    }

Class interface
---------------
``CANoeAdapter`` implements the Adapter SDK interface (``can_handle`` +
``adapt``) and is registered by :class:`avera.adapters.interface.AdapterRegistry`.
It dispatches to the correct underlying function based on file extension.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# CANoe XML report adapter
# ---------------------------------------------------------------------------

# Verdict strings used by CANoe TEF → normalised AVERA status
_CANOE_VERDICT_MAP: dict[str, str] = {
    "passed":   "passed",
    "pass":     "passed",
    "ok":       "passed",
    "failed":   "failed",
    "fail":     "failed",
    "error":    "error",
    "notexec":  "skipped",
    "not executed": "skipped",
    "skipped":  "skipped",
    "inconclusive": "inconclusive",
}


def adapt_canoe_xml(
    path: str | Path,
    *,
    run_id: str,
    stage: str,
) -> dict[str, Any]:
    """Convert a CANoe XML test report into an AVERA verification-run dict.

    Supports both ``<TestReport>`` (CANoe ≤ 16) and ``<TEF_Report>``
    (CANoe 17+) root elements.  Nested ``<TestGroup>`` elements are
    flattened; their names are prepended to child test-case IDs.

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
        If the file is not a recognised CANoe XML format.
    """

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"CANoe XML report not found: {source}")

    try:
        root = ET.fromstring(source.read_text(encoding="utf-8", errors="replace"))
    except ET.ParseError as exc:
        raise ValueError(f"CANoe XML parse error in {source}: {exc}") from exc

    if root.tag not in {"TestReport", "TEF_Report", "testReport", "tef_report"}:
        # Tolerate unknown roots but warn via metadata
        format_note = f"unrecognised_root:{root.tag}"
    else:
        format_note = root.tag

    tests: list[dict[str, Any]] = []
    _collect_canoe_tests(root, tests, group_prefix="")

    if not tests:
        raise ValueError(f"CANoe XML report contains no test cases: {source}")

    # Attempt to read report-level metadata
    report_meta: dict[str, str] = {}
    for tag in ("DUT", "TestObject", "TestEnvironment", "Version"):
        elem = root.find(f".//{tag}")
        if elem is not None and (elem.text or "").strip():
            report_meta[tag.lower()] = elem.text.strip()

    return {
        "runId": run_id,
        "stage": stage,
        "tests": tests,
        "metadata": {
            "adapter": "canoe_xml.v1",
            "source_format": "canoe_xml",
            "source_path": str(source),
            "xml_root": format_note,
            "test_count": len(tests),
            **report_meta,
        },
    }


def _collect_canoe_tests(
    node: ET.Element,
    tests: list[dict[str, Any]],
    group_prefix: str,
) -> None:
    """Recursively collect test cases from a CANoe XML subtree."""

    for child in node:
        tag = child.tag

        # Test groups — recurse with updated prefix
        if tag in {"TestGroup", "testGroup", "TestSuite", "testSuite"}:
            group_name = (
                child.attrib.get("Name")
                or child.attrib.get("name")
                or child.attrib.get("title")
                or tag
            ).strip()
            new_prefix = f"{group_prefix}{group_name}." if group_prefix else f"{group_name}."
            _collect_canoe_tests(child, tests, new_prefix)
            continue

        # Test cases
        if tag in {"TestCase", "testCase", "TestCaseResult"}:
            tests.append(_parse_canoe_testcase(child, group_prefix))
            continue

        # Recurse into other container elements
        _collect_canoe_tests(child, tests, group_prefix)


def _parse_canoe_testcase(
    node: ET.Element,
    group_prefix: str,
) -> dict[str, Any]:
    """Parse a single CANoe ``<TestCase>`` element."""

    # Name / ID
    name = (
        node.attrib.get("Name")
        or node.attrib.get("name")
        or node.attrib.get("title")
        or (node.find("Name") or node.find("name") or ET.Element("x")).text
        or "unnamed_testcase"
    ).strip()
    test_id = f"{group_prefix}{name}" if group_prefix else name

    # Verdict
    raw_verdict = (
        node.attrib.get("Verdict")
        or node.attrib.get("verdict")
        or node.attrib.get("result")
        or (node.find("Verdict") or node.find("verdict") or ET.Element("x")).text
        or "inconclusive"
    ).strip().lower()
    status = _CANOE_VERDICT_MAP.get(raw_verdict, "inconclusive")

    # Component — infer from group_prefix or DUT attribute
    component = (
        node.attrib.get("Component")
        or node.attrib.get("component")
        or node.attrib.get("Module")
        or (group_prefix.rstrip(".").split(".")[-1] if group_prefix else "")
        or "CANoe"
    ).strip()

    # Metrics from <Measurement> and <Signal> children
    metrics: dict[str, Any] = {}
    for meas in node.findall(".//Measurement") + node.findall(".//Signal"):
        m_name = (meas.attrib.get("Name") or meas.attrib.get("name") or "").strip()
        m_value = (meas.attrib.get("Value") or meas.attrib.get("value") or (meas.text or "")).strip()
        if m_name and m_value:
            metrics[m_name] = _coerce(m_value)

    # Duration
    duration_str = node.attrib.get("Duration") or node.attrib.get("duration") or ""
    if duration_str:
        try:
            metrics["duration_s"] = float(duration_str)
        except ValueError:
            pass

    # Evidence from <Description>, <ErrorText>, <Comment>
    evidence_parts: list[str] = []
    for tag in ("Description", "ErrorText", "Comment", "FailureReason"):
        elem = node.find(tag)
        if elem is not None and (elem.text or "").strip():
            evidence_parts.append(elem.text.strip())
    evidence = "\n".join(evidence_parts)

    # Metadata
    metadata: dict[str, Any] = {
        "adapter": "canoe_xml.v1",
        "raw_verdict": raw_verdict,
    }
    for attr in ("Timestamp", "timestamp", "StartTime", "EndTime"):
        val = node.attrib.get(attr, "").strip()
        if val:
            metadata[attr.lower()] = val

    return {
        "id": test_id,
        "component": component,
        "status": status,
        "metrics": metrics,
        "evidence": evidence,
        "metadata": {k: v for k, v in metadata.items() if v not in (None, "")},
    }


# ---------------------------------------------------------------------------
# Vector ASC log adapter
# ---------------------------------------------------------------------------

# Matches AVERA annotation comments in ASC logs:
# // AVERA: BMS-HIL-FASTCHARGE-07 passed max_cell_temp_c=48.3
# // AVERA: BMS-HIL-FASTCHARGE-08 failed
_AVERA_ANNOTATION = re.compile(
    r"//\s*AVERA:\s*(?P<test_id>\S+)\s+(?P<status>passed|failed|error|skipped|inconclusive)"
    r"(?P<metrics>.*)?$",
    re.IGNORECASE,
)

# Matches metric key=value pairs at end of annotation line
_METRIC_KV = re.compile(r"(\w[\w./-]*)\s*=\s*([^\s,;]+)")

# Matches a UDS positive response for ReadDataByIdentifier (service 0x22 → 0x62)
# that encodes a test verdict via a DID in the 0xF200..0xF2FF range.
# Format: timestamp channel frame_id  d  len  b0 b1 b2 b3 ...
# b0=0x62, b1-b2=DID, b3=verdict (0=pass, 1=fail, 2=error, 3=skip)
_UDS_RDBI_LINE = re.compile(
    r"^\s*[\d.]+\s+\d+\s+[\dA-Fa-f]+\s+"   # timestamp  channel  frame_id
    r"(?:\w+\s+)?"                            # optional direction (Rx / Tx)
    r"d\s+\d+\s+"                            # d  dlc
    r"62\s+F2\s+(?P<did_lo>[0-9A-Fa-f]{2})\s+(?P<verdict_byte>[0-3])\b"
)

_UDS_VERDICT_MAP = {"0": "passed", "1": "failed", "2": "error", "3": "skipped"}


def adapt_canoe_asc(
    path: str | Path,
    *,
    run_id: str,
    stage: str,
) -> dict[str, Any]:
    """Convert a Vector ASC log file into an AVERA verification-run dict.

    Reads AVERA-annotated comment lines (``// AVERA: <id> <status> [k=v ...]``)
    and optionally UDS RDBI responses (service 0x62, DID 0xF2xx) that encode
    binary pass/fail results per test identifier.

    Parameters
    ----------
    path:
        Path to the ``.asc`` file.
    run_id:
        AVERA run identifier string.
    stage:
        ``"baseline"`` or ``"current"``.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If no AVERA test results are found in the log.
    """

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"ASC log not found: {source}")

    tests: dict[str, dict[str, Any]] = {}
    line_count = 0
    annotation_count = 0
    uds_count = 0

    for raw_line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        line_count += 1
        line = raw_line.strip()

        # AVERA annotation comment
        m = _AVERA_ANNOTATION.search(line)
        if m:
            annotation_count += 1
            test_id = m.group("test_id")
            status = m.group("status").lower()
            metrics: dict[str, Any] = {}
            for kv_m in _METRIC_KV.finditer(m.group("metrics") or ""):
                metrics[kv_m.group(1)] = _coerce(kv_m.group(2))
            _merge_asc_result(tests, test_id, status, metrics, line_count)
            continue

        # UDS RDBI response
        u = _UDS_RDBI_LINE.match(line)
        if u:
            uds_count += 1
            did_lo = int(u.group("did_lo"), 16)
            test_id = f"DID_F2{did_lo:02X}"
            status = _UDS_VERDICT_MAP.get(u.group("verdict_byte"), "inconclusive")
            _merge_asc_result(tests, test_id, status, {}, line_count)
            continue

    if not tests:
        raise ValueError(
            f"ASC log contains no AVERA test annotations or UDS results: {source}"
        )

    return {
        "runId": run_id,
        "stage": stage,
        "tests": list(tests.values()),
        "metadata": {
            "adapter": "canoe_asc.v1",
            "source_format": "canoe_asc",
            "source_path": str(source),
            "line_count": line_count,
            "annotation_count": annotation_count,
            "uds_result_count": uds_count,
            "test_count": len(tests),
        },
    }


def _merge_asc_result(
    tests: dict[str, dict[str, Any]],
    test_id: str,
    status: str,
    metrics: dict[str, Any],
    line_number: int,
) -> None:
    """Merge a single ASC result line into the *tests* accumulator."""

    if test_id not in tests:
        tests[test_id] = {
            "id": test_id,
            "component": "CANoe",
            "status": status,
            "metrics": dict(metrics),
            "evidence": "",
            "metadata": {
                "adapter": "canoe_asc.v1",
                "source_lines": [line_number],
            },
        }
    else:
        entry = tests[test_id]
        # Worst status wins (same order as logs adapter)
        _order = {"error": 4, "failed": 3, "inconclusive": 2, "skipped": 1, "passed": 0}
        if _order.get(status, 0) > _order.get(str(entry["status"]), 0):
            entry["status"] = status
        entry["metrics"].update(metrics)
        entry["metadata"]["source_lines"].append(line_number)


# ---------------------------------------------------------------------------
# Coercion helper (shared)
# ---------------------------------------------------------------------------

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
# SDK-compatible class adapter
# ---------------------------------------------------------------------------

from avera.adapters.interface import VerificationAdapter as _VA
class CANoeAdapter(_VA):
    """Unified VerificationAdapter for CANoe XML reports and ASC logs.

    Dispatches to :func:`adapt_canoe_xml` for ``.xml`` files and
    :func:`adapt_canoe_asc` for ``.asc`` files.
    """

    name = "canoe"
    version = "1.0.0"
    source_format = "canoe"
    file_extensions = (".xml", ".asc")

    def adapt(self, path: Path, *, run_id: str, stage: str) -> dict[str, Any]:
        """Dispatch to the correct underlying parser based on file extension."""
        suffix = path.suffix.lower()
        if suffix == ".xml":
            return adapt_canoe_xml(path, run_id=run_id, stage=stage)
        if suffix == ".asc":
            return adapt_canoe_asc(path, run_id=run_id, stage=stage)
        raise ValueError(
            f"CANoeAdapter: unsupported file extension {path.suffix!r} "
            f"for {path.name!r}. Supported: .xml, .asc"
        )

    def can_handle(self, path: Path) -> bool:
        suffix = path.suffix.lower()
        if suffix == ".asc":
            return True
        if suffix == ".xml":
            try:
                text = path.read_text(encoding="utf-8", errors="replace")[:512]
                return any(
                    tag in text
                    for tag in ("TestReport", "TEF_Report", "testReport", "tef_report")
                )
            except OSError:
                return False
        return False

    @property
    def metadata(self) -> dict[str, str]:
        return {
            "adapter": "canoe.1_0_0",
            "adapter_name": "canoe",
            "adapter_version": "1.0.0",
            "source_format": "canoe",
        }

    def __repr__(self) -> str:
        return "CANoeAdapter(name='canoe', version='1.0.0')"
