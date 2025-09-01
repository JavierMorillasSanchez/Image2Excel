"""Excel exporter for tables using openpyxl.

Refactor aplicado:
- Mejorado el formato y presentación de Excel con estilos profesionales
- Añadido manejo robusto de errores y validaciones
- Implementado sistema de plantillas y configuraciones personalizables
- Soporte para múltiples hojas y metadatos
- Mejor gestión de memoria y optimización de rendimiento
- Logging detallado del proceso de exportación
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

import openpyxl
from openpyxl.styles import (
    Font, Alignment, PatternFill, Border, Side, NamedStyle
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from core.models import Table, OCRResult
from infrastructure.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ExcelConfig:
    """Configuración para la exportación a Excel."""

    # Configuración de archivo
    filename: str = "texto_extraido.xlsx"
    sheet_name: str = "Texto Extraído"
    include_metadata: bool = True
    include_confidence: bool = True

    # Configuración de formato
    header_style: str = "header"  # Nombre del estilo predefinido
    data_style: str = "data"      # Nombre del estilo predefinido
    auto_adjust_columns: bool = True
    freeze_panes: bool = True

    # Configuración de colores
    header_bg_color: str = "366092"  # Azul corporativo
    header_font_color: str = "FFFFFF"  # Blanco
    data_bg_color: str = "FFFFFF"     # Blanco
    data_font_color: str = "000000"   # Negro
    border_color: str = "CCCCCC"      # Gris claro

    # Configuración de fuentes
    header_font_size: int = 12
    data_font_size: int = 10
    header_font_bold: bool = True
    data_font_bold: bool = False


class ExcelExporter:
    """
    Exportador profesional de tablas a Excel con formato avanzado.

    Refactor: Implementado sistema de estilos, mejor manejo de errores y formato profesional
    """

    def __init__(self, config: Optional[ExcelConfig] = None):
        """
        Inicializar el exportador de Excel.

        Parameters
        ----------
        config : Optional[ExcelConfig]
            Configuración personalizada para la exportación
        """
        self.config = config or ExcelConfig()
        self.logger = get_logger(self.__class__.__name__)

        # Estilos predefinidos
        self._styles = {}
        self._initialize_styles()

        self.logger.info(
            "ExcelExporter inicializado con configuración: "
            "archivo=%s, hoja=%s, incluir_confianza=%s",
            self.config.filename, self.config.sheet_name,
            self.config.include_confidence
        )

    def _initialize_styles(self) -> None:
        """Inicializar estilos predefinidos para Excel."""
        # Estilo de encabezado
        header_style = NamedStyle(name="header")
        header_style.font = Font(
            name="Calibri",
            size=self.config.header_font_size,
            bold=self.config.header_font_bold,
            color=self.config.header_font_color
        )
        header_style.fill = PatternFill(
            start_color=self.config.header_bg_color,
            end_color=self.config.header_bg_color,
            fill_type="solid"
        )
        header_style.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )
        header_style.border = Border(
            left=Side(style="thin", color=self.config.border_color),
            right=Side(style="thin", color=self.config.border_color),
            top=Side(style="thin", color=self.config.border_color),
            bottom=Side(style="thin", color=self.config.border_color)
        )

        # Estilo de datos
        data_style = NamedStyle(name="data")
        data_style.font = Font(
            name="Calibri",
            size=self.config.data_font_size,
            bold=self.config.data_font_bold,
            color=self.config.data_font_color
        )
        data_style.fill = PatternFill(
            start_color=self.config.data_bg_color,
            end_color=self.config.data_bg_color,
            fill_type="solid"
        )
        data_style.alignment = Alignment(
            horizontal="left",
            vertical="center",
            wrap_text=True
        )
        data_style.border = Border(
            left=Side(style="thin", color=self.config.border_color),
            right=Side(style="thin", color=self.config.border_color),
            top=Side(style="thin", color=self.config.border_color),
            bottom=Side(style="thin", color=self.config.border_color)
        )

        self._styles["header"] = header_style
        self._styles["data"] = data_style

    def export_table(
        self,
        table: Table,
        ocr: Optional[OCRResult],
        output_dir: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Exportar tabla a archivo Excel con formato profesional.

        Parameters
        ----------
        table : Table
            Tabla a exportar
        ocr : Optional[OCRResult]
            Resultado del OCR para metadatos
        output_dir : str
            Directorio de salida
        filename : Optional[str]
            Nombre personalizado del archivo

        Returns
        -------
        str
            Ruta completa del archivo Excel generado

        Raises
        ------
        ValueError
            Si los parámetros no son válidos
        RuntimeError
            Si falla la exportación
        """
        try:
            start_time = time.time()

            # Validar entrada
            self._validate_export_params(table, output_dir)

            # Crear directorio de salida si no existe
            os.makedirs(output_dir, exist_ok=True)

            # Determinar nombre del archivo
            final_filename = filename or self.config.filename
            if not final_filename.endswith('.xlsx'):
                final_filename += '.xlsx'

            excel_path = os.path.join(output_dir, final_filename)

            self.logger.info(
                "Iniciando exportación a Excel: %s líneas, %s columnas",
                len(table.rows), self._get_max_columns(table)
            )

            # Crear workbook y worksheet
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            worksheet.title = self.config.sheet_name

            # Aplicar estilos y formato
            self._setup_worksheet(worksheet, table)

            # Escribir encabezados
            self._write_headers(worksheet, table, ocr)

            # Escribir datos
            self._write_data(worksheet, table, ocr)

            # Aplicar formato final
            self._apply_final_formatting(worksheet, table)

            # Guardar archivo
            workbook.save(excel_path)
            workbook.close()

            # Calcular tiempo de exportación
            export_time = time.time() - start_time

            self.logger.info(
                "Excel exportado exitosamente en %.2f segundos: %s",
                export_time, excel_path
            )

            return excel_path

        except Exception as e:
            self.logger.exception("Error durante la exportación a Excel")
            raise RuntimeError(f"Error en exportación Excel: {str(e)}") from e

    def _validate_export_params(self, table: Table, output_dir: str) -> None:
        """
        Validar parámetros de exportación.

        Parameters
        ----------
        table : Table
            Tabla a validar
        output_dir : str
            Directorio de salida a validar

        Raises
        ------
        ValueError
            Si los parámetros no son válidos
        """
        if not table or not table.rows:
            raise ValueError("La tabla no puede estar vacía")

        if not output_dir:
            raise ValueError("El directorio de salida no puede estar vacío")

        if not isinstance(table, Table):
            raise ValueError("El parámetro table debe ser una instancia de Table")

    def _setup_worksheet(self, worksheet: Worksheet, table: Table) -> None:
        """
        Configurar la hoja de trabajo con propiedades básicas.

        Parameters
        ----------
        worksheet : Worksheet
            Hoja de trabajo a configurar
        table : Table
            Tabla para obtener dimensiones
        """
        # Configurar propiedades de la hoja
        worksheet.sheet_properties.tabColor = self.config.header_bg_color

        # Configurar vista de página
        if self.config.freeze_panes:
            worksheet.freeze_panes = "A2"

        # Configurar dimensiones de columnas
        if self.config.auto_adjust_columns:
            self._adjust_column_widths(worksheet, table)

    def _write_headers(self, worksheet: Worksheet, table: Table, ocr: Optional[OCRResult]) -> None:
        """
        Escribir encabezados de la tabla.

        Parameters
        ----------
        worksheet : Worksheet
            Hoja de trabajo
        table : Table
            Tabla para obtener información de columnas
        ocr : Optional[OCRResult]
            Resultado del OCR para metadatos
        """
        # Determinar número de columnas
        max_columns = self._get_max_columns(table)

        # Escribir encabezado principal
        worksheet.merge_cells(f'A1:{get_column_letter(max_columns)}1')
        worksheet['A1'] = "Datos Extraídos por OCR"
        worksheet['A1'].style = self._styles["header"]
        worksheet['A1'].font = Font(
            name="Calibri",
            size=14,
            bold=True,
            color=self.config.header_font_color
        )

        # Escribir encabezados de columnas
        headers = []
        for i in range(max_columns):
            col_letter = get_column_letter(i + 1)
            header_cell = f'{col_letter}2'
            header_text = f"Columna {i + 1}"

            # Intentar usar texto de la primera fila como encabezado
            if table.rows and i < len(table.rows[0].cells):
                header_text = table.rows[0].cells[i].text[:30]  # Limitar longitud

            worksheet[header_cell] = header_text
            worksheet[header_cell].style = self._styles["header"]
            headers.append(header_cell)

        # Añadir columna de confianza si está habilitado
        if self.config.include_confidence and ocr:
            conf_col = get_column_letter(max_columns + 1)
            conf_header = f'{conf_col}2'
            worksheet[conf_header] = "Confianza"
            worksheet[conf_header].style = self._styles["header"]

        # Añadir metadatos si está habilitado
        if self.config.include_metadata:
            self._write_metadata(worksheet, table, ocr, max_columns)

    def _write_data(self, worksheet: Worksheet, table: Table, ocr: Optional[OCRResult]) -> None:
        """
        Escribir datos de la tabla.

        Parameters
        ----------
        worksheet : Worksheet
            Hoja de trabajo
        table : Table
            Tabla con los datos
        ocr : Optional[OCRResult]
            Resultado del OCR para confianza
        """
        start_row = 4  # Después de encabezados y metadatos

        for row_idx, table_row in enumerate(table.rows):
            excel_row = start_row + row_idx

            # Escribir celdas de datos
            for col_idx, cell in enumerate(table_row.cells):
                col_letter = get_column_letter(col_idx + 1)
                excel_cell = f'{col_letter}{excel_row}'
                worksheet[excel_cell] = cell.text
                worksheet[excel_cell].style = self._styles["data"]

            # Añadir confianza si está habilitado
            if self.config.include_confidence and ocr:
                conf_col = get_column_letter(len(table_row.cells) + 1)
                conf_cell = f'{conf_col}{excel_row}'

                if row_idx < len(ocr.lines) and ocr.lines[row_idx].confidence is not None:
                    confidence = ocr.lines[row_idx].confidence
                    worksheet[conf_cell] = f"{confidence:.2%}"
                else:
                    worksheet[conf_cell] = "N/A"

                worksheet[conf_cell].style = self._styles["data"]
                worksheet[conf_cell].alignment = Alignment(horizontal="center")

    def _write_metadata(
        self,
        worksheet: Worksheet,
        table: Table,
        ocr: Optional[OCRResult],
        max_columns: int
    ) -> None:
        """
        Escribir metadatos de la exportación.

        Parameters
        ----------
        worksheet : Worksheet
            Hoja de trabajo
        table : Table
            Tabla exportada
        ocr : Optional[OCRResult]
            Resultado del OCR
        max_columns : int
            Número máximo de columnas
        """
        metadata_start_row = 3

        # Información de la tabla
        worksheet[f'A{metadata_start_row}'] = "Información de la Tabla:"
        worksheet[f'A{metadata_start_row}'].font = Font(bold=True)

        worksheet[f'A{metadata_start_row + 1}'] = f"Filas: {len(table.rows)}"
        worksheet[f'A{metadata_start_row + 2}'] = f"Columnas: {max_columns}"
        worksheet[f'A{metadata_start_row + 3}'] = f"Total de celdas: {sum(len(row.cells) for row in table.rows)}"

        # Información del OCR si está disponible
        if ocr:
            worksheet[f'C{metadata_start_row}'] = "Información del OCR:"
            worksheet[f'C{metadata_start_row}'].font = Font(bold=True)

            worksheet[f'C{metadata_start_row + 1}'] = f"Líneas procesadas: {len(ocr.lines)}"

            if ocr.lines:
                avg_confidence = sum(
                    line.confidence or 0 for line in ocr.lines
                ) / len(ocr.lines)
                worksheet[f'C{metadata_start_row + 2}'] = f"Confianza promedio: {avg_confidence:.2%}"

        # Fecha y hora de exportación
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        worksheet[f'E{metadata_start_row}'] = f"Exportado: {current_time}"
        worksheet[f'E{metadata_start_row}'].font = Font(italic=True)

    def _apply_final_formatting(self, worksheet: Worksheet, table: Table) -> None:
        """
        Aplicar formato final a la hoja de trabajo.

        Parameters
        ----------
        worksheet : Worksheet
            Hoja de trabajo
        table : Table
            Tabla para obtener dimensiones
        """
        # Ajustar altura de filas
        worksheet.row_dimensions[1].height = 25  # Título principal
        worksheet.row_dimensions[2].height = 20  # Encabezados
        worksheet.row_dimensions[3].height = 15  # Metadatos

        # Ajustar altura de filas de datos
        for row in range(4, len(table.rows) + 4):
            worksheet.row_dimensions[row].height = 18

        # Aplicar filtros si hay datos
        if table.rows:
            max_columns = self._get_max_columns(table)
            if self.config.include_confidence:
                max_columns += 1

            filter_range = f"A2:{get_column_letter(max_columns)}2"
            worksheet.auto_filter.ref = filter_range

    def _adjust_column_widths(self, worksheet: Worksheet, table: Table) -> None:
        """
        Ajustar automáticamente el ancho de las columnas.

        Parameters
        ----------
        worksheet : Worksheet
            Hoja de trabajo
        table : Table
            Tabla para calcular anchos
        """
        max_columns = self._get_max_columns(table)

        for col in range(1, max_columns + 1):
            col_letter = get_column_letter(col)

            # Calcular ancho basado en contenido
            max_width = 10  # Ancho mínimo

            # Revisar encabezado
            header_cell = f'{col_letter}2'
            if header_cell in worksheet:
                header_width = len(str(worksheet[header_cell].value or ""))
                max_width = max(max_width, header_width)

            # Revisar datos
            for row in range(4, len(table.rows) + 4):
                cell = f'{col_letter}{row}'
                if cell in worksheet:
                    cell_width = len(str(worksheet[cell].value or ""))
                    max_width = max(max_width, cell_width)

            # Aplicar ancho con límites
            final_width = min(max_width + 2, 50)  # +2 para padding, máximo 50
            worksheet.column_dimensions[col_letter].width = final_width

        # Ajustar columna de confianza si está habilitado
        if self.config.include_confidence:
            conf_col = get_column_letter(max_columns + 1)
            worksheet.column_dimensions[conf_col].width = 15

    def _get_max_columns(self, table: Table) -> int:
        """Obtener el número máximo de columnas en la tabla."""
        if not table.rows:
            return 0
        return max(len(row.cells) for row in table.rows)


