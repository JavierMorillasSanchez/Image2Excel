#!/usr/bin/env python3
"""
Tests para la aplicación I2E (Imagen a Excel).

Refactor: Tests completos para verificar la funcionalidad de todos los componentes
refactorizados, incluyendo OCR, parser, exportador y configuración.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Añadir el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import AppConfig, get_config, get_development_config
from core.models import OCRResult, OCRTextLine, Table, TableRow, TableCell
from services.paddle_ocr import PaddleOCREngine, OCRConfig, create_ocr_engine
from services.parser import TableParser, ParsingConfig, ocr_to_table
from services.exporter import ExcelExporter, ExcelConfig, export_table_to_excel
from infrastructure.logging_config import configure_logging, get_logger


class TestAppConfig(unittest.TestCase):
    """Tests para la configuración de la aplicación."""

    def setUp(self):
        """Configurar tests."""
        self.config = AppConfig()

    def test_default_config(self):
        """Test de configuración por defecto."""
        self.assertEqual(self.config.app_name, "Convertidor de Imagen a Excel")
        self.assertEqual(self.config.app_version, "2.0.0")
        self.assertEqual(self.config.ocr_language, "es")
        self.assertTrue(self.config.ocr_use_angle_cls)

    def test_config_validation(self):
        """Test de validación de configuración."""
        # Test de confianza válida
        self.config.ocr_min_confidence = 0.8
        self.assertEqual(self.config.ocr_min_confidence, 0.8)

        # Test de confianza inválida
        with self.assertRaises(ValueError):
            self.config.ocr_min_confidence = 1.5

        with self.assertRaises(ValueError):
            self.config.ocr_min_confidence = -0.1

    def test_get_ocr_config(self):
        """Test de obtención de configuración OCR."""
        ocr_config = self.config.get_ocr_config()
        self.assertEqual(ocr_config['language'], 'es')
        self.assertTrue(ocr_config['use_angle_cls'])
        self.assertFalse(ocr_config['use_gpu'])

    def test_get_parser_config(self):
        """Test de obtención de configuración del parser."""
        parser_config = self.config.get_parser_config()
        self.assertEqual(parser_config['min_column_width'], 3)
        self.assertEqual(parser_config['max_columns'], 20)
        self.assertTrue(parser_config['use_confidence_filtering'])

    def test_get_excel_config(self):
        """Test de obtención de configuración de Excel."""
        excel_config = self.config.get_excel_config()
        self.assertEqual(excel_config['filename'], 'texto_extraido.xlsx')
        self.assertEqual(excel_config['sheet_name'], 'Texto Extraído')
        self.assertTrue(excel_config['include_metadata'])


class TestOCRConfig(unittest.TestCase):
    """Tests para la configuración del OCR."""

    def test_ocr_config_defaults(self):
        """Test de valores por defecto de OCRConfig."""
        config = OCRConfig()
        self.assertEqual(config.language, "es")
        self.assertTrue(config.use_angle_cls)
        self.assertFalse(config.use_gpu)
        self.assertEqual(config.cpu_threads, 10)

    def test_ocr_config_custom(self):
        """Test de configuración personalizada de OCR."""
        config = OCRConfig(
            language="en",
            use_gpu=True,
            gpu_mem=1000,
            cpu_threads=20
        )
        self.assertEqual(config.language, "en")
        self.assertTrue(config.use_gpu)
        self.assertEqual(config.gpu_mem, 1000)
        self.assertEqual(config.cpu_threads, 20)


class TestParsingConfig(unittest.TestCase):
    """Tests para la configuración del parser."""

    def test_parsing_config_defaults(self):
        """Test de valores por defecto de ParsingConfig."""
        config = ParsingConfig()
        self.assertIn('\t', config.column_separators)
        self.assertIn('  ', config.column_separators)
        self.assertEqual(config.min_column_width, 3)
        self.assertEqual(config.max_columns, 20)

    def test_parsing_config_custom(self):
        """Test de configuración personalizada del parser."""
        config = ParsingConfig(
            min_column_width=5,
            max_columns=50,
            remove_special_chars=True
        )
        self.assertEqual(config.min_column_width, 5)
        self.assertEqual(config.max_columns, 50)
        self.assertTrue(config.remove_special_chars)


class TestExcelConfig(unittest.TestCase):
    """Tests para la configuración de Excel."""

    def test_excel_config_defaults(self):
        """Test de valores por defecto de ExcelConfig."""
        config = ExcelConfig()
        self.assertEqual(config.filename, "texto_extraido.xlsx")
        self.assertEqual(config.sheet_name, "Texto Extraído")
        self.assertTrue(config.include_metadata)
        self.assertTrue(config.include_confidence)

    def test_excel_config_custom(self):
        """Test de configuración personalizada de Excel."""
        config = ExcelConfig(
            filename="custom.xlsx",
            sheet_name="Custom Sheet",
            include_metadata=False
        )
        self.assertEqual(config.filename, "custom.xlsx")
        self.assertEqual(config.sheet_name, "Custom Sheet")
        self.assertFalse(config.include_metadata)


class TestCoreModels(unittest.TestCase):
    """Tests para los modelos del core."""

    def test_ocr_text_line(self):
        """Test de OCRTextLine."""
        line = OCRTextLine(text="Test text", confidence=0.95)
        self.assertEqual(line.text, "Test text")
        self.assertEqual(line.confidence, 0.95)

    def test_ocr_result(self):
        """Test de OCRResult."""
        lines = [
            OCRTextLine(text="Line 1", confidence=0.9),
            OCRTextLine(text="Line 2", confidence=0.8)
        ]
        result = OCRResult(lines=lines)
        self.assertEqual(len(result.lines), 2)
        self.assertEqual(result.lines[0].text, "Line 1")

    def test_table_cell(self):
        """Test de TableCell."""
        cell = TableCell(text="Cell content")
        self.assertEqual(cell.text, "Cell content")

    def test_table_row(self):
        """Test de TableRow."""
        cells = [TableCell(text="Cell 1"), TableCell(text="Cell 2")]
        row = TableRow(cells=cells)
        self.assertEqual(len(row.cells), 2)
        self.assertEqual(row.cells[0].text, "Cell 1")

    def test_table(self):
        """Test de Table."""
        rows = [
            TableRow(cells=[TableCell(text="A1"), TableCell(text="A2")]),
            TableRow(cells=[TableCell(text="B1"), TableCell(text="B2")])
        ]
        table = Table(rows=rows)
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(len(table.rows[0].cells), 2)


class TestTableParser(unittest.TestCase):
    """Tests para el parser de tablas."""

    def setUp(self):
        """Configurar tests."""
        self.config = ParsingConfig()
        self.parser = TableParser(self.config)

        # Crear datos de prueba
        self.test_lines = [
            Mock(text="Col1\tCol2\tCol3", confidence=0.9),
            Mock(text="Data1\tData2\tData3", confidence=0.8),
            Mock(text="More1\tMore2\tMore3", confidence=0.7)
        ]

    def test_parser_initialization(self):
        """Test de inicialización del parser."""
        self.assertIsNotNone(self.parser)
        self.assertEqual(self.parser.config.min_column_width, 3)
        self.assertEqual(self.parser.config.max_columns, 20)

    def test_compile_separators(self):
        """Test de compilación de separadores."""
        patterns = self.parser._separator_patterns
        self.assertGreater(len(patterns), 0)

        # Verificar que se compilaron correctamente
        for pattern in patterns:
            self.assertIsNotNone(pattern)

    def test_split_line_into_columns(self):
        """Test de división de líneas en columnas."""
        text = "Col1\tCol2\tCol3"
        columns = self.parser._split_line_into_columns(text)
        self.assertEqual(len(columns), 3)
        self.assertEqual(columns[0], "Col1")
        self.assertEqual(columns[1], "Col2")
        self.assertEqual(columns[2], "Col3")

    def test_split_line_with_spaces(self):
        """Test de división con espacios múltiples."""
        text = "Col1  Col2  Col3"
        columns = self.parser._split_line_into_columns(text)
        self.assertEqual(len(columns), 3)

    def test_parse_ocr_to_table(self):
        """Test de parseo completo de OCR a tabla."""
        # Crear OCRResult de prueba
        ocr_result = OCRResult(lines=self.test_lines)

        # Parsear
        table, metrics = self.parser.parse_ocr_to_table(ocr_result)

        # Verificar resultados
        self.assertIsNotNone(table)
        self.assertIsNotNone(metrics)
        self.assertEqual(len(table.rows), 3)
        self.assertEqual(metrics.total_lines, 3)
        self.assertEqual(metrics.processed_lines, 3)
        self.assertGreater(metrics.confidence_score, 0)

    def test_filter_lines_by_confidence(self):
        """Test de filtrado por confianza."""
        # Configurar umbral bajo
        self.parser.config.min_confidence_threshold = 0.85

        filtered = self.parser._filter_lines_by_confidence(self.test_lines, Mock())
        self.assertEqual(len(filtered), 1)  # Solo la línea con confianza 0.9

    def test_detect_table_structure(self):
        """Test de detección de estructura de tabla."""
        structure = self.parser._detect_table_structure(self.test_lines)
        self.assertIsNotNone(structure)
        self.assertIn('column_count', structure)
        self.assertIn('main_separator', structure)

    def test_calculate_confidence_score(self):
        """Test de cálculo de score de confianza."""
        rows = [
            TableRow(cells=[TableCell(text="A1"), TableCell(text="A2")]),
            TableRow(cells=[TableCell(text="B1"), TableCell(text="B2")])
        ]

        score = self.parser._calculate_confidence_score(rows, self.test_lines)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestExcelExporter(unittest.TestCase):
    """Tests para el exportador de Excel."""

    def setUp(self):
        """Configurar tests."""
        self.config = ExcelConfig()
        self.exporter = ExcelExporter(self.config)

        # Crear tabla de prueba
        self.test_table = Table(rows=[
            TableRow(cells=[TableCell(text="Header1"), TableCell(text="Header2")]),
            TableRow(cells=[TableCell(text="Data1"), TableCell(text="Data2")])
        ])

        # Crear OCR de prueba
        self.test_ocr = OCRResult(lines=[
            Mock(text="Header1\tHeader2", confidence=0.9),
            Mock(text="Data1\tData2", confidence=0.8)
        ])

    def test_exporter_initialization(self):
        """Test de inicialización del exportador."""
        self.assertIsNotNone(self.exporter)
        self.assertEqual(self.exporter.config.filename, "texto_extraido.xlsx")
        self.assertTrue(self.exporter.config.include_metadata)

    def test_initialize_styles(self):
        """Test de inicialización de estilos."""
        self.assertIn("header", self.exporter._styles)
        self.assertIn("data", self.exporter._styles)

        header_style = self.exporter._styles["header"]
        self.assertIsNotNone(header_style.font)
        self.assertIsNotNone(header_style.fill)

    def test_validate_export_params(self):
        """Test de validación de parámetros."""
        # Test válido
        self.exporter._validate_export_params(self.test_table, "/tmp")

        # Test inválido - tabla vacía
        with self.assertRaises(ValueError):
            self.exporter._validate_export_params(Table(rows=[]), "/tmp")

        # Test inválido - directorio vacío
        with self.assertRaises(ValueError):
            self.exporter._validate_export_params(self.test_table, "")

    def test_get_max_columns(self):
        """Test de obtención de columnas máximas."""
        max_cols = self.exporter._get_max_columns(self.test_table)
        self.assertEqual(max_cols, 2)

    def test_export_table(self):
        """Test de exportación completa."""
        with tempfile.TemporaryDirectory() as temp_dir:
            excel_path = self.exporter.export_table(
                self.test_table,
                self.test_ocr,
                temp_dir
            )

            # Verificar que se creó el archivo
            self.assertTrue(os.path.exists(excel_path))
            self.assertTrue(excel_path.endswith('.xlsx'))

            # Verificar tamaño del archivo
            file_size = os.path.getsize(excel_path)
            self.assertGreater(file_size, 0)


class TestIntegration(unittest.TestCase):
    """Tests de integración entre componentes."""

    def setUp(self):
        """Configurar tests."""
        self.config = get_development_config()

        # Configurar logging para tests
        configure_logging(
            level=logging.WARNING,
            log_to_file=False,
            log_to_console=False
        )

    def test_end_to_end_workflow(self):
        """Test del flujo completo de trabajo."""
        # Crear datos de prueba
        test_lines = [
            OCRTextLine(text="Name\tAge\tCity", confidence=0.9),
            OCRTextLine(text="John\t25\tMadrid", confidence=0.8),
            OCRTextLine(text="Jane\t30\tBarcelona", confidence=0.85)
        ]

        ocr_result = OCRResult(lines=test_lines)

        # Parsear OCR a tabla
        table = ocr_to_table(ocr_result)
        self.assertEqual(len(table.rows), 3)
        self.assertEqual(len(table.rows[0].cells), 3)

        # Exportar a Excel
        with tempfile.TemporaryDirectory() as temp_dir:
            excel_path = export_table_to_excel(
                table, ocr_result, temp_dir, "test_output.xlsx"
            )

            # Verificar archivo generado
            self.assertTrue(os.path.exists(excel_path))
            self.assertTrue(excel_path.endswith('.xlsx'))

    def test_configuration_integration(self):
        """Test de integración de configuración."""
        # Verificar que la configuración se puede usar en todos los componentes
        config = self.config

        # Parser
        parser_config = ParsingConfig(**config.get_parser_config())
        self.assertEqual(parser_config.min_column_width, 3)

        # Excel
        excel_config = ExcelConfig(**config.get_excel_config())
        self.assertEqual(excel_config.filename, "texto_extraido.xlsx")

        # OCR
        ocr_config = OCRConfig(**config.get_ocr_config())
        self.assertEqual(ocr_config.language, "es")


class TestErrorHandling(unittest.TestCase):
    """Tests de manejo de errores."""

    def test_parser_error_handling(self):
        """Test de manejo de errores en el parser."""
        parser = TableParser()

        # Test con datos inválidos
        invalid_ocr = OCRResult(lines=[])
        table, metrics = parser.parse_ocr_to_table(invalid_ocr)

        # Debe devolver tabla vacía pero válida
        self.assertIsNotNone(table)
        self.assertEqual(len(table.rows), 0)
        self.assertIsNotNone(metrics)

    def test_exporter_error_handling(self):
        """Test de manejo de errores en el exportador."""
        exporter = ExcelExporter()

        # Test con parámetros inválidos
        with self.assertRaises(ValueError):
            exporter._validate_export_params(Table(rows=[]), "/tmp")

        with self.assertRaises(ValueError):
            exporter._validate_export_params(None, "/tmp")


def run_tests():
    """Ejecutar todos los tests."""
    # Configurar logging para tests
    configure_logging(
        level=logging.WARNING,
        log_to_file=False,
        log_to_console=False
    )

    # Crear suite de tests
    test_suite = unittest.TestSuite()

    # Añadir tests
    test_classes = [
        TestAppConfig,
        TestOCRConfig,
        TestParsingConfig,
        TestExcelConfig,
        TestCoreModels,
        TestTableParser,
        TestExcelExporter,
        TestIntegration,
        TestErrorHandling
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Retornar código de salida
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    # Ejecutar tests
    exit_code = run_tests()
    sys.exit(exit_code)
