"""Parse a Cobertura XML coverage report into per-file covered lines.

Covers JaCoCo (Java), ``coverage.py --cov-report=xml``, and several Node/Go
exporters that target the same schema. Walks every ``<class filename="…">``
anywhere in the document (package nesting is not load-bearing) and reads its
``<line number=".." hits="..">`` children — the one part of the schema that
has stayed stable across Cobertura's exporters.

Reuses ``adapters._xml_safe.secure_fromstring``: the same billion-laughs /
DOCTYPE refusal as every other XML AVERA parses, rather than a second way of
parsing XML in the codebase.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from avera.adapters._xml_safe import secure_fromstring


def parse_cobertura(text: str) -> dict[str, set[int]]:
    """Return ``{file_path: {covered_line_numbers}}``.

    A line is covered if *any* ``<line>`` record for it, across every
    ``<class>`` that maps to the same ``filename`` (e.g. nested/inner
    classes), shows ``hits`` > 0. A ``<class>`` with no ``<line>`` children
    still registers the file with an empty covered set.
    """
    try:
        root = secure_fromstring(text, source="<cobertura report>")
    except ET.ParseError as exc:
        raise ValueError(f"not a valid Cobertura XML document: {exc}") from exc

    result: dict[str, set[int]] = {}
    for class_el in root.iter("class"):
        filename = class_el.get("filename")
        if not filename:
            continue
        result.setdefault(filename, set())
        for line_el in class_el.iter("line"):
            number_raw = line_el.get("number")
            hits_raw = line_el.get("hits")
            if number_raw is None or hits_raw is None:
                raise ValueError(
                    f"malformed Cobertura <line> in {filename!r}: "
                    f"missing number/hits ({ET.tostring(line_el, encoding='unicode')!r})"
                )
            try:
                number = int(number_raw)
                hits = int(hits_raw)
            except ValueError as exc:
                raise ValueError(
                    f"malformed Cobertura <line> in {filename!r}: "
                    f"non-integer number/hits ({number_raw!r}, {hits_raw!r})"
                ) from exc
            if hits > 0:
                result[filename].add(number)

    return result
