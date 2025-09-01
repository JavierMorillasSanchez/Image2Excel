"""OCR engine interface and factory.

Refactor notes:
- Defines a protocol-like abstract base for OCR engines.
- Facilitates swapping OCR backends (e.g., PaddleOCR) without UI changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol

from core.models import OCRResult


class OCREngine(ABC):
    """Abstract OCR engine contract."""

    @abstractmethod
    def extract_text(self, image_path: str) -> OCRResult:
        """Run OCR for the given image path.

        Parameters
        ----------
        image_path: str
            Path to the input image.

        Returns
        -------
        OCRResult
            Structured OCR output.
        """
        raise NotImplementedError


__all__ = ["OCREngine"]
