# test_app.py
from __future__ import annotations
from pathlib import Path

from image2excel.use_cases import RunImageToExcel, RunImageToExcelConfig
from image2excel.adapters import PaddleOcrAdapter, BasicParserAdapter, OpenpyxlExporterAdapter


def test_end_to_end(tmp_path: Path):
    # Dado: imagen mínima de prueba (sintética o fixture)
    sample = Path("tests/data/sample_text.png")
    assert sample.exists(), "Falta tests/data/sample_text.png"

    use_case = RunImageToExcel(PaddleOcrAdapter(), BasicParserAdapter(), OpenpyxlExporterAdapter())
    out = use_case(sample, tmp_path, RunImageToExcelConfig(lang="es", output_filename="out.xlsx"))

    assert out.exists()
    assert out.suffix == ".xlsx"
