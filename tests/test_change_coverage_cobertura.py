"""US-09.3: Cobertura XML coverage report -> per-file covered-line sets.

Cobertura covers JaCoCo (Java), ``coverage.py --cobertura``, and several
Node/Go exporters. A line is covered if its ``<line number=".." hits="..">``
has hits > 0.
"""

from __future__ import annotations

import pytest

from avera.change_coverage.cobertura import parse_cobertura

ONE_FILE = """\
<?xml version="1.0"?>
<coverage line-rate="0.66" version="1">
  <packages>
    <package name="pkg">
      <classes>
        <class name="math" filename="pkg/math.py" line-rate="0.66">
          <lines>
            <line number="1" hits="3"/>
            <line number="2" hits="0"/>
            <line number="3" hits="1" branch="true" condition-coverage="50% (1/2)"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""

TWO_FILES_NESTED_PACKAGES = """\
<coverage>
  <packages>
    <package name="pkg.sub">
      <classes>
        <class name="a" filename="pkg/sub/a.py">
          <lines><line number="1" hits="1"/></lines>
        </class>
      </classes>
    </package>
    <package name="pkg">
      <classes>
        <class name="b" filename="pkg/b.py">
          <lines><line number="10" hits="0"/></lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""

TWO_CLASSES_SAME_FILE_UNION = """\
<coverage>
  <packages><package name="p"><classes>
    <class name="Outer" filename="pkg/multi.py">
      <lines><line number="1" hits="0"/><line number="2" hits="0"/></lines>
    </class>
    <class name="Outer.Inner" filename="pkg/multi.py">
      <lines><line number="1" hits="2"/></lines>
    </class>
  </classes></package></packages>
</coverage>
"""

MISSING_HITS_ATTRIBUTE = """\
<coverage><packages><package name="p"><classes>
  <class name="a" filename="a.py"><lines><line number="1"/></lines></class>
</classes></package></packages></coverage>
"""

WITH_DOCTYPE = """\
<?xml version="1.0"?>
<!DOCTYPE coverage SYSTEM "http://cobertura.sourceforge.net/xml/coverage-04.dtd">
<coverage><packages/></coverage>
"""


def test_single_file_hit_lines_are_covered_zero_hits_are_not():
    result = parse_cobertura(ONE_FILE)
    assert result == {"pkg/math.py": {1, 3}}


def test_multiple_files_across_nested_packages():
    result = parse_cobertura(TWO_FILES_NESTED_PACKAGES)
    assert result == {"pkg/sub/a.py": {1}, "pkg/b.py": set()}


def test_two_classes_in_the_same_file_union_covered_lines():
    result = parse_cobertura(TWO_CLASSES_SAME_FILE_UNION)
    # line 1: hits=0 in the first class, hits=2 in the second -> covered (union).
    # line 2: hits=0 and never mentioned again -> stays uncovered.
    assert result == {"pkg/multi.py": {1}}


def test_empty_report_yields_empty_map():
    assert parse_cobertura("<coverage><packages/></coverage>") == {}


def test_malformed_hits_attribute_raises_value_error():
    with pytest.raises(ValueError):
        parse_cobertura(MISSING_HITS_ATTRIBUTE)


def test_doctype_is_refused_same_as_other_adapters():
    with pytest.raises(ValueError):
        parse_cobertura(WITH_DOCTYPE)


def test_not_xml_raises_value_error():
    with pytest.raises(ValueError):
        parse_cobertura("not xml at all")