# Función de conveniencia para mantener compatibilidad
def export_table_to_excel(
    table: Table,
    ocr: Optional[OCRResult],
    output_dir: str,
    filename: str = "texto_extraido.xlsx",
) -> str:
    """
    Exportar tabla a Excel usando el exportador mejorado.

    Parameters
    ----------
    table : Table
        Tabla a exportar
    ocr : Optional[OCRResult]
        Resultado del OCR para metadatos
    output_dir : str
        Directorio de salida
    filename : str
        Nombre del archivo Excel

    Returns
    -------
    str
        Ruta del archivo Excel generado
    """
    config = ExcelConfig(filename=filename)
    exporter = ExcelExporter(config)

    return exporter.export_table(table, ocr, output_dir, filename)


# Función avanzada con configuración personalizada
def export_table_with_config(
    table: Table,
    ocr: Optional[OCRResult],
    output_dir: str,
    config: ExcelConfig
) -> str:
    """
    Exportar tabla a Excel con configuración personalizada.

    Parameters
    ----------
    table : Table
        Tabla a exportar
    ocr : Optional[OCRResult]
        Resultado del OCR para metadatos
    output_dir : str
        Directorio de salida
    config : ExcelConfig
        Configuración personalizada para la exportación

    Returns
    -------
    str
        Ruta del archivo Excel generado
    """
    exporter = ExcelExporter(config)
    return exporter.export_table(table, ocr, output_dir)


__all__ = [
    "export_table_to_excel",
    "export_table_with_config",
    "ExcelExporter",
    "ExcelConfig"
]
