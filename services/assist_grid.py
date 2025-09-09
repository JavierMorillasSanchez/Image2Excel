"""
Servicio para procesar cuadrículas asistidas por el usuario.

Este módulo toma las coordenadas de separadores marcados por el usuario
y extrae el texto de cada celda usando PaddleOCR.
"""

from __future__ import annotations
from typing import List, Tuple
import cv2
import numpy as np
from services.paddle_ocr import PaddleOcrService


def extract_text_from_grid(
    image_path: str,
    vertical_lines: List[int],
    horizontal_lines: List[int],
    lang: str = "es"
) -> List[List[str]]:
    """
    Extrae texto de cada celda de la cuadrícula definida por las líneas marcadas.

    Args:
        image_path: Ruta a la imagen
        vertical_lines: Lista de coordenadas X de líneas verticales
        horizontal_lines: Lista de coordenadas Y de líneas horizontales
        lang: Idioma para OCR

    Returns:
        Matriz de texto extraído [fila][columna]
    """
    # Cargar imagen
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    # Añadir bordes de la imagen a las líneas
    h, w = img.shape[:2]
    x_coords = [0] + sorted(vertical_lines) + [w]
    y_coords = [0] + sorted(horizontal_lines) + [h]

    # Inicializar OCR
    ocr_service = PaddleOcrService(profile="precision", use_gpu=False)

    # Crear matriz de resultados
    rows = len(y_coords) - 1
    cols = len(x_coords) - 1
    result = [["" for _ in range(cols)] for _ in range(rows)]

    # Procesar cada celda
    for row in range(rows):
        for col in range(cols):
            # Calcular coordenadas de la celda
            x1, y1 = x_coords[col], y_coords[row]
            x2, y2 = x_coords[col + 1], y_coords[row + 1]

            # Recortar celda
            cell_img = img[y1:y2, x1:x2]

            # Verificar que la celda no esté vacía
            if cell_img.size == 0:
                continue

            # Añadir padding para mejorar OCR
            padding = 10
            padded_img = cv2.copyMakeBorder(
                cell_img, padding, padding, padding, padding,
                cv2.BORDER_CONSTANT, value=[255, 255, 255]
            )

            # Guardar imagen temporal para OCR
            temp_path = f"temp_cell_{row}_{col}.png"
            cv2.imwrite(temp_path, padded_img)

            try:
                # Extraer texto de la celda
                ocr_results = ocr_service.extract_words(temp_path, lang=lang)

                # Combinar todo el texto encontrado
                cell_text = " ".join([text for _, (text, _) in ocr_results if text.strip()])
                result[row][col] = cell_text.strip()

            except Exception as e:
                print(f"Error procesando celda ({row}, {col}): {e}")
                result[row][col] = ""

            finally:
                # Limpiar archivo temporal
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    return result


def validate_grid_coordinates(
    vertical_lines: List[int],
    horizontal_lines: List[int],
    image_width: int,
    image_height: int
) -> bool:
    """
    Valida que las coordenadas de la cuadrícula sean válidas.

    Args:
        vertical_lines: Lista de coordenadas X
        horizontal_lines: Lista de coordenadas Y
        image_width: Ancho de la imagen
        image_height: Alto de la imagen

    Returns:
        True si las coordenadas son válidas
    """
    # Verificar que hay al menos una línea en cada dirección
    if not vertical_lines or not horizontal_lines:
        return False

    # Verificar que las líneas están dentro de la imagen
    for x in vertical_lines:
        if x < 0 or x >= image_width:
            return False

    for y in horizontal_lines:
        if y < 0 or y >= image_height:
            return False

    # Verificar que las líneas no están en los bordes
    if 0 in vertical_lines or image_width - 1 in vertical_lines:
        return False

    if 0 in horizontal_lines or image_height - 1 in horizontal_lines:
        return False

    return True
