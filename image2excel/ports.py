# image2excel/ports.py
"""Ports (interfaces) para Clean Architecture.

Tipos de datos mínimos para desacoplar el dominio de librerías externas.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol


@dataclass(frozen=True)
class OcrWord:
    text: str
    confidence: float
    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class TableRow:
    cells: list[str]


@dataclass(frozen=True)
class Table:
    rows: list[TableRow]


class OcrEngine(Protocol):
    def extract_words(self, image_path: Path, lang: str) -> list[OcrWord]:
        """Extrae palabras con confianza y bounding boxes."""


class TableParser(Protocol):
    def words_to_table(self, words: Iterable[OcrWord], max_cols: int | None = None) -> Table:
        """Convierte OCR a tabla estructurada."""


class ExcelExporter(Protocol):
    def export(self, table: Table, output_dir: Path, filename: str) -> Path:
        """Exporta la tabla a un .xlsx y devuelve la ruta final."""
