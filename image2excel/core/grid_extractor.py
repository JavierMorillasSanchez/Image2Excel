"""
Extractor de cuadrícula para Image2Excel.

Extrae celdas individuales de una imagen alineada usando una especificación de cuadrícula.
"""

from __future__ import annotations
import cv2
import numpy as np
from typing import List, Tuple
from .template_manager import GridSpec, Cell


class GridExtractor:
    """Extractor de celdas de cuadrícula."""

    def __init__(self, spec: GridSpec, pad: int = 6):
        self.spec = spec
        self.pad = pad

    def crop_cells(self, img: np.ndarray) -> List[Tuple[Cell, np.ndarray]]:
        """
        Extrae todas las celdas de la imagen según la especificación.

        Args:
            img: Imagen alineada

        Returns:
            Lista de tuplas (Cell, crop_image) para cada celda
        """
        crops = []
        img_h, img_w = img.shape[:2]

        for cell in self.spec.cells:
            # Convertir coordenadas normalizadas a píxeles si es necesario
            if self.spec.normalized:
                x1 = int(cell.x * img_w)
                y1 = int(cell.y * img_h)
                x2 = int((cell.x + cell.w) * img_w)
                y2 = int((cell.y + cell.h) * img_h)
            else:
                x1 = int(cell.x)
                y1 = int(cell.y)
                x2 = int(cell.x + cell.w)
                y2 = int(cell.y + cell.h)

            # Aplicar padding a las coordenadas
            x1 = max(0, x1 - self.pad)
            y1 = max(0, y1 - self.pad)
            x2 = min(img_w, x2 + self.pad)
            y2 = min(img_h, y2 + self.pad)

            # Extraer la región de la celda
            crop = img[y1:y2, x1:x2]

            # Solo incluir si la región no está vacía
            if crop.size > 0:
                crops.append((cell, crop))

        return crops

    def extract_single_cell(self, img: np.ndarray, cell: Cell) -> np.ndarray:
        """
        Extrae una celda específica de la imagen.

        Args:
            img: Imagen alineada
            cell: Especificación de la celda

        Returns:
            Imagen recortada de la celda
        """
        img_h, img_w = img.shape[:2]

        # Convertir coordenadas normalizadas a píxeles si es necesario
        if self.spec.normalized:
            x1 = int(cell.x * img_w)
            y1 = int(cell.y * img_h)
            x2 = int((cell.x + cell.w) * img_w)
            y2 = int((cell.y + cell.h) * img_h)
        else:
            x1 = int(cell.x)
            y1 = int(cell.y)
            x2 = int(cell.x + cell.w)
            y2 = int(cell.y + cell.h)

        # Aplicar padding a las coordenadas
        x1 = max(0, x1 - self.pad)
        y1 = max(0, y1 - self.pad)
        x2 = min(img_w, x2 + self.pad)
        y2 = min(img_h, y2 + self.pad)

        return img[y1:y2, x1:x2]
