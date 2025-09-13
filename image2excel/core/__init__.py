"""
Módulo core de Image2Excel.

Contiene las clases principales para el procesamiento de imágenes con plantillas:
- TemplateManager: Gestión de plantillas
- ImageAligner: Alineación de imágenes
- GridExtractor: Extracción de celdas de cuadrícula
- OCREngine: Motor OCR
- Postprocess: Postprocesamiento de datos
- ExporterExcel: Exportación a Excel
"""

from .template_manager import TemplateManager, GridSpec, Cell
from .aligner import ImageAligner
from .grid_extractor import GridExtractor
from .ocr_engine import OCREngine
from .postprocess import postprocess_by_column
from .exporter_excel import export_rows_xlsx

__all__ = [
    'TemplateManager', 'GridSpec', 'Cell',
    'ImageAligner',
    'GridExtractor',
    'OCREngine',
    'postprocess_by_column',
    'export_rows_xlsx'
]
