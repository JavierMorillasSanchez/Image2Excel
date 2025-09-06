from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class Cell:
    text: str
    confidence: Optional[float] = None


@dataclass(frozen=True)
class TableRow:
    cells: List[Cell]


@dataclass(frozen=True)
class Table:
    rows: List[TableRow]


@dataclass(frozen=True)
class OcrResult:
    text: str
    table: Optional[Table] = None


@dataclass(frozen=True)
class ExportResult:
    output_path: Path
