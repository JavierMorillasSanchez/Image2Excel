"""Parser to convert OCR text lines into a structured table.

Refactor aplicado:
- Implementado algoritmo inteligente de detección de tablas
- Mejorado el procesamiento de texto con limpieza y normalización
- Añadida detección automática de columnas basada en alineación
- Soporte para diferentes tipos de separadores y formatos
- Validación robusta de datos y manejo de errores
- Métricas de calidad para evaluar la precisión del parseo
"""
from __future__ import annotations

import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

from core.models import OCRResult, Table, TableRow, TableCell
from infrastructure.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ParsingConfig:
    """Configuración para el parser de tablas."""

    # Separadores para detectar columnas
    column_separators: List[str] = None
    min_column_width: int = 3
    max_columns: int = 20

    # Configuración de limpieza de texto
    remove_extra_spaces: bool = True
    normalize_whitespace: bool = True
    remove_special_chars: bool = False

    # Configuración de detección de tablas
    min_confidence_threshold: float = 0.5
    use_confidence_filtering: bool = True
    detect_table_structure: bool = True

    def __post_init__(self):
        """Inicializar valores por defecto."""
        if self.column_separators is None:
            self.column_separators = ['\t', '  ', '|', ';', ',']


@dataclass
class ParsingMetrics:
    """Métricas de calidad del parseo."""

    total_lines: int = 0
    processed_lines: int = 0
    detected_columns: int = 0
    confidence_score: float = 0.0
    parsing_time: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        """Inicializar lista de errores."""
        if self.errors is None:
            self.errors = []


