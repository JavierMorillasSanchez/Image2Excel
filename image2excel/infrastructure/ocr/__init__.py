"""OCR adapters for image2excel application."""

from .paddle_table_detector import PaddleTableDetector
from .paddle_ocr_engine import PaddleOcrEngine

__all__ = ["PaddleTableDetector", "PaddleOcrEngine"]
