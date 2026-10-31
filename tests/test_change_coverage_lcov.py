"""US-09.2: LCOV coverage report -> per-file covered-line sets.

LCOV (``lcov.info``) is the common output of pytest-cov, Jest/Istanbul, and
grcov (Rust), among others. A line is covered if any ``DA:`` record for it
shows a hit count > 0.
"""

from __future__ import annotations

import pytest

from avera.change_coverage.lcov import parse_lcov

ONE_FILE = """\
TN:
SF:pkg/math.py
FN:1,add
FNDA:3,add
FNF:1
FNH:1
DA:1,3
DA:2,3
DA:3,0
DA:5,0
LF:4
LH:2
end_of_record
"""

TWO_FILES = """\
SF:a.py
DA:1,1
DA:2,0
end_of_record
SF:b.py
DA:10,5
end_of_record
"""

REPEATED_FILE_UNIONS_HITS = """\
SF:a.py
DA:1,0
DA:2,0
end_of_record
SF:a.py
DA:1,1
DA:2,0
end_of_record
"""

WITH_CHECKSUM_FIELD = """\
SF:a.py
DA:1,4,abc123checksum
end_of_record
"""

BRANCH_AND_FUNCTION_RECORDS_IGNORED = """\
SF:a.py
FN:1,f
FNDA:0,f
DA:1,2
BRDA:1,0,0,2
BRDA:1,0,1,0
BRF:2
BRH:1
end_of_record
"""

MISSING_END_OF_RECORD = """\
SF:a.py
DA:1,1
"""

UNKNOWN_FUTURE_DIRECTIVE = """\
SF:a.py
VER:2.1
DA:1,1
MRR:some,future,field
end_of_record
"""


def test_single_file_hit_lines_are_covered_zero_hits_are_not():
    result = parse_lcov(ONE_FILE)
    assert result == {"pkg/math.py": {1, 2}}


def test_multiple_files():
    result = parse_lcov(TWO_FILES)
    assert result == {"a.py": {1}, "b.py": {10}}


def test_repeated_sf_block_for_same_file_unions_covered_lines():
    result = parse_lcov(REPEATED_FILE_UNIONS_HITS)
    assert result == {"a.py": {1}}  # covered in the second block, not the first


def test_checksum_field_is_ignored():
    result = parse_lcov(WITH_CHECKSUM_FIELD)
    assert result == {"a.py": {1}}


def test_branch_and_function_records_are_ignored():
    result = parse_lcov(BRANCH_AND_FUNCTION_RECORDS_IGNORED)
    assert result == {"a.py": {1}}


def test_missing_end_of_record_at_eof_still_yields_the_block():
    result = parse_lcov(MISSING_END_OF_RECORD)
    assert result == {"a.py": {1}}


def test_unrecognized_directives_are_skipped_not_fatal():
    result = parse_lcov(UNKNOWN_FUTURE_DIRECTIVE)
    assert result == {"a.py": {1}}


def test_empty_report_yields_empty_map():
    assert parse_lcov("") == {}


def test_file_with_no_covered_lines_is_present_with_empty_set():
    result = parse_lcov("SF:a.py\nDA:1,0\nend_of_record\n")
    assert result == {"a.py": set()}


def test_malformed_da_line_raises_value_error():
    with pytest.raises(ValueError):
        parse_lcov("SF:a.py\nDA:not,a,number\nend_of_record\n")
