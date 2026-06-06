from __future__ import annotations

from pathlib import Path

from avera.adapters import adapt_requirements_csv

ROOT = Path(__file__).resolve().parents[1]


def test_adapt_requirements_csv_maps_variant_columns() -> None:
    fixture = ROOT / "fixtures/bms-requirements-adapted/requirements_export_variant.csv"

    rows = adapt_requirements_csv(fixture)

    assert len(rows) == 2
    assert rows[0]["id"] == "BMS-REQ-112"
    assert rows[0]["component"] == "BMS Thermal Control"
    assert rows[0]["requirement"].startswith("Maximum cell temperature")
    assert rows[0]["metric"] == "max_cell_temp_c"
    assert rows[0]["operator"] == "<="
    assert rows[0]["threshold"] == "50.0"
    assert rows[0]["safety_level"] == "high"
    assert rows[0]["next_checks"] == "BMS-HIL-FASTCHARGE-07"


def test_adapt_requirements_csv_rejects_missing_required_value(tmp_path: Path) -> None:
    source = tmp_path / "requirements_variant.csv"
    source.write_text(
        """requirement_id,title,module,threshold_signal,threshold_operator,threshold_value
,Missing id,BMS Thermal Control,max_cell_temp_c,<=,50.0
""",
        encoding="utf-8",
    )

    try:
        adapt_requirements_csv(source)
    except ValueError as exc:
        assert "missing value for id" in str(exc).lower()
    else:
        raise AssertionError("Expected missing requirement id to fail")
