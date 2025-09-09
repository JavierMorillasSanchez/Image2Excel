# image2excel/use_cases.py
"""Application layer: casos de uso atómicos."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .ports import OcrEngine, TableParser, ExcelExporter, Table, TableRow


@dataclass(slots=True, frozen=True)
class RunImageToExcelConfig:
    lang: str = "es"
    max_cols: int | None = None
    output_filename: str = "texto_extraido.xlsx"


class RunImageToExcel:
    """Caso de uso: imagen -> OCR -> tabla -> Excel."""

    def __init__(self, ocr: OcrEngine, parser: TableParser, exporter: ExcelExporter) -> None:
        self._ocr = ocr
        self._parser = parser
        self._exporter = exporter

    def __call__(self, image_path: Path, output_dir: Path, cfg: RunImageToExcelConfig) -> Path:
        try:
            from services.pp_table import PPTableExtractor
            grid = PPTableExtractor(lang=cfg.lang, use_gpu=False).image_to_grid(str(image_path))
            if grid and any(any(c for c in r) for r in grid):
                return self._exporter.export(
                    Table(rows=[TableRow(cells=r) for r in grid]),
                    output_dir, cfg.output_filename
                )
        except Exception:
            pass

        # Fallback actual:
        words = self._ocr.extract_words(image_path, cfg.lang)
        table = self._parser.words_to_table(words, cfg.max_cols)
        return self._exporter.export(table, output_dir, cfg.output_filename)
