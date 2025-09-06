from __future__ import annotations
from pathlib import Path
from typing import Protocol, Optional
from .models import OcrResult, Table, ExportResult


class ImageLoader(Protocol):
    def load(self, image_path: Path) -> "Image":
        """Carga imagen desde disco y retorna un objeto imagen (tipo opaco)."""


class Preprocessor(Protocol):
    def preprocess(self, image: "Image") -> "Image":
        """Aplica preprocesado (binarización, deskew, denoise...)."""


class OcrEngine(Protocol):
    def run_ocr(self, image: "Image") -> OcrResult:
        """Ejecuta OCR y retorna texto y, si aplica, tabla detectada."""


class TableDetector(Protocol):
    def detect_table(self, image: "Image", ocr_text: str) -> Optional[Table]:
        """Detecta tabla estructurada a partir de la imagen y/o texto OCR."""


class ExcelExporter(Protocol):
    def export_table(self, table: Table, output_path: Path) -> ExportResult:
        """Exporta tabla a Excel en `output_path`."""
