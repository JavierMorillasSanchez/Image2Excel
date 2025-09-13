"""
Motor OCR para Image2Excel.

Procesa imágenes de celdas individuales para extraer texto.
"""

from __future__ import annotations
import cv2
import numpy as np
from typing import Optional


class OCREngine:
    """Motor OCR para procesar celdas individuales."""

    def __init__(self, lang: str = "es"):
        self.lang = lang
        self._paddle_ocr = None

    def _get_ocr(self):
        """Obtiene la instancia de PaddleOCR (lazy loading)."""
        if self._paddle_ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    show_log=False
                )
            except ImportError:
                raise ImportError("PaddleOCR no está instalado. Instale con: pip install paddleocr")
        return self._paddle_ocr

    def read_cell(self, cell_image: np.ndarray) -> str:
        """
        Extrae texto de una imagen de celda.

        Args:
            cell_image: Imagen de la celda

        Returns:
            Texto extraído de la celda
        """
        try:
            # Preprocesar la imagen de la celda
            processed = self._preprocess_cell(cell_image)

            # Ejecutar OCR
            ocr = self._get_ocr()
            result = ocr.ocr(processed, cls=True)

            # Extraer texto de los resultados
            text_parts = []
            if result and isinstance(result, list):
                for page in result:
                    for _, (text, _) in page:
                        if text and text.strip():
                            text_parts.append(text.strip())

            return " ".join(text_parts) if text_parts else ""

        except Exception as e:
            print(f"Error en OCR de celda: {e}")
            return ""

    def _preprocess_cell(self, cell_image: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen de la celda para mejorar el OCR.

        Args:
            cell_image: Imagen original de la celda

        Returns:
            Imagen preprocesada
        """
        # Convertir a escala de grises si es necesario
        if len(cell_image.shape) == 3:
            gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cell_image.copy()

        # Aplicar filtro gaussiano para reducir ruido
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # Aplicar umbralización adaptativa
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Redimensionar si la imagen es muy pequeña
        h, w = thresh.shape
        if h < 20 or w < 20:
            scale = max(20 / h, 20 / w)
            new_h = int(h * scale)
            new_w = int(w * scale)
            thresh = cv2.resize(thresh, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        return thresh
