"""Central logging configuration.

Refactor aplicado:
- Sistema de logging más robusto con múltiples handlers
- Configuración centralizada y personalizable
- Rotación de logs para evitar archivos muy grandes
- Formato de logs más detallado y estructurado
- Soporte para diferentes niveles de logging por módulo
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class LoggingConfig:
    """Configuración centralizada para el sistema de logging."""

    def __init__(
        self,
        level: int = logging.INFO,
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_dir: str = "logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        format_string: Optional[str] = None
    ):
        """
        Inicializar configuración de logging.

        Parameters
        ----------
        level : int
            Nivel de logging por defecto
        log_to_file : bool
            Si se debe escribir logs a archivo
        log_to_console : bool
            Si se debe escribir logs a consola
        log_dir : str
            Directorio para archivos de log
        max_file_size : int
            Tamaño máximo del archivo de log en bytes
        backup_count : int
            Número de archivos de backup a mantener
        format_string : Optional[str]
            Formato personalizado para los logs
        """
        self.level = level
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.log_dir = log_dir
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # Formato por defecto si no se especifica
        if format_string is None:
            self.format_string = (
                "%(asctime)s | %(levelname)-8s | %(name)-25s | "
                "%(funcName)-20s:%(lineno)-4d | %(message)s"
            )
        else:
            self.format_string = format_string

        # Crear directorio de logs si es necesario
        if self.log_to_file:
            os.makedirs(self.log_dir, exist_ok=True)

    def get_formatter(self) -> logging.Formatter:
        """Obtener el formateador de logs configurado."""
        return logging.Formatter(
            fmt=self.format_string,
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def get_console_handler(self) -> logging.StreamHandler:
        """Obtener el handler para consola."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self.get_formatter())
        handler.setLevel(self.level)
        return handler

    def get_file_handler(self) -> logging.handlers.RotatingFileHandler:
        """Obtener el handler para archivo con rotación."""
        log_file = os.path.join(self.log_dir, "app.log")
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(self.get_formatter())
        handler.setLevel(self.level)
        return handler

    def get_error_file_handler(self) -> logging.handlers.RotatingFileHandler:
        """Obtener el handler para archivo de errores."""
        error_log_file = os.path.join(self.log_dir, "errors.log")
        handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setFormatter(self.get_formatter())
        handler.setLevel(logging.ERROR)
        return handler


def configure_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_dir: str = "logs",
    **kwargs: Any
) -> None:
    """
    Configurar el sistema de logging de la aplicación.

    Parameters
    ----------
    level : int
        Nivel de logging por defecto
    log_to_file : bool
        Si se debe escribir logs a archivo
    log_to_console : bool
        Si se debe escribir logs a consola
    log_dir : str
        Directorio para archivos de log
    **kwargs : Any
        Parámetros adicionales para LoggingConfig
    """
    config = LoggingConfig(
        level=level,
        log_to_file=log_to_file,
        log_to_console=log_to_console,
        log_dir=log_dir,
        **kwargs
    )

    # Limpiar handlers existentes
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Configurar nivel del logger raíz
    root_logger.setLevel(logging.DEBUG)

    # Añadir handlers según configuración
    if config.log_to_console:
        root_logger.addHandler(config.get_console_handler())

    if config.log_to_file:
        root_logger.addHandler(config.get_file_handler())
        root_logger.addHandler(config.get_error_file_handler())

    # Configurar loggers específicos para librerías externas
    _configure_external_loggers(level)

    # Log de inicio
    root_logger.info("Sistema de logging configurado correctamente")
    root_logger.info("Nivel de logging: %s", logging.getLevelName(level))
    if config.log_to_file:
        root_logger.info("Logs de archivo habilitados en: %s", config.log_dir)
    if config.log_to_console:
        root_logger.info("Logs de consola habilitados")


def _configure_external_loggers(level: int) -> None:
    """
    Configurar loggers de librerías externas para evitar spam.

    Parameters
    ----------
    level : int
        Nivel de logging para librerías externas
    """
    # Librerías que pueden generar mucho spam
    noisy_libraries = [
        'PIL', 'Pillow', 'cv2', 'opencv',
        'paddle', 'paddleocr', 'paddlepaddle',
        'numpy', 'pandas', 'openpyxl'
    ]

    for lib_name in noisy_libraries:
        lib_logger = logging.getLogger(lib_name)
        lib_logger.setLevel(max(level, logging.WARNING))

    # Logger específico para PaddleOCR que puede ser muy verboso
    paddle_logger = logging.getLogger('paddleocr')
    paddle_logger.setLevel(logging.WARNING)

    # Logger para urllib3 (usado por algunas librerías)
    urllib_logger = logging.getLogger('urllib3')
    urllib_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtener un logger configurado para un módulo específico.

    Parameters
    ----------
    name : str
        Nombre del módulo o componente

    Returns
    -------
    logging.Logger
        Logger configurado para el módulo
    """
    return logging.getLogger(name)


def set_log_level(level: int, logger_name: Optional[str] = None) -> None:
    """
    Cambiar el nivel de logging dinámicamente.

    Parameters
    ----------
    level : int
        Nuevo nivel de logging
    logger_name : Optional[str]
        Nombre del logger específico. Si es None, se cambia el logger raíz
    """
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()

    logger.setLevel(level)
    logger.info("Nivel de logging cambiado a: %s", logging.getLevelName(level))


def log_function_call(func_name: str, args: tuple, kwargs: dict) -> None:
    """
    Decorador helper para logging de llamadas a funciones.

    Parameters
    ----------
    func_name : str
        Nombre de la función
    args : tuple
        Argumentos posicionales
    kwargs : dict
        Argumentos por nombre
    """
    logger = logging.getLogger(__name__)
    logger.debug(
        "Llamada a función: %s(args=%s, kwargs=%s)",
        func_name, args, kwargs
    )


# Configuración por defecto para desarrollo
def configure_development_logging() -> None:
    """Configurar logging optimizado para desarrollo."""
    configure_logging(
        level=logging.DEBUG,
        log_to_file=True,
        log_to_console=True,
        log_dir="logs",
        max_file_size=5 * 1024 * 1024,  # 5MB para desarrollo
        backup_count=3
    )


# Configuración por defecto para producción
def configure_production_logging() -> None:
    """Configurar logging optimizado para producción."""
    configure_logging(
        level=logging.INFO,
        log_to_file=True,
        log_to_console=False,  # No logs en consola en producción
        log_dir="logs",
        max_file_size=50 * 1024 * 1024,  # 50MB para producción
        backup_count=10
    )


__all__ = [
    "configure_logging",
    "configure_development_logging",
    "configure_production_logging",
    "get_logger",
    "set_log_level",
    "log_function_call",
    "LoggingConfig"
]
