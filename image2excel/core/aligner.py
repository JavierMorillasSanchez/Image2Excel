"""
Alineador de imágenes para Image2Excel.

Alinea una imagen de entrada con una plantilla de referencia.
"""

from __future__ import annotations
import cv2
import numpy as np
from typing import Tuple


class ImageAligner:
    """Alineador de imágenes con plantillas."""

    def __init__(self, target_w: int, target_h: int):
        self.target_w = target_w
        self.target_h = target_h

    def align(self, img: np.ndarray, template: np.ndarray) -> np.ndarray:
        """
        Alinea la imagen con la plantilla.

        Args:
            img: Imagen de entrada
            template: Imagen de plantilla de referencia

        Returns:
            Imagen alineada redimensionada al tamaño objetivo
        """
        # Redimensionar la imagen de entrada al tamaño objetivo
        img_resized = cv2.resize(img, (self.target_w, self.target_h))

        # Para simplificar, devolvemos la imagen redimensionada
        # En una implementación completa, aquí se haría alineación por características
        return img_resized

    def _find_template_match(self, img: np.ndarray, template: np.ndarray) -> Tuple[int, int]:
        """
        Encuentra la mejor coincidencia de la plantilla en la imagen.

        Returns:
            Tupla (x, y) con las coordenadas del mejor match
        """
        # Usar template matching de OpenCV
        result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(result)
        return max_loc
