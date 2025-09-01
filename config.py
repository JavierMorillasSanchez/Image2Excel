"""
Configuración centralizada de la aplicación I2E (Imagen a Excel).

Refactor: Centralizada toda la configuración en un solo lugar para facilitar
mantenimiento y personalización de la aplicación.
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AppConfig:
    """Configuración principal de la aplicación."""

    # Información de la aplicación
    app_name: str = "Convertidor de Imagen a Excel"
    app_version: str = "2.0.0"
    app_description: str = "Aplicación de escritorio para convertir imágenes a Excel usando OCR"
    organization: str = "Tu Organización"

    # Configuración de la ventana principal
    window_title: str = "Convertidor de Imagen a Excel"
    window_width: int = 500
    window_height: int = 450
    center_window: bool = True

    # Configuración de logging
    logging_level: int = logging.INFO
    logging_to_file: bool = True
    logging_to_console: bool = True
    log_directory: str = "logs"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # Configuración de OCR
    ocr_language: str = "es"
    ocr_use_angle_cls: bool = True
    ocr_use_gpu: bool = False
    ocr_gpu_mem: int = 500
    ocr_cpu_threads: int = 10
    ocr_enable_mkldnn: bool = True
    ocr_det_db_thresh: float = 0.3
    ocr_det_db_box_thresh: float = 0.5
    ocr_det_db_unclip_ratio: float = 1.6
    ocr_rec_batch_num: int = 6
    ocr_cls_batch_num: int = 6
    ocr_cls_thresh: float = 0.9
    ocr_min_confidence: float = 0.5

    # Configuración de parser
    parser_min_column_width: int = 3
    parser_max_columns: int = 20
    parser_remove_extra_spaces: bool = True
    parser_normalize_whitespace: bool = True
    parser_remove_special_chars: bool = False
    parser_use_confidence_filtering: bool = True
    parser_detect_table_structure: bool = True

    # Configuración de exportación Excel
    excel_default_filename: str = "texto_extraido.xlsx"
    excel_sheet_name: str = "Texto Extraído"
    excel_include_metadata: bool = True
    excel_include_confidence: bool = True
    excel_auto_adjust_columns: bool = True
    excel_freeze_panes: bool = True
    excel_header_bg_color: str = "366092"
    excel_header_font_color: str = "FFFFFF"
    excel_data_bg_color: str = "FFFFFF"
    excel_data_font_color: str = "000000"
    excel_border_color: str = "CCCCCC"
    excel_header_font_size: int = 12
    excel_data_font_size: int = 10

    # Configuración de archivos
    supported_image_formats: List[str] = field(default_factory=lambda: [
        "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.tiff", "*.gif"
    ])
    supported_image_extensions: List[str] = field(default_factory=lambda: [
        ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"
    ])
    max_image_size_mb: int = 100

    # Configuración de UI
    ui_colors: Dict[str, str] = field(default_factory=lambda: {
        'primary_100': '#1E88E5',    # Azul principal
        'primary_200': '#6ab7ff',    # Azul claro
        'primary_300': '#dbffff',    # Azul muy claro
        'accent_100': '#000000',     # Negro
        'accent_200': '#818181',     # Gris
        'text_100': '#FFFFFF',       # Blanco
        'text_200': '#e0e0e0',       # Gris claro
        'bg_100': '#FFFFFF',         # Blanco de fondo
        'bg_200': '#f5f5f5',         # Gris muy claro
        'bg_300': '#cccccc'          # Gris claro
    })

    # Configuración de rendimiento
    max_worker_threads: int = 2
    processing_timeout: int = 300  # 5 minutos
    memory_limit_mb: int = 1024    # 1GB

    # Configuración de desarrollo
    debug_mode: bool = False
    show_performance_metrics: bool = False
    enable_profiling: bool = False

    def __post_init__(self):
        """Validar y ajustar configuración después de la inicialización."""
        self._validate_config()
        self._adjust_paths()

    def _validate_config(self):
        """Validar valores de configuración."""
        if self.ocr_min_confidence < 0 or self.ocr_min_confidence > 1:
            raise ValueError("ocr_min_confidence debe estar entre 0 y 1")

        if self.parser_min_column_width < 1:
            raise ValueError("parser_min_column_width debe ser mayor que 0")

        if self.parser_max_columns < 1:
            raise ValueError("parser_max_columns debe ser mayor que 0")

        if self.max_image_size_mb < 1:
            raise ValueError("max_image_size_mb debe ser mayor que 0")

    def _adjust_paths(self):
        """Ajustar rutas relativas a absolutas."""
        # Convertir directorio de logs a ruta absoluta
        if not os.path.isabs(self.log_directory):
            self.log_directory = os.path.join(os.getcwd(), self.log_directory)

    def get_ocr_config(self) -> Dict[str, Any]:
        """Obtener configuración para el motor OCR."""
        return {
            'language': self.ocr_language,
            'use_angle_cls': self.ocr_use_angle_cls,
            'use_gpu': self.ocr_use_gpu,
            'gpu_mem': self.ocr_gpu_mem,
            'cpu_threads': self.ocr_cpu_threads,
            'enable_mkldnn': self.ocr_enable_mkldnn,
            'det_db_thresh': self.ocr_det_db_thresh,
            'det_db_box_thresh': self.ocr_det_db_box_thresh,
            'det_db_unclip_ratio': self.ocr_det_db_unclip_ratio,
            'rec_batch_num': self.ocr_rec_batch_num,
            'cls_batch_num': self.ocr_cls_batch_num,
            'cls_thresh': self.ocr_cls_thresh
        }

    def get_parser_config(self) -> Dict[str, Any]:
        """Obtener configuración para el parser de tablas."""
        return {
            'min_column_width': self.parser_min_column_width,
            'max_columns': self.parser_max_columns,
            'remove_extra_spaces': self.parser_remove_extra_spaces,
            'normalize_whitespace': self.parser_normalize_whitespace,
            'remove_special_chars': self.parser_remove_special_chars,
            'use_confidence_filtering': self.parser_use_confidence_filtering,
            'detect_table_structure': self.parser_detect_table_structure,
            'min_confidence_threshold': self.ocr_min_confidence
        }

    def get_excel_config(self) -> Dict[str, Any]:
        """Obtener configuración para el exportador de Excel."""
        return {
            'filename': self.excel_default_filename,
            'sheet_name': self.excel_sheet_name,
            'include_metadata': self.excel_include_metadata,
            'include_confidence': self.excel_include_confidence,
            'auto_adjust_columns': self.excel_auto_adjust_columns,
            'freeze_panes': self.excel_freeze_panes,
            'header_bg_color': self.excel_header_bg_color,
            'header_font_color': self.excel_header_font_color,
            'data_bg_color': self.excel_data_bg_color,
            'data_font_color': self.excel_data_font_color,
            'border_color': self.excel_border_color,
            'header_font_size': self.excel_header_font_size,
            'data_font_size': self.excel_data_font_size
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """Obtener configuración para el sistema de logging."""
        return {
            'level': self.logging_level,
            'log_to_file': self.logging_to_file,
            'log_to_console': self.logging_to_console,
            'log_dir': self.log_directory,
            'max_file_size': self.log_max_size,
            'backup_count': self.log_backup_count
        }


# Configuraciones predefinidas
def get_development_config() -> AppConfig:
    """Configuración optimizada para desarrollo."""
    config = AppConfig()
    config.logging_level = logging.DEBUG
    config.debug_mode = True
    config.show_performance_metrics = True
    config.enable_profiling = True
    config.log_max_size = 5 * 1024 * 1024  # 5MB para desarrollo
    config.log_backup_count = 3
    return config


def get_production_config() -> AppConfig:
    """Configuración optimizada para producción."""
    config = AppConfig()
    config.logging_level = logging.WARNING
    config.logging_to_console = False
    config.debug_mode = False
    config.show_performance_metrics = False
    config.enable_profiling = False
    config.log_max_size = 50 * 1024 * 1024  # 50MB para producción
    config.log_backup_count = 10
    return config


def get_test_config() -> AppConfig:
    """Configuración optimizada para testing."""
    config = AppConfig()
    config.logging_level = logging.WARNING
    config.logging_to_file = False
    config.logging_to_console = False
    config.debug_mode = False
    config.max_worker_threads = 1
    config.processing_timeout = 60
    return config


# Función principal para obtener configuración
def get_config(environment: str = "development") -> AppConfig:
    """
    Obtener configuración según el entorno.

    Parameters
    ----------
    environment : str
        Entorno de ejecución ("development", "production", "test")

    Returns
    -------
    AppConfig
        Configuración correspondiente al entorno
    """
    environment = environment.lower()

    if environment == "production":
        return get_production_config()
    elif environment == "test":
        return get_test_config()
    else:
        return get_development_config()


# Configuración por defecto
DEFAULT_CONFIG = get_config()

# Variables de entorno que pueden sobrescribir la configuración
def load_config_from_env(config: AppConfig) -> AppConfig:
    """
    Cargar configuración desde variables de entorno.

    Parameters
    ----------
    config : AppConfig
        Configuración base

    Returns
    -------
    AppConfig
        Configuración actualizada con variables de entorno
    """
    # Logging
    if os.getenv('I2E_LOG_LEVEL'):
        try:
            level_name = os.getenv('I2E_LOG_LEVEL').upper()
            config.logging_level = getattr(logging, level_name, logging.INFO)
        except (ValueError, AttributeError):
            pass

    if os.getenv('I2E_LOG_TO_FILE'):
        config.logging_to_file = os.getenv('I2E_LOG_TO_FILE').lower() == 'true'

    if os.getenv('I2E_LOG_TO_CONSOLE'):
        config.logging_to_console = os.getenv('I2E_LOG_TO_CONSOLE').lower() == 'true'

    # OCR
    if os.getenv('I2E_OCR_LANGUAGE'):
        config.ocr_language = os.getenv('I2E_OCR_LANGUAGE')

    if os.getenv('I2E_OCR_USE_GPU'):
        config.ocr_use_gpu = os.getenv('I2E_OCR_USE_GPU').lower() == 'true'

    if os.getenv('I2E_OCR_MIN_CONFIDENCE'):
        try:
            config.ocr_min_confidence = float(os.getenv('I2E_OCR_MIN_CONFIDENCE'))
        except ValueError:
            pass

    # Debug
    if os.getenv('I2E_DEBUG'):
        config.debug_mode = os.getenv('I2E_DEBUG').lower() == 'true'

    return config


__all__ = [
    "AppConfig",
    "get_config",
    "get_development_config",
    "get_production_config",
    "get_test_config",
    "load_config_from_env",
    "DEFAULT_CONFIG"
]