class TableParser:
    """
    Parser inteligente para convertir resultados OCR en tablas estructuradas.

    Refactor: Implementado algoritmo avanzado de detección de tablas con métricas de calidad
    """

    def __init__(self, config: Optional[ParsingConfig] = None):
        """
        Inicializar el parser de tablas.

        Parameters
        ----------
        config : Optional[ParsingConfig]
            Configuración personalizada para el parser
        """
        self.config = config or ParsingConfig()
        self.logger = get_logger(self.__class__.__name__)

        # Compilar regex para separadores
        self._separator_patterns = self._compile_separators()

        self.logger.info(
            "TableParser inicializado con configuración: "
            "separadores=%s, min_column_width=%d, max_columns=%d",
            self.config.column_separators, self.config.min_column_width,
            self.config.max_columns
        )

    def _compile_separators(self) -> List[re.Pattern]:
        """Compilar patrones regex para separadores."""
        patterns = []
        for separator in self.config.column_separators:
            if separator == '\t':
                patterns.append(re.compile(r'\t+'))
            elif separator == '  ':
                patterns.append(re.compile(r'\s{2,}'))
            else:
                # Escapar caracteres especiales
                escaped = re.escape(separator)
                patterns.append(re.compile(f'{escaped}+'))
        return patterns

    def parse_ocr_to_table(self, ocr: OCRResult) -> Tuple[Table, ParsingMetrics]:
        """
        Parsear resultado OCR a tabla estructurada.

        Parameters
        ----------
        ocr : OCRResult
            Resultado del OCR a procesar

        Returns
        -------
        Tuple[Table, ParsingMetrics]
            Tabla parseada y métricas de calidad
        """
        import time
        start_time = time.time()

        metrics = ParsingMetrics(total_lines=len(ocr.lines))

        try:
            self.logger.info("Iniciando parseo de %d líneas OCR", len(ocr.lines))

            # Filtrar líneas por confianza si está habilitado
            filtered_lines = self._filter_lines_by_confidence(ocr.lines, metrics)

            # Detectar estructura de tabla
            if self.config.detect_table_structure:
                table_structure = self._detect_table_structure(filtered_lines)
            else:
                table_structure = self._simple_table_structure(filtered_lines)

            # Parsear líneas a filas de tabla
            rows = self._parse_lines_to_rows(filtered_lines, table_structure, metrics)

            # Crear tabla final
            table = Table(rows=rows)

            # Calcular métricas finales
            metrics.processed_lines = len(rows)
            metrics.detected_columns = self._count_columns(rows)
            metrics.parsing_time = time.time() - start_time
            metrics.confidence_score = self._calculate_confidence_score(rows, ocr.lines)

            self.logger.info(
                "Parseo completado: %d filas, %d columnas, tiempo=%.3fs, "
                "confianza=%.2f",
                len(rows), metrics.detected_columns, metrics.parsing_time,
                metrics.confidence_score
            )

            return table, metrics

        except Exception as e:
            error_msg = f"Error durante el parseo: {str(e)}"
            self.logger.exception(error_msg)
            metrics.errors.append(error_msg)

            # Devolver tabla vacía en caso de error
            return Table(rows=[]), metrics

    def _filter_lines_by_confidence(
        self,
        lines: List[Any],
        metrics: ParsingMetrics
    ) -> List[Any]:
        """
        Filtrar líneas por umbral de confianza.

        Parameters
        ----------
        lines : List[Any]
            Líneas OCR a filtrar
        metrics : ParsingMetrics
            Métricas para actualizar

        Returns
        -------
        List[Any]
            Líneas filtradas
        """
        if not self.config.use_confidence_filtering:
            return lines

        filtered = []
        for line in lines:
            if hasattr(line, 'confidence') and line.confidence is not None:
                if line.confidence >= self.config.min_confidence_threshold:
                    filtered.append(line)
                else:
                    self.logger.debug(
                        "Línea filtrada por baja confianza (%.2f): '%s'",
                        line.confidence, line.text[:50]
                    )
            else:
                # Si no hay confianza, incluir la línea
                filtered.append(line)

        self.logger.info(
            "Filtrado por confianza: %d/%d líneas mantenidas",
            len(filtered), len(lines)
        )

        return filtered

    def _detect_table_structure(self, lines: List[Any]) -> Dict[str, Any]:
        """
        Detectar estructura de tabla analizando patrones en las líneas.

        Parameters
        ----------
        lines : List[Any]
            Líneas OCR a analizar

        Returns
        -------
        Dict[str, Any]
            Información de la estructura de tabla detectada
        """
        if not lines:
            return {'column_count': 0, 'separators': [], 'alignment': 'left'}

        # Analizar patrones de separación
        separator_counts = defaultdict(int)
        column_counts = []

        for line in lines:
            if not hasattr(line, 'text') or not line.text:
                continue

            text = line.text.strip()
            if not text:
                continue

            # Contar ocurrencias de cada separador
            for pattern in self._separator_patterns:
                matches = len(pattern.findall(text))
                if matches > 0:
                    separator_counts[pattern.pattern] += matches

            # Contar columnas potenciales
            columns = self._split_line_into_columns(text)
            column_counts.append(len(columns))

        # Determinar separador principal
        main_separator = None
        if separator_counts:
            main_separator = max(separator_counts.items(), key=lambda x: x[1])[0]

        # Determinar número de columnas
        if column_counts:
            # Usar la mediana para evitar outliers
            column_counts.sort()
            median_columns = column_counts[len(column_counts) // 2]
            column_count = min(median_columns, self.config.max_columns)
        else:
            column_count = 0

        structure = {
            'column_count': column_count,
            'main_separator': main_separator,
            'separator_counts': dict(separator_counts),
            'column_distribution': column_counts,
            'alignment': 'left'  # Por defecto
        }

        self.logger.debug(
            "Estructura de tabla detectada: %d columnas, separador='%s'",
            column_count, main_separator
        )

        return structure

    def _simple_table_structure(self, lines: List[Any]) -> Dict[str, Any]:
        """
        Estructura de tabla simple para casos básicos.

        Parameters
        ----------
        lines : List[Any]
            Líneas OCR

        Returns
        -------
        Dict[str, Any]
            Estructura básica de tabla
        """
        return {
            'column_count': 0,
            'main_separator': None,
            'separator_counts': {},
            'column_distribution': [],
            'alignment': 'left'
        }

    def _parse_lines_to_rows(
        self,
        lines: List[Any],
        structure: Dict[str, Any],
        metrics: ParsingMetrics
    ) -> List[TableRow]:
        """
        Parsear líneas OCR a filas de tabla.

        Parameters
        ----------
        lines : List[Any]
            Líneas OCR a procesar
        structure : Dict[str, Any]
            Estructura de tabla detectada
        metrics : ParsingMetrics
            Métricas para actualizar

        Returns
        -------
        List[TableRow]
            Filas de tabla parseadas
        """
        rows = []

        for i, line in enumerate(lines):
            try:
                if not hasattr(line, 'text') or not line.text:
                    continue

                text = line.text.strip()
                if not text:
                    continue

                # Dividir línea en columnas
                cells = self._split_line_into_columns(text, structure)

                # Crear fila de tabla
                table_cells = [TableCell(text=cell.strip()) for cell in cells if cell.strip()]

                if table_cells:  # Solo añadir filas con contenido
                    row = TableRow(cells=table_cells)
                    rows.append(row)

                    self.logger.debug(
                        "Fila %d parseada: %d celdas, texto='%s...'",
                        i + 1, len(table_cells), text[:50]
                    )

            except Exception as e:
                error_msg = f"Error parseando línea {i + 1}: {str(e)}"
                self.logger.warning(error_msg)
                metrics.errors.append(error_msg)
                continue

        return rows

    def _split_line_into_columns(
        self,
        text: str,
        structure: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Dividir una línea de texto en columnas.

        Parameters
        ----------
        text : str
            Texto a dividir
        structure : Optional[Dict[str, Any]]
            Estructura de tabla para guiar la división

        Returns
        -------
        List[str]
            Lista de columnas
        """
        if not text:
            return []

        # Limpiar texto si está habilitado
        if self.config.remove_extra_spaces:
            text = re.sub(r'\s+', ' ', text)

        if self.config.normalize_whitespace:
            text = ' '.join(text.split())

        # Intentar dividir usando el separador principal si está disponible
        if structure and structure.get('main_separator'):
            separator = structure['main_separator']
            if separator == r'\t+':
                columns = re.split(r'\t+', text)
            elif separator == r'\s{2,}':
                columns = re.split(r'\s{2,}', text)
            else:
                # Escapar caracteres especiales
                escaped = re.escape(separator.replace('+', ''))
                columns = re.split(f'{escaped}+', text)
        else:
            # Fallback: usar todos los separadores disponibles
            columns = [text]
            for pattern in self._separator_patterns:
                new_columns = []
                for col in columns:
                    if pattern.pattern == r'\t+':
                        new_columns.extend(re.split(r'\t+', col))
                    elif pattern.pattern == r'\s{2,}':
                        new_columns.extend(re.split(r'\s{2,}', col))
                    else:
                        escaped = re.escape(pattern.pattern.replace('+', ''))
                        new_columns.extend(re.split(f'{escaped}+', col))
                columns = new_columns

        # Filtrar columnas vacías y muy cortas
        filtered_columns = [
            col.strip() for col in columns
            if col.strip() and len(col.strip()) >= self.config.min_column_width
        ]

        return filtered_columns

    def _count_columns(self, rows: List[TableRow]) -> int:
        """Contar el número máximo de columnas en las filas."""
        if not rows:
            return 0
        return max(len(row.cells) for row in rows)

    def _calculate_confidence_score(
        self,
        rows: List[TableRow],
        original_lines: List[Any]
    ) -> float:
        """
        Calcular score de confianza basado en la calidad del parseo.

        Parameters
        ----------
        rows : List[TableRow]
            Filas parseadas
        original_lines : List[Any]
            Líneas originales del OCR

        Returns
        -------
        float
            Score de confianza entre 0.0 y 1.0
        """
        if not rows or not original_lines:
            return 0.0

        # Calcular métricas de calidad
        total_cells = sum(len(row.cells) for row in rows)
        avg_cells_per_row = total_cells / len(rows) if rows else 0

        # Factor de completitud (cuántas líneas se procesaron)
        completeness = len(rows) / len(original_lines) if original_lines else 0

        # Factor de consistencia (variación en número de columnas)
        column_counts = [len(row.cells) for row in rows]
        if column_counts:
            std_dev = (sum((x - avg_cells_per_row) ** 2 for x in column_counts) / len(column_counts)) ** 0.5
            consistency = max(0, 1 - (std_dev / avg_cells_per_row)) if avg_cells_per_row > 0 else 0
        else:
            consistency = 0

        # Score final ponderado
        confidence = (completeness * 0.4 + consistency * 0.6)

        return max(0.0, min(1.0, confidence))


# Función de conveniencia para mantener compatibilidad
def ocr_to_table(ocr: OCRResult) -> Table:
    """
    Convertir resultado OCR a tabla usando el parser mejorado.

    Parameters
    ----------
    ocr : OCRResult
        Resultado del OCR a procesar

    Returns
    -------
    Table
        Tabla parseada
    """
    parser = TableParser()
    table, metrics = parser.parse_ocr_to_table(ocr)

    # Log de métricas
    logger = get_logger(__name__)
    logger.info(
        "Parseo OCR completado: %d filas, %d columnas, confianza=%.2f",
        metrics.processed_lines, metrics.detected_columns, metrics.confidence_score
    )

    return table


# Función avanzada con configuración personalizada
def parse_ocr_with_config(
    ocr: OCRResult,
    config: ParsingConfig
) -> Tuple[Table, ParsingMetrics]:
    """
    Parsear OCR con configuración personalizada.

    Parameters
    ----------
    ocr : OCRResult
        Resultado del OCR a procesar
    config : ParsingConfig
        Configuración personalizada para el parser

    Returns
    -------
    Tuple[Table, ParsingMetrics]
        Tabla parseada y métricas detalladas
    """
    parser = TableParser(config)
    return parser.parse_ocr_to_table(ocr)


__all__ = [
    "ocr_to_table",
    "parse_ocr_with_config",
    "TableParser",
    "ParsingConfig",
    "ParsingMetrics"
]
