"""Hardened XML parsing shared by the report adapters.

The stdlib ``xml.etree.ElementTree`` parser expands internal entities and
processes DTDs, which exposes a billion-laughs / entity-expansion denial of
service when parsing untrusted test reports (and the entry point for
external-entity attacks). Test reports (JUnit / xUnit / CANoe) never legitimately
need a DTD, so we refuse any document that declares one rather than letting the
parser expand entities.
"""

from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# A DOCTYPE declaration is the only way to define internal entities (billion
# laughs) or reference external/parameter entities. Refuse it outright.
_DOCTYPE_RE = re.compile(r"<!DOCTYPE", re.IGNORECASE)


def secure_fromstring(text: str, source: Path | str) -> ET.Element:
    """Parse XML text, refusing any DTD/DOCTYPE.

    Raises
    ------
    ValueError
        If the document declares a DOCTYPE/DTD.
    xml.etree.ElementTree.ParseError
        If the XML is otherwise malformed (callers wrap this as ``ValueError``).
    """
    if _DOCTYPE_RE.search(text):
        raise ValueError(
            f"XML declaring a DOCTYPE/DTD is not allowed (entity-expansion risk): {source}"
        )
    return ET.fromstring(text)


def finite_float(raw: str) -> float | None:
    """Parse ``raw`` as a float, returning None for non-finite values.

    NaN / Infinity must never enter a safety gate: NaN comparisons are always
    false, so a NaN metric could silently slip past a threshold check.
    """
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None
