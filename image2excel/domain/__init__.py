"""Domain layer for image2excel application.

This module contains the core domain models and ports (interfaces)
that define the business logic and contracts for the application.
"""

from .models import Cell, TableRow, Table, OcrResult, ExportResult
from .ports import (
    ImageLoader,
    Preprocessor,
    OcrEngine,
    TableDetector,
    ExcelExporter,
)

__all__ = [
    "Cell",
    "TableRow",
    "Table",
    "OcrResult",
    "ExportResult",
    "ImageLoader",
    "Preprocessor",
    "OcrEngine",
    "TableDetector",
    "ExcelExporter",
]
