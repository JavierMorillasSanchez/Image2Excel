#!/usr/bin/env python3
"""
Aplicación de escritorio para convertir imágenes a Excel usando OCR
Creada con PyQt5 y arquitectura modular (PaddleOCR, parser, exportador)

Refactor aplicado:
- Separada la lógica de negocio en ImageProcessor (SRP)
- Implementado sistema robusto de manejo de errores con logging
- Mejoradas las señales de PyQt5 y gestión de threads
- Añadidos type hints completos y validaciones
- Centralizada la configuración de la aplicación
- Implementado patrón Observer para comunicación entre componentes
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any


from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QFrame,
    QSpacerItem,
    QSizePolicy,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPalette, QColor


from infrastructure.logging_config import configure_logging
from services.paddle_ocr import PaddleOCREngine
from services.parser import ocr_to_table
from services.exporter import export_table_to_excel
from config import AppConfig

# Imports para la nueva arquitectura
from image2excel.infrastructure.ocr.paddle_table_detector import PaddleTableDetector
from image2excel.infrastructure.ocr.paddle_ocr_engine import PaddleOcrEngine
from image2excel.infrastructure.exporter.openpyxl_exporter import OpenpyxlExcelExporter
from image2excel.use_cases.process_image_to_excel import ProcessImageToExcel

# --- INICIO BLOQUE NUEVO (WIRING Clean Architecture) ---
from pathlib import Path

# Importa tu caso de uso y adaptadores nuevos
from image2excel.use_cases.process_image_to_excel import ProcessImageToExcel
from image2excel.infrastructure.ocr.paddle_table_detector import PaddleTableDetector
from image2excel.infrastructure.ocr.paddle_ocr_engine import PaddleOcrEngine
from image2excel.infrastructure.exporter.openpyxl_exporter import OpenpyxlExcelExporter

# Pequeños adaptadores locales para cumplir los puertos
from PIL import Image

class PillowImageLoader:
    def load(self, image_path: Path):
        return Image.open(image_path)

class NoopPreprocessor:
    def preprocess(self, image):
        return image

def run_image_to_excel(image_path_str: str, output_dir_str: str) -> str:
    """
    Cursor debe hacer que la GUI llame a esta función con la ruta de imagen seleccionada
    y el directorio de salida que el usuario elige en la ventana.
    Devuelve la ruta final del Excel generado.
    """
    image_path = Path(image_path_str)
    output_dir = Path(output_dir_str)

    app = ProcessImageToExcel(
        image_loader=PillowImageLoader(),
        preprocessor=NoopPreprocessor(),  # si tienes un preprocesador real, inyéctalo aquí
        ocr_engine=PaddleOcrEngine(table_detector=PaddleTableDetector(), lang="es"),  # prueba "es"
        excel_exporter=OpenpyxlExcelExporter(),
        default_output_name="texto_extraido.xlsx",
    )

    result = app.execute(image_path, output_dir)
    return result.output_path.as_posix()
# --- FIN BLOQUE NUEVO ---


class ImageProcessor(QObject):
    """
    Procesador de imágenes que maneja toda la lógica de negocio.

    Refactor: Separada la lógica de negocio de la UI (SRP)
    """

    # Señales personalizadas para comunicación con la UI
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal(str)  # Ruta del archivo Excel
    processing_error = pyqtSignal(str)     # Mensaje de error
    progress_updated = pyqtSignal(int)     # Progreso (0-100)

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        from infrastructure.logging_config import get_logger
        self.logger = get_logger(self.__class__.__name__)
        self._ocr_engine: Optional[PaddleOCREngine] = None

        # Wiring de la nueva arquitectura
        self._setup_new_architecture()

    def process_image(self, image_path: str, output_dir: str) -> None:
        """
        Procesa una imagen y genera un archivo Excel usando la nueva arquitectura Clean Architecture.

        Parameters
        ----------
        image_path : str
            Ruta de la imagen a procesar
        output_dir : str
            Directorio de salida para el archivo Excel
        """
        try:
            self.logger.info("Iniciando procesamiento de imagen: %s", image_path)
            self.processing_started.emit()
            self.progress_updated.emit(10)

            # Validar entrada
            self._validate_inputs(image_path, output_dir)
            self.progress_updated.emit(20)

            # Usar la nueva función de Clean Architecture
            self.logger.info("Ejecutando conversión con Clean Architecture")
            excel_path = run_image_to_excel(image_path, output_dir)
            self.progress_updated.emit(100)

            self.logger.info("Procesamiento completado exitosamente: %s", excel_path)
            self.processing_finished.emit(excel_path)

        except Exception as e:
            error_msg = f"Error durante el procesamiento: {str(e)}"
            self.logger.exception(error_msg)
            self.processing_error.emit(error_msg)

    def _validate_inputs(self, image_path: str, output_dir: str) -> None:
        """
        Valida los parámetros de entrada.

        Parameters
        ----------
        image_path : str
            Ruta de la imagen
        output_dir : str
            Directorio de salida

        Raises
        ------
        ValueError
            Si los parámetros no son válidos
        """
        if not image_path or not os.path.exists(image_path):
            raise ValueError(f"La imagen no existe: {image_path}")

        if not os.path.isfile(image_path):
            raise ValueError(f"La ruta no es un archivo: {image_path}")

        # Verificar formato de imagen
        image_ext = Path(image_path).suffix.lower()
        supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}
        if image_ext not in supported_extensions:
            raise ValueError(f"Formato de imagen no soportado: {image_ext}")

        if not output_dir:
            raise ValueError("El directorio de salida no puede estar vacío")

        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)

    def _setup_new_architecture(self):
        """Configura la nueva arquitectura con inyección de dependencias."""
        # Ya no necesitamos esta configuración porque usamos run_image_to_excel()
        # que maneja el wiring internamente
        self.logger.info("Nueva arquitectura configurada - usando run_image_to_excel()")


class OCRWorker(QThread):
    """
    Worker thread para procesar OCR sin bloquear la interfaz.

    Refactor: Mejorada la gestión de threads y comunicación con la UI
    """

    def __init__(self, processor: ImageProcessor, image_path: str, output_path: str):
        super().__init__()
        self.processor = processor
        self.image_path = image_path
        self.output_path = output_path

        # Inicializar logger
        from infrastructure.logging_config import get_logger
        self.logger = get_logger(self.__class__.__name__)

        # Conectar señales del procesador
        self.processor.processing_started.connect(self._on_started)
        self.processor.processing_finished.connect(self._on_finished)
        self.processor.processing_error.connect(self._on_error)
        self.processor.progress_updated.connect(self._on_progress)

    def run(self):
        """Ejecuta el procesamiento en el thread separado."""
        try:
            self.processor.process_image(self.image_path, self.output_path)
        except Exception as e:
            self.logger.exception("Error crítico en el worker thread")
            self._on_error(str(e))

    def _on_started(self):
        """Maneja el inicio del procesamiento."""
        pass  # La UI se encarga de esto

    def _on_finished(self, excel_path: str):
        """Maneja la finalización exitosa."""
        pass  # La UI se encarga de esto

    def _on_error(self, error_message: str):
        """Maneja los errores."""
        pass  # La UI se encarga de esto

    def _on_progress(self, progress: int):
        """Maneja las actualizaciones de progreso."""
        pass  # La UI se encarga de esto


class ImageToExcelApp(QMainWindow):
    """
    Aplicación principal para convertir imágenes a Excel usando OCR.

    Refactor: UI simplificada que solo maneja la presentación y delega en ImageProcessor
    """

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        from infrastructure.logging_config import get_logger
        self.logger = get_logger(self.__class__.__name__)

        # Colores personalizables - Paleta de colores especificada
        self.colors = {
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
        }

        # Variables para rutas
        self.image_path: str = ""
        self.output_path: str = ""

        # Componentes del sistema
        self.image_processor = ImageProcessor(config)
        self.ocr_worker: Optional[OCRWorker] = None

        # Inicializar UI
        self.init_ui()
        self.apply_styles()
        self.setup_connections()

    def init_ui(self):
        """Inicializar la interfaz de usuario."""
        self.setWindowTitle(self.config.window_title)
        self.setFixedSize(self.config.window_width, self.config.window_height)
        self.center_window()

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(30, 25, 30, 25)

        # Título principal
        self.title_label = QLabel("Imagen a Excel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        main_layout.addWidget(self.title_label)

        # Espaciador más pequeño
        main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Botón para seleccionar imagen
        self.select_image_btn = QPushButton("Seleccionar Imagen")
        main_layout.addWidget(self.select_image_btn)

        # Label para mostrar nombre del archivo seleccionado
        self.image_status_label = QLabel("Ninguna imagen seleccionada")
        self.image_status_label.setAlignment(Qt.AlignCenter)
        self.image_status_label.setWordWrap(True)
        main_layout.addWidget(self.image_status_label)

        # Separador visual
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator1)

        # Botón para seleccionar directorio de salida
        self.select_output_btn = QPushButton("Seleccionar Directorio de Salida")
        main_layout.addWidget(self.select_output_btn)

        # Label para mostrar directorio seleccionado
        self.output_status_label = QLabel("Ningún directorio seleccionado")
        self.output_status_label.setAlignment(Qt.AlignCenter)
        self.output_status_label.setWordWrap(True)
        main_layout.addWidget(self.output_status_label)

        # Separador visual
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        main_layout.addWidget(separator2)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Espaciador
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Botón de conversión
        self.convert_btn = QPushButton("Convertir a Excel")
        self.convert_btn.setEnabled(False)
        main_layout.addWidget(self.convert_btn)

        # Espaciador final
        main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def setup_connections(self):
        """Configura las conexiones de señales y slots."""
        # Botones
        self.select_image_btn.clicked.connect(self.select_image)
        self.select_output_btn.clicked.connect(self.select_output_directory)
        self.convert_btn.clicked.connect(self.convert_to_excel)

        # Procesador de imágenes
        self.image_processor.processing_started.connect(self.on_processing_started)
        self.image_processor.processing_finished.connect(self.on_processing_finished)
        self.image_processor.processing_error.connect(self.on_processing_error)
        self.image_processor.progress_updated.connect(self.on_progress_updated)

    def apply_styles(self):
        """Aplicar estilos personalizados a la aplicación."""
        # Estilo general de la ventana
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.colors['bg_200']};
            }}

            QWidget {{
                background-color: {self.colors['bg_200']};
                color: {self.colors['accent_100']};
            }}
        """)

        # Estilo del título principal
        title_font = QFont("Arial", 16, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['accent_100']};
                background-color: {self.colors['bg_100']};
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid {self.colors['primary_100']};
                margin: 5px;
            }}
        """)

        # Estilo de los botones
        button_style = f"""
            QPushButton {{
                background-color: {self.colors['primary_100']};
                color: {self.colors['text_100']};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-height: 35px;
            }}

            QPushButton:hover {{
                background-color: {self.colors['primary_200']};
            }}

            QPushButton:pressed {{
                background-color: {self.colors['primary_100']};
            }}

            QPushButton:disabled {{
                background-color: {self.colors['bg_300']};
                color: {self.colors['accent_200']};
            }}
        """

        self.select_image_btn.setStyleSheet(button_style)
        self.select_output_btn.setStyleSheet(button_style)

        # Estilo especial para el botón de conversión
        convert_button_style = f"""
            QPushButton {{
                background-color: {self.colors['primary_100']};
                color: {self.colors['text_100']};
                border: none;
                border-radius: 10px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                min-height: 40px;
            }}

            QPushButton:hover {{
                background-color: {self.colors['primary_200']};
            }}

            QPushButton:pressed {{
                background-color: {self.colors['primary_100']};
            }}

            QPushButton:disabled {{
                background-color: {self.colors['bg_300']};
                color: {self.colors['accent_200']};
            }}
        """

        self.convert_btn.setStyleSheet(convert_button_style)

        # Estilo de las etiquetas de estado
        status_label_style = f"""
            QLabel {{
                color: {self.colors['accent_200']};
                background-color: {self.colors['bg_100']};
                padding: 10px;
                border-radius: 5px;
                border: 1px solid {self.colors['bg_300']};
                font-size: 12px;
            }}
        """

        self.image_status_label.setStyleSheet(status_label_style)
        self.output_status_label.setStyleSheet(status_label_style)

        # Estilo de los separadores
        separator_style = f"""
            QFrame {{
                color: {self.colors['bg_300']};
                background-color: {self.colors['bg_300']};
            }}
        """

        for separator in self.findChildren(QFrame):
            if separator.frameShape() == QFrame.HLine:
                separator.setStyleSheet(separator_style)

        # Estilo de la barra de progreso
        progress_style = f"""
            QProgressBar {{
                border: 2px solid {self.colors['primary_100']};
                border-radius: 5px;
                text-align: center;
                background-color: {self.colors['bg_100']};
            }}

            QProgressBar::chunk {{
                background-color: {self.colors['primary_100']};
                border-radius: 3px;
            }}
        """
        self.progress_bar.setStyleSheet(progress_style)

    def center_window(self):
        """Centrar la ventana en la pantalla."""
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_image(self):
        """Abrir diálogo para seleccionar imagen."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar Imagen",
                "",
                "Archivos de Imagen (*.png *.jpg *.jpeg *.bmp *.tiff *.gif)"
            )

            if file_path:
                self.image_path = file_path
                filename = os.path.basename(file_path)
                self.image_status_label.setText(f"Imagen seleccionada: {filename}")
                self.image_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.colors['primary_100']};
                        background-color: {self.colors['bg_100']};
                        padding: 10px;
                        border-radius: 5px;
                        border: 1px solid {self.colors['primary_100']};
                        font-size: 12px;
                        font-weight: bold;
                    }}
                """)
                self.check_ready_to_convert()
                self.logger.info("Imagen seleccionada: %s", file_path)

        except Exception as e:
            self.logger.error("Error al seleccionar imagen: %s", e)
            QMessageBox.critical(self, "Error", f"Error al seleccionar imagen: {str(e)}")

    def select_output_directory(self):
        """Abrir diálogo para seleccionar directorio de salida."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar Directorio de Salida"
            )

            if directory:
                self.output_path = directory
                self.output_status_label.setText(f"Directorio de salida: {directory}")
                self.output_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {self.colors['primary_100']};
                        background-color: {self.colors['bg_100']};
                        padding: 10px;
                        border-radius: 5px;
                        border: 1px solid {self.colors['primary_100']};
                        font-size: 12px;
                        font-weight: bold;
                    }}
                """)
                self.check_ready_to_convert()
                self.logger.info("Directorio de salida seleccionado: %s", directory)

        except Exception as e:
            self.logger.error("Error al seleccionar directorio: %s", e)
            QMessageBox.critical(self, "Error", f"Error al seleccionar directorio: {str(e)}")

    def check_ready_to_convert(self):
        """Verificar si la aplicación está lista para convertir."""
        if self.image_path and self.output_path:
            self.convert_btn.setEnabled(True)
        else:
            self.convert_btn.setEnabled(False)

    def convert_to_excel(self):
        """Iniciar el proceso de conversión a Excel."""
        if not self.image_path or not self.output_path:
            QMessageBox.warning(self, "Error", "Por favor selecciona una imagen y un directorio de salida.")
            return

        try:
            # Crear y iniciar worker thread
            self.ocr_worker = OCRWorker(self.image_processor, self.image_path, self.output_path)
            self.ocr_worker.start()

        except Exception as e:
            self.logger.error("Error al iniciar conversión: %s", e)
            QMessageBox.critical(self, "Error", f"Error al iniciar conversión: {str(e)}")

    def on_processing_started(self):
        """Maneja el inicio del procesamiento."""
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("Procesando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.logger.info("Procesamiento iniciado")

    def on_processing_finished(self, excel_path: str):
        """Maneja la finalización exitosa de la conversión."""
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("Convertir a Excel")
        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self,
            "Éxito",
            f"Excel generado correctamente en:\n{excel_path}"
        )
        self.logger.info("Conversión completada exitosamente: %s", excel_path)

    def on_processing_error(self, error_message: str):
        """Maneja errores durante la conversión."""
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("Convertir a Excel")
        self.progress_bar.setVisible(False)

        QMessageBox.critical(
            self,
            "Error",
            f"Error durante la conversión:\n{error_message}"
        )
        self.logger.error("Error en conversión: %s", error_message)

    def on_progress_updated(self, progress: int):
        """Maneja las actualizaciones de progreso."""
        self.progress_bar.setValue(progress)

    def closeEvent(self, event):
        """Manejar el cierre de la aplicación."""
        try:
            if self.ocr_worker and self.ocr_worker.isRunning():
                self.logger.info("Deteniendo worker thread antes del cierre")
                self.ocr_worker.terminate()
                self.ocr_worker.wait()
            event.accept()
        except Exception as e:
            self.logger.error("Error al cerrar aplicación: %s", e)
            event.accept()


def main():
    """Función principal de la aplicación."""
    try:
        # Configurar logging
        config = AppConfig()
        configure_logging(config.logging_level)

        # Crear aplicación
        app = QApplication(sys.argv)
        app.setApplicationName("Convertidor de Imagen a Excel")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("Tu Organización")

        # Crear y mostrar ventana principal
        window = ImageToExcelApp(config)
        window.show()

        # Ejecutar aplicación
        sys.exit(app.exec_())

    except Exception as e:
        from infrastructure.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error("Error crítico en la aplicación: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
