"""Parse an LCOV coverage report (``lcov.info``) into per-file covered lines.

Only the directives relevant to line coverage are read: ``SF:`` (source file),
``DA:<line>,<hits>[,<checksum>]`` (per-line hit count), and ``end_of_record``.
Branch (``BRDA``/``BRF``/``BRH``) and function (``FN``/``FNDA``/``FNF``/``FNH``)
records are not line coverage and are ignored, as is any directive this parser
does not recognise — LCOV gains fields over tool versions, and an unrecognised
directive is not evidence of anything, so it is skipped rather than failing.

A malformed ``DA:`` line (non-numeric fields) *does* raise: unlike an unknown
directive, it means a line coverage record that should be trustworthy is not,
and silently dropping it would under-report, not fail closed.
"""

from __future__ import annotations


def parse_lcov(text: str) -> dict[str, set[int]]:
    """Return ``{file_path: {covered_line_numbers}}``.

    A line is covered if *any* ``DA:`` record for it, across possibly repeated
    ``SF:`` blocks for the same file, shows a hit count > 0.
    """
    result: dict[str, set[int]] = {}
    current_file: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("SF:"):
            current_file = line[3:]
            result.setdefault(current_file, set())
        elif line.startswith("DA:"):
            if current_file is None:
                continue  # DA before any SF — malformed input, nothing to attribute it to
            fields = line[3:].split(",")
            if len(fields) < 2:
                raise ValueError(f"malformed LCOV DA record: {raw_line!r}")
            try:
                lineno = int(fields[0])
                hits = int(fields[1])
            except ValueError as exc:
                raise ValueError(f"malformed LCOV DA record: {raw_line!r}") from exc
            if hits > 0:
                result[current_file].add(lineno)
        elif line == "end_of_record":
            current_file = None
        # Any other directive (FN/FNDA/FNF/FNH/BRDA/BRF/BRH/TN/VER/future ones)
        # is not line coverage data and is intentionally ignored.

    return result
