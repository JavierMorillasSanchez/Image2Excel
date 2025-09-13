"""
Postprocesamiento de datos para Image2Excel.

Limpia y normaliza los datos extraídos por OCR según el tipo de columna.
"""

from __future__ import annotations
import re
from typing import Any


def postprocess_by_column(column_name: str, text: str) -> str:
    """
    Postprocesa el texto según el tipo de columna.

    Args:
        column_name: Nombre de la columna
        text: Texto extraído por OCR

    Returns:
        Texto postprocesado
    """
    if not text:
        return ""

    # Limpiar texto básico
    cleaned = _clean_text(text)

    # Aplicar reglas específicas por columna
    if column_name.lower() in ['peso', 'weight']:
        return _process_weight(cleaned)
    elif column_name.lower() in ['dxo', 'codigo', 'code']:
        return _process_code(cleaned)
    elif column_name.lower() in ['marca', 'brand']:
        return _process_brand(cleaned)
    elif column_name.lower() in ['etiqueta', 'label', 'tag']:
        return _process_label(cleaned)
    else:
        return cleaned


def _clean_text(text: str) -> str:
    """Limpia el texto básico."""
    # Remover caracteres extraños comunes en OCR
    text = re.sub(r'[^\w\s\-\.]', '', text)

    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text)

    # Remover espacios al inicio y final
    return text.strip()


def _process_weight(text: str) -> str:
    """Procesa texto de peso."""
    # Buscar números con unidades de peso
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|g|lb|lbs)?', text, re.IGNORECASE)
    if weight_match:
        return weight_match.group(1)

    # Si no hay unidades, devolver solo números
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    return numbers[0] if numbers else text


def _process_code(text: str) -> str:
    """Procesa códigos alfanuméricos."""
    # Remover espacios y caracteres especiales
    code = re.sub(r'[^\w]', '', text.upper())
    return code


def _process_brand(text: str) -> str:
    """Procesa nombres de marca."""
    # Capitalizar primera letra de cada palabra
    return ' '.join(word.capitalize() for word in text.split())


def _process_label(text: str) -> str:
    """Procesa etiquetas."""
    # Mantener el texto tal como está, solo limpiado
    return text
