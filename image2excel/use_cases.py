# image2excel/use_cases.py
"""Application layer: casos de uso atómicos."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .ports import OcrEngine, TableParser, ExcelExporter


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
        words = self._ocr.extract_words(image_path, cfg.lang)
        table = self._parser.words_to_table(words, cfg.max_cols)
        xlsx_path = self._exporter.export(table, output_dir, cfg.output_filename)
        return xlsx_path
