"""US-09.1: unified diff -> per-file changed line ranges.

Only lines *present in the new version* count as "changed" — a deleted line
has nothing left to cover. Ranges are 1-indexed, inclusive, merged, and sorted.
"""

from __future__ import annotations

import itertools

import pytest

from avera.change_coverage.diff import _merge_ranges, parse_unified_diff

BLANK_CONTEXT_LINE_WITH_STRIPPED_SPACE = """\
diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
@@ -1,4 +1,5 @@
 before

+added after blank
 after
"""

ONE_FILE = """\
diff --git a/pkg/math.py b/pkg/math.py
index abc123..def456 100644
--- a/pkg/math.py
+++ b/pkg/math.py
@@ -10,7 +10,9 @@ def add(a, b):
 def add(a, b):
-    return a + b
+    total = a + b
+    return total


 def sub(a, b):
"""

TWO_HUNKS = """\
diff --git a/pkg/math.py b/pkg/math.py
--- a/pkg/math.py
+++ b/pkg/math.py
@@ -2,3 +2,4 @@
 context
+added at 3
 context
+added at 5
@@ -20,2 +21,3 @@
 context
+added at 22
"""

TWO_FILES = """\
diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,3 @@
 ctx
+new in a
 ctx
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -5,1 +5,2 @@
 ctx
+new in b
"""

NEW_FILE = """\
diff --git a/fresh.py b/fresh.py
new file mode 100644
index 0000000..aaaa111
--- /dev/null
+++ b/fresh.py
@@ -0,0 +1,3 @@
+def f():
+    return 1
+
"""

DELETED_FILE = """\
diff --git a/gone.py b/gone.py
deleted file mode 100644
index aaaa111..0000000
--- a/gone.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def f():
-    return 1
-
"""

RENAME_NO_CONTENT = """\
diff --git a/old_name.py b/new_name.py
similarity index 100%
rename from old_name.py
rename to new_name.py
"""

PURE_DELETE_HUNK = """\
diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
@@ -5,3 +5,1 @@
 ctx
-removed
 ctx
"""

NO_TRAILING_NEWLINE = """\
diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
@@ -1,1 +1,1 @@
-old
\\ No newline at end of file
+new
\\ No newline at end of file
"""

STRAY_LINE_BEFORE_FIRST_HUNK = """\
diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
some stray line a mangled diff might insert here
@@ -1,1 +1,1 @@
+hello
"""

OMITTED_COUNT = """\
diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
@@ -10 +10 @@
-old line
+new line
"""


def test_single_hunk_added_and_modified_lines():
    result = parse_unified_diff(ONE_FILE)
    assert result == {"pkg/math.py": [(11, 12)]}


def test_deleted_line_is_not_a_changed_line():
    # The hunk above replaces one line with two; the deleted original line
    # must not appear as a changed (coverable) new-file line.
    result = parse_unified_diff(ONE_FILE)
    ranges = result["pkg/math.py"]
    covered_lines = {ln for start, end in ranges for ln in range(start, end + 1)}
    assert 10 not in covered_lines  # "def add(a, b):" context line, unchanged


def test_multiple_hunks_in_one_file_merge_in_order():
    result = parse_unified_diff(TWO_HUNKS)
    assert result == {"pkg/math.py": [(3, 3), (5, 5), (22, 22)]}


def test_multiple_files():
    result = parse_unified_diff(TWO_FILES)
    assert result == {"a.py": [(2, 2)], "b.py": [(6, 6)]}


def test_new_file_every_line_is_changed():
    result = parse_unified_diff(NEW_FILE)
    assert result == {"fresh.py": [(1, 3)]}


def test_deleted_file_has_nothing_to_cover():
    result = parse_unified_diff(DELETED_FILE)
    assert "gone.py" not in result


def test_rename_without_content_change_has_nothing_to_cover():
    result = parse_unified_diff(RENAME_NO_CONTENT)
    assert result == {}


def test_hunk_with_only_deletions_yields_no_ranges_for_that_hunk():
    result = parse_unified_diff(PURE_DELETE_HUNK)
    assert "x.py" not in result


def test_no_newline_at_eof_marker_is_ignored_not_content():
    result = parse_unified_diff(NO_TRAILING_NEWLINE)
    assert result == {"x.py": [(1, 1)]}


def test_stray_line_before_first_hunk_is_ignored_not_fatal():
    # Between "+++ file" and the first "@@" header, current_file is set but
    # no hunk is open yet. A stray/unrecognized line there (a mangled diff,
    # an email client reflow) must be ignored without derailing the real
    # hunk that follows.
    result = parse_unified_diff(STRAY_LINE_BEFORE_FIRST_HUNK)
    assert result == {"x.py": [(1, 1)]}


def test_hunk_header_with_omitted_count_means_one_line():
    result = parse_unified_diff(OMITTED_COUNT)
    assert result == {"x.py": [(10, 10)]}


def test_empty_diff_yields_empty_map():
    assert parse_unified_diff("") == {}


def test_crlf_line_endings_do_not_corrupt_filenames():
    text = ONE_FILE.replace("\n", "\r\n")
    result = parse_unified_diff(text)
    assert result == {"pkg/math.py": [(11, 12)]}


@pytest.mark.parametrize("text", [ONE_FILE, TWO_HUNKS, TWO_FILES, NEW_FILE])
def test_ranges_are_sorted_merged_and_non_overlapping(text):
    for ranges in parse_unified_diff(text).values():
        starts = [s for s, _ in ranges]
        assert starts == sorted(starts)
        for (_, end), (next_start, _) in itertools.pairwise(ranges):
            assert next_start > end + 1  # not adjacent/overlapping -> would have merged


def test_blank_context_line_with_stripped_leading_space_does_not_end_the_hunk():
    # Some diff viewers/tools strip trailing whitespace, turning a blank
    # context line's single leading space into a truly empty line. It must
    # still be read as context (not "end of hunk, ignore the rest") or the
    # file's own hunk fixture below — real git diff output, lines 1-4 — line
    # numbering for everything after it would be silently dropped.
    fixture_line = BLANK_CONTEXT_LINE_WITH_STRIPPED_SPACE.splitlines()[5]
    assert fixture_line == ""  # confirms the fixture actually has a bare blank line
    result = parse_unified_diff(BLANK_CONTEXT_LINE_WITH_STRIPPED_SPACE)
    assert result == {"x.py": [(3, 3)]}


# ---------------------------------------------------------------------------
# _merge_ranges boundary behaviour, directly
# ---------------------------------------------------------------------------

def test_merge_ranges_empty_input():
    assert _merge_ranges([]) == []


def test_merge_ranges_merges_truly_adjacent_ranges():
    assert _merge_ranges([(1, 5), (6, 6)]) == [(1, 6)]


def test_merge_ranges_does_not_merge_a_one_line_gap():
    assert _merge_ranges([(1, 5), (7, 7)]) == [(1, 5), (7, 7)]


def test_merge_ranges_merges_overlapping_ranges():
    assert _merge_ranges([(1, 5), (3, 8)]) == [(1, 8)]
