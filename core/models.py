"""Core domain models for OCR results and tabular data.

Refactor notes:
- Introduced explicit data models to decouple UI/IO from business logic.
- Enables testing and substitution of components (SOLID, DIP).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OCRTextLine:
    """Represents a single line of OCR text with optional confidence.

    Attributes
    ----------
    text: str
        Extracted text content.
    confidence: Optional[float]
        Confidence score in range [0, 1]. None if unknown.
    """

    text: str
    confidence: Optional[float] = None


@dataclass
class OCRResult:
    """OCR result for a single image/document.

    Attributes
    ----------
    lines: List[OCRTextLine]
        List of extracted text lines.
    """

    lines: List[OCRTextLine] = field(default_factory=list)


@dataclass
class TableCell:
    """Represents a cell in a table."""

    text: str


@dataclass
class TableRow:
    """Represents a row in a table."""

    cells: List[TableCell] = field(default_factory=list)


@dataclass
class Table:
    """Represents a simple table composed of rows and cells."""

    rows: List[TableRow] = field(default_factory=list)


__all__ = [
    "OCRTextLine",
    "OCRResult",
    "TableCell",
    "TableRow",
    "Table",
]
