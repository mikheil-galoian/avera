from __future__ import annotations

from pathlib import Path

from avera.cli import run_adapt_requirements


def test_run_adapt_requirements_writes_stable_csv(tmp_path: Path) -> None:
    source = tmp_path / "requirements_variant.csv"
    target = tmp_path / "requirements.csv"
    source.write_text(
        """requirement_id,title,module,threshold_signal,threshold_operator,threshold_value,next_check,safety_relevance
BMS-REQ-112,Maximum cell temperature during fast charging must not exceed 50 C,BMS Thermal Control,max_cell_temp_c,<=,50.0,BMS-HIL-FASTCHARGE-07,high
""",
        encoding="utf-8",
    )

    code = run_adapt_requirements(source, target)
    written = target.read_text(encoding="utf-8")

    assert code == 0
    assert "id,component,requirement,metric,operator,threshold,safety_level,next_checks" in written
    assert "BMS-REQ-112,BMS Thermal Control,Maximum cell temperature during fast charging must not exceed 50 C,max_cell_temp_c,<=,50.0,high,BMS-HIL-FASTCHARGE-07" in written
