"""Parse a unified diff into per-file changed line ranges.

Only lines present *in the new version of the file* are "changed" — a deleted
line has nothing left for a test to cover. A new file counts every line as
changed; a deleted file (or a rename with no content change) contributes
nothing.

Deliberately count-less: rather than trusting the hunk header's declared line
count (``@@ -a,b +c,d @@``), a hunk is read until the next recognised
transition line (``+++``, ``---``, another ``@@``, or anything that is not a
content line). Real diffs from ``git diff`` always have exactly as many
``+``/`` `` lines as the header's new-count before that happens, so this is
equivalent for well-formed input and more tolerant of an imperfect generator.
"""

from __future__ import annotations

import re

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _strip_new_file_prefix(path: str) -> str:
    """Strip git's conventional ``b/`` prefix; a path without one is used as-is
    (covers ``git diff --no-prefix`` and hand-built diffs)."""
    return path.removeprefix("b/")


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Sort and merge overlapping/adjacent (start, end) ranges."""
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def parse_unified_diff(text: str) -> dict[str, list[tuple[int, int]]]:
    """Return ``{file_path: [(start, end), ...]}`` — 1-indexed, inclusive,
    sorted, non-overlapping ranges of lines added or modified in the new
    version of each file touched by the diff."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    raw: dict[str, list[tuple[int, int]]] = {}
    current_file: str | None = None
    new_line: int | None = None
    run_start: int | None = None
    run_end: int | None = None

    def flush_run() -> None:
        nonlocal run_start, run_end
        if run_start is not None and current_file is not None:
            raw.setdefault(current_file, []).append((run_start, run_end))
        run_start = None
        run_end = None

    for line in lines:
        if line.startswith("+++ "):
            flush_run()
            path = line[4:]
            current_file = None if path == "/dev/null" else _strip_new_file_prefix(path)
            new_line = None
            continue
        if line.startswith("--- "):
            flush_run()
            continue
        header = _HUNK_HEADER.match(line)
        if header:
            flush_run()
            new_line = int(header.group(1))
            continue

        if current_file is None or new_line is None:
            continue  # header/metadata line (diff --git, index, mode, rename …)

        if line.startswith("+"):
            if run_start is None:
                run_start = new_line
            run_end = new_line
            new_line += 1
        elif line.startswith("-"):
            flush_run()  # removed line: not present in the new file
        elif line.startswith("\\"):
            pass  # "\ No newline at end of file" — not a content line
        elif line.startswith(" ") or line == "":
            flush_run()  # context line (unchanged)
            new_line += 1
        else:
            # Anything else (next file's "diff --git", "index …", …) ends the hunk.
            flush_run()
            current_file = None
            new_line = None

    flush_run()
    return {path: _merge_ranges(ranges) for path, ranges in raw.items()}
