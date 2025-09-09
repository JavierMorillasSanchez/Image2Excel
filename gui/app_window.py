"""
Interfaz gráfica principal de la aplicación Image2Excel.

Refactor: GUI simplificada que usa la nueva arquitectura Clean Architecture
para procesar imágenes y generar archivos Excel.
"""

from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional, List
import cv2
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QTextEdit,
    QMessageBox, QFrame, QSpacerItem, QSizePolicy, QCheckBox,
    QDialog, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon

from config import AppConfig
from image2excel.use_cases import RunImageToExcel, RunImageToExcelConfig
from image2excel.adapters import PaddleOcrAdapter, BasicParserAdapter, OpenpyxlExporterAdapter


class GridMarkerDialog(QDialog):
    """Diálogo para marcar separadores de cuadrícula en la imagen."""

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.vertical_lines = []  # Lista de coordenadas X
        self.horizontal_lines = []  # Lista de coordenadas Y
        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.setWindowTitle("Marcar Separadores de Cuadrícula")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # Instrucciones
        instructions = QLabel(
            "Haz clic en la imagen para marcar separadores:\n"
            "• Clic izquierdo: Línea vertical (columna)\n"
            "• Clic derecho: Línea horizontal (fila)\n"
            "• Doble clic: Finalizar"
        )
        instructions.setStyleSheet("font-weight: bold; margin: 10px;")
        layout.addWidget(instructions)

        # Área de scroll para la imagen
        scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.mousePressEvent = self.on_image_click
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Botones
        button_layout = QHBoxLayout()

        clear_button = QPushButton("Limpiar Todo")
        clear_button.clicked.connect(self.clear_lines)
        button_layout.addWidget(clear_button)

        button_layout.addStretch()

        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        finish_button = QPushButton("Finalizar")
        finish_button.clicked.connect(self.accept)
        button_layout.addWidget(finish_button)

        layout.addLayout(button_layout)

    def load_image(self):
        """Carga y muestra la imagen."""
        try:
            # Cargar imagen con OpenCV
            img = cv2.imread(self.image_path)
            if img is None:
                raise ValueError(f"No se pudo cargar la imagen: {self.image_path}")

            # Convertir BGR a RGB para Qt
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img_rgb.shape
            bytes_per_line = ch * w

            # Crear QImage
            from PyQt5.QtGui import QImage
            q_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Escalar imagen si es muy grande
            max_size = 1000
            if w > max_size or h > max_size:
                scale = max_size / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                q_image = q_image.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.scale_factor = scale
            else:
                self.scale_factor = 1.0

            # Guardar dimensiones originales
            self.original_width = w
            self.original_height = h

            # Mostrar imagen
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar la imagen: {e}")
            self.reject()

    def on_image_click(self, event):
        """Maneja los clics en la imagen."""
        if event.button() == Qt.LeftButton:
            # Clic izquierdo: línea vertical
            x = int(event.x() / self.scale_factor)
            if x not in self.vertical_lines:
                self.vertical_lines.append(x)
                self.vertical_lines.sort()
        elif event.button() == Qt.RightButton:
            # Clic derecho: línea horizontal
            y = int(event.y() / self.scale_factor)
            if y not in self.horizontal_lines:
                self.horizontal_lines.append(y)
                self.horizontal_lines.sort()

        self.update_image_display()

    def update_image_display(self):
        """Actualiza la imagen con las líneas marcadas."""
        # Recargar imagen original
        img = cv2.imread(self.image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Dibujar líneas verticales
        for x in self.vertical_lines:
            cv2.line(img_rgb, (x, 0), (x, img_rgb.shape[0]), (255, 0, 0), 2)

        # Dibujar líneas horizontales
        for y in self.horizontal_lines:
            cv2.line(img_rgb, (0, y), (img_rgb.shape[1], y), (0, 255, 0), 2)

        # Convertir a QImage y mostrar
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        from PyQt5.QtGui import QImage
        q_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Escalar si es necesario
        if self.scale_factor != 1.0:
            new_w = int(w * self.scale_factor)
            new_h = int(h * self.scale_factor)
            q_image = q_image.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)

    def clear_lines(self):
        """Limpia todas las líneas marcadas."""
        self.vertical_lines.clear()
        self.horizontal_lines.clear()
        self.update_image_display()

    def get_grid_coordinates(self) -> tuple[List[int], List[int]]:
        """Retorna las coordenadas de las líneas marcadas."""
        return self.vertical_lines, self.horizontal_lines


class OCRWorker(QThread):
    """Worker thread para procesar OCR sin bloquear la UI."""

    finished = pyqtSignal(str)  # Ruta del archivo Excel generado
    error = pyqtSignal(str)     # Mensaje de error
    progress = pyqtSignal(int)  # Progreso (0-100)
    log_message = pyqtSignal(str)  # Mensaje de log para mostrar en UI

    def __init__(self, image_path: str, output_dir: str, config: AppConfig):
        super().__init__()
        self.image_path = image_path
        self.output_dir = output_dir
        self.config = config

    def run(self):
        """Ejecuta el procesamiento OCR en un hilo separado."""
        try:
            self.log_message.emit("🔍 Iniciando validación de archivos...")
            self.progress.emit(5)

            # Validar archivo de imagen
            image_path = Path(self.image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"La imagen no existe: {self.image_path}")

            if not image_path.is_file():
                raise ValueError(f"La ruta no es un archivo válido: {self.image_path}")

            # Validar directorio de salida
            output_dir = Path(self.output_dir)
            if not output_dir.exists():
                self.log_message.emit(f"📁 Creando directorio de salida: {output_dir}")
                output_dir.mkdir(parents=True, exist_ok=True)

            self.log_message.emit("✅ Validación de archivos completada")
            self.progress.emit(10)

            # Construir caso de uso
            self.log_message.emit("🔧 Inicializando componentes OCR...")
            try:
                ocr = PaddleOcrAdapter()
                self.log_message.emit("✅ Adaptador OCR inicializado")
            except Exception as e:
                raise RuntimeError(f"Error al inicializar OCR: {e}")

            try:
                parser = BasicParserAdapter()
                self.log_message.emit("✅ Parser de tablas inicializado")
            except Exception as e:
                raise RuntimeError(f"Error al inicializar parser: {e}")

            try:
                exporter = OpenpyxlExporterAdapter()
                self.log_message.emit("✅ Exportador Excel inicializado")
            except Exception as e:
                raise RuntimeError(f"Error al inicializar exportador: {e}")

            use_case = RunImageToExcel(ocr=ocr, parser=parser, exporter=exporter)
            self.log_message.emit("✅ Caso de uso construido correctamente")
            self.progress.emit(25)

            # Configurar parámetros
            self.log_message.emit("⚙️ Configurando parámetros de procesamiento...")

            # Generar nombre de archivo basado en la imagen
            image_name = Path(self.image_path).stem  # Nombre sin extensión
            excel_filename = f"imagen_a_excel_{image_name}.xlsx"

            config = RunImageToExcelConfig(
                lang=self.config.ocr_language,
                output_filename=excel_filename
            )
            self.log_message.emit(f"📋 Idioma OCR: {config.lang}")
            self.log_message.emit(f"📄 Nombre de archivo: {config.output_filename}")
            self.progress.emit(35)

            # Ejecutar procesamiento
            self.log_message.emit("🚀 Iniciando extracción de texto con OCR...")
            self.progress.emit(40)

            try:
                output_path = use_case(
                    image_path=image_path,
                    output_dir=output_dir,
                    cfg=config
                )
                self.log_message.emit("✅ Procesamiento OCR completado exitosamente")
                self.progress.emit(80)

                # Verificar que el archivo se creó
                if not output_path.exists():
                    raise FileNotFoundError(f"El archivo Excel no se generó: {output_path}")

                file_size = output_path.stat().st_size
                self.log_message.emit(f"📊 Archivo Excel generado: {file_size} bytes")
                self.progress.emit(100)

                self.log_message.emit("🎉 ¡Conversión completada exitosamente!")
                self.finished.emit(str(output_path))

            except Exception as e:
                raise RuntimeError(f"Error durante el procesamiento OCR: {e}")

        except Exception as e:
            error_msg = f"❌ Error en procesamiento: {e}"
            self.log_message.emit(error_msg)
            logging.error(f"Error en procesamiento OCR: {e}", exc_info=True)
            self.error.emit(str(e))


class ImageToExcelApp(QMainWindow):
    """Ventana principal de la aplicación Image2Excel."""

    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        self.selected_image_path: Optional[str] = None
        self.selected_output_dir: Optional[str] = None
        self.worker: Optional[OCRWorker] = None
        self.last_output_dir: Optional[str] = None  # Para recordar el último directorio usado

        self.init_ui()
        self.apply_styles()

        # Ajustar el tamaño de la ventana al contenido
        self.adjustSize()

        # Establecer un tamaño mínimo razonable
        self.setMinimumSize(600, 500)

        # Inicializar estado del botón después de que la UI esté lista
        self.check_ready_to_convert()

    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        self.setWindowTitle("Imagen a Excel")
        # No establecer tamaño fijo, dejar que se ajuste al contenido

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Título
        title_label = QLabel("🖼️ Imagen a Excel")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title_label)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # Sección de imagen
        image_section = self.create_image_section()
        main_layout.addWidget(image_section)

        # Sección de directorio de salida
        output_section = self.create_output_section()
        main_layout.addWidget(output_section)

        # Checkbox para modo asistido
        self.assisted_mode_checkbox = QCheckBox("Modo asistido (marcar columnas/filas)")
        self.assisted_mode_checkbox.setFont(QFont("Arial", 10))
        main_layout.addWidget(self.assisted_mode_checkbox)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Área de texto para logs
        self.log_text = QTextEdit()
        self.log_text.setMinimumHeight(120)
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Los mensajes de procesamiento aparecerán aquí...")
        main_layout.addWidget(self.log_text)

        # Botón de conversión
        self.convert_button = QPushButton("🔄 Convertir a Excel")
        self.convert_button.setEnabled(False)
        self.convert_button.clicked.connect(self.convert_to_excel)
        main_layout.addWidget(self.convert_button)

        # Espaciador
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

    def create_image_section(self) -> QWidget:
        """Crea la sección para seleccionar imagen."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 15, 0, 15)

        # Título de sección
        title = QLabel("📁 Seleccionar Imagen")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Layout horizontal para botón y label
        h_layout = QHBoxLayout()

        self.select_image_button = QPushButton("Examinar...")
        self.select_image_button.clicked.connect(self.select_image)
        # Hacer que el botón se ajuste al contenido pero mantenga altura mínima
        self.select_image_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        h_layout.addWidget(self.select_image_button)

        self.image_label = QLabel("Ninguna imagen seleccionada")
        self.image_label.setStyleSheet("color: #666; font-style: italic;")
        h_layout.addWidget(self.image_label, 1)

        layout.addLayout(h_layout)
        return section

    def create_output_section(self) -> QWidget:
        """Crea la sección para seleccionar directorio de salida."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 15, 0, 15)

        # Título de sección
        title = QLabel("📂 Directorio de Salida")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Layout horizontal para botón y label
        h_layout = QHBoxLayout()

        self.select_output_button = QPushButton("Examinar...")
        self.select_output_button.clicked.connect(self.select_output_directory)
        # Hacer que el botón se ajuste al contenido pero mantenga altura mínima
        self.select_output_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        h_layout.addWidget(self.select_output_button)

        self.output_label = QLabel("Directorio actual")
        self.output_label.setStyleSheet("color: #666; font-style: italic;")
        h_layout.addWidget(self.output_label, 1)

        layout.addLayout(h_layout)
        return section

    def apply_styles(self):
        """Aplica estilos a la interfaz."""
        colors = self.config.ui_colors

        style = f"""
        QMainWindow {{
            background-color: {colors['bg_100']};
        }}

        QPushButton {{
            background-color: {colors['primary_100']};
            color: {colors['text_100']};
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            min-height: 35px;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background-color: {colors['primary_200']};
        }}

        QPushButton:pressed {{
            background-color: {colors['accent_100']};
        }}

        QPushButton:disabled {{
            background-color: {colors['bg_300']};
            color: {colors['accent_200']};
        }}

        QLabel {{
            color: {colors['accent_100']};
        }}

        QTextEdit {{
            background-color: {colors['bg_200']};
            border: 1px solid {colors['bg_300']};
            border-radius: 5px;
            padding: 5px;
        }}

        QProgressBar {{
            border: 1px solid {colors['bg_300']};
            border-radius: 5px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {colors['primary_100']};
            border-radius: 4px;
        }}
        """

        self.setStyleSheet(style)

    def select_image(self):
        """Abre diálogo para seleccionar imagen."""
        file_dialog = QFileDialog()
        file_dialog.setNameFilter(
            "Archivos de Imagen (*.png *.jpg *.jpeg *.bmp *.tiff *.gif)"
        )
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            if files:
                self.selected_image_path = files[0]
                image_name = Path(self.selected_image_path).name
                self.image_label.setText(f"📄 {image_name}")
                self.image_label.setStyleSheet("color: #1E88E5; font-weight: bold;")

                # Log informativo (solo si el log_text está inicializado)
                if hasattr(self, 'log_text') and self.log_text is not None:
                    self.log_text.append(f"📁 Imagen seleccionada: {image_name}")

                    # Verificar que el archivo existe y es válido
                    if Path(self.selected_image_path).exists():
                        file_size = Path(self.selected_image_path).stat().st_size
                        self.log_text.append(f"   ✅ Archivo válido ({file_size} bytes)")
                    else:
                        self.log_text.append(f"   ❌ Error: El archivo no existe")

                # Actualizar estado del botón de forma segura
                self.update_convert_button_state()

    def select_output_directory(self):
        """Abre diálogo para seleccionar directorio de salida."""
        # Usar el último directorio usado si existe, sino usar el directorio actual
        start_dir = self.last_output_dir if self.last_output_dir else str(Path.cwd())

        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar Directorio de Salida", start_dir
        )

        if directory:
            self.selected_output_dir = directory
            self.last_output_dir = directory  # Guardar para la próxima vez
            dir_name = Path(directory).name
            self.output_label.setText(f"📁 {dir_name}")
            self.output_label.setStyleSheet("color: #1E88E5; font-weight: bold;")

            # Log informativo (solo si el log_text está inicializado)
            if hasattr(self, 'log_text') and self.log_text is not None:
                self.log_text.append(f"📂 Directorio de salida seleccionado: {dir_name}")

                # Verificar permisos de escritura
                try:
                    test_file = Path(directory) / "test_write.tmp"
                    test_file.touch()
                    test_file.unlink()
                    self.log_text.append(f"   ✅ Permisos de escritura verificados")
                except Exception as e:
                    self.log_text.append(f"   ⚠️ Advertencia: No se pudo verificar permisos de escritura")

            # Actualizar estado del botón de forma segura
            self.update_convert_button_state()

    def update_convert_button_state(self):
        """Actualiza el estado del botón de conversión de forma segura."""
        try:
            # Verificar que el botón existe y no es None
            if not hasattr(self, 'convert_button') or self.convert_button is None:
                return

            # Verificar si está listo para convertir
            ready = bool(self.selected_image_path and self.selected_output_dir)
            self.convert_button.setEnabled(ready)

        except Exception as e:
            # Si hay cualquier error, simplemente ignorar
            print(f"Warning: Error updating button state: {e}")
            pass

    def check_ready_to_convert(self):
        """Método legacy - redirige al nuevo método."""
        self.update_convert_button_state()

    def convert_to_excel(self):
        """Inicia el proceso de conversión SOLO cuando se pulsa el botón."""
        if not self.selected_image_path or not self.selected_output_dir:
            self.log_text.append("❌ Error: Debe seleccionar una imagen y un directorio de salida")
            return

        # Verificar que no hay otro proceso en ejecución
        if self.worker and self.worker.isRunning():
            self.log_text.append("⚠️ Ya hay un proceso en ejecución. Espere a que termine.")
            return

        # Verificar modo asistido
        if self.assisted_mode_checkbox.isChecked():
            self.start_assisted_mode()
        else:
            self.start_normal_mode()

    def start_assisted_mode(self):
        """Inicia el modo asistido con marcado de cuadrícula."""
        # Deshabilitar botones durante procesamiento
        self.convert_button.setEnabled(False)
        self.convert_button.setText("🔄 Abriendo editor...")
        self.select_image_button.setEnabled(False)
        self.select_output_button.setEnabled(False)

        # Limpiar logs y mostrar información inicial
        self.log_text.clear()
        self.log_text.append("=" * 50)
        self.log_text.append("🎯 MODO ASISTIDO - MARCAR CUADRÍCULA")
        self.log_text.append("=" * 50)
        self.log_text.append(f"📁 Imagen: {Path(self.selected_image_path).name}")
        self.log_text.append(f"📂 Destino: {Path(self.selected_output_dir).name}")
        self.log_text.append("🖱️ Abriendo editor de cuadrícula...")
        self.log_text.append("")

        # Abrir diálogo de marcado de cuadrícula
        dialog = GridMarkerDialog(self.selected_image_path, self)
        if dialog.exec_() == QDialog.Accepted:
            vertical_lines, horizontal_lines = dialog.get_grid_coordinates()

            if not vertical_lines or not horizontal_lines:
                self.log_text.append("❌ Error: Debe marcar al menos una línea vertical y una horizontal")
                self.reset_ui_state()
                return

            # Procesar cuadrícula asistida
            self.process_assisted_grid(vertical_lines, horizontal_lines)
        else:
            self.log_text.append("❌ Operación cancelada por el usuario")
            self.reset_ui_state()

    def start_normal_mode(self):
        """Inicia el modo normal de procesamiento."""
        # Deshabilitar botones durante procesamiento
        self.convert_button.setEnabled(False)
        self.convert_button.setText("🔄 Procesando...")
        self.select_image_button.setEnabled(False)
        self.select_output_button.setEnabled(False)

        # Mostrar barra de progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Limpiar logs y mostrar información inicial
        self.log_text.clear()
        self.log_text.append("=" * 50)
        self.log_text.append("🚀 INICIANDO CONVERSIÓN DE IMAGEN A EXCEL")
        self.log_text.append("=" * 50)
        self.log_text.append(f"📁 Imagen: {Path(self.selected_image_path).name}")
        self.log_text.append(f"📂 Destino: {Path(self.selected_output_dir).name}")
        self.log_text.append(f"🌐 Idioma: {self.config.ocr_language}")
        self.log_text.append("")

        # Crear y ejecutar worker
        self.worker = OCRWorker(
            self.selected_image_path,
            self.selected_output_dir,
            self.config
        )
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self.on_log_message)
        self.worker.start()

    def process_assisted_grid(self, vertical_lines: List[int], horizontal_lines: List[int]):
        """Procesa la cuadrícula marcada por el usuario."""
        try:
            self.log_text.append("🔍 Procesando cuadrícula asistida...")
            self.log_text.append(f"📏 Líneas verticales: {len(vertical_lines)}")
            self.log_text.append(f"📏 Líneas horizontales: {len(horizontal_lines)}")

            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)

            # Importar y usar el servicio de cuadrícula asistida
            from services.assist_grid import extract_text_from_grid

            # Extraer texto de la cuadrícula
            grid_data = extract_text_from_grid(
                self.selected_image_path,
                vertical_lines,
                horizontal_lines,
                self.config.ocr_language
            )

            self.progress_bar.setValue(80)
            self.log_text.append("📊 Cuadrícula procesada, exportando a Excel...")

            # Exportar a Excel usando el exporter actual
            from image2excel.adapters import OpenpyxlExporterAdapter
            from image2excel.ports import Table, TableRow

            # Convertir datos a formato Table
            table_rows = [TableRow(cells=row) for row in grid_data]
            table = Table(rows=table_rows)

            # Generar nombre de archivo
            image_name = Path(self.selected_image_path).stem
            filename = f"imagen_a_excel_{image_name}.xlsx"

            # Exportar
            exporter = OpenpyxlExporterAdapter()
            output_path = exporter.export(table, self.selected_output_dir, filename)

            self.progress_bar.setValue(100)
            self.log_text.append("✅ ¡Conversión completada exitosamente!")
            self.log_text.append(f"📄 Archivo generado: {Path(output_path).name}")
            self.log_text.append(f"📂 Ubicación: {output_path}")

            # Mostrar mensaje de éxito
            QMessageBox.information(
                self,
                "Conversión Exitosa",
                f"El archivo Excel se ha generado correctamente:\n\n{output_path}"
            )

        except Exception as e:
            self.log_text.append(f"❌ Error en modo asistido: {e}")
            QMessageBox.critical(self, "Error", f"Error en modo asistido: {e}")

        finally:
            self.reset_ui_state()

    def reset_ui_state(self):
        """Restaura el estado de la UI después del procesamiento."""
        self.convert_button.setEnabled(True)
        self.convert_button.setText("🔄 Convertir a Excel")
        self.select_image_button.setEnabled(True)
        self.select_output_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_log_message(self, message: str):
        """Maneja mensajes de log del worker."""
        self.log_text.append(message)
        # Auto-scroll al final
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def on_conversion_finished(self, excel_path: str):
        """Maneja la finalización exitosa de la conversión."""
        self.progress_bar.setVisible(False)
        self.log_text.append("")
        self.log_text.append("=" * 50)
        self.log_text.append("🎉 CONVERSIÓN COMPLETADA EXITOSAMENTE")
        self.log_text.append("=" * 50)
        self.log_text.append(f"📄 Archivo Excel generado:")
        self.log_text.append(f"   {excel_path}")

        # Rehabilitar botones
        self.convert_button.setEnabled(True)
        self.convert_button.setText("🔄 Convertir a Excel")
        self.select_image_button.setEnabled(True)
        self.select_output_button.setEnabled(True)

        # Mostrar mensaje de éxito
        QMessageBox.information(
            self,
            "✅ Conversión Exitosa",
            f"El archivo Excel se ha generado correctamente:\n\n{excel_path}\n\n"
            f"Puede abrir el archivo para ver el resultado."
        )

    def on_conversion_error(self, error_message: str):
        """Maneja errores durante la conversión."""
        self.progress_bar.setVisible(False)
        self.log_text.append("")
        self.log_text.append("=" * 50)
        self.log_text.append("❌ ERROR EN LA CONVERSIÓN")
        self.log_text.append("=" * 50)
        self.log_text.append(f"Detalles del error:")
        self.log_text.append(f"   {error_message}")
        self.log_text.append("")
        self.log_text.append("💡 Sugerencias:")
        self.log_text.append("   - Verifique que la imagen sea válida")
        self.log_text.append("   - Asegúrese de que el directorio de salida existe")
        self.log_text.append("   - Compruebe que tiene permisos de escritura")

        # Rehabilitar botones
        self.convert_button.setEnabled(True)
        self.convert_button.setText("🔄 Convertir a Excel")
        self.select_image_button.setEnabled(True)
        self.select_output_button.setEnabled(True)

        # Mostrar mensaje de error
        QMessageBox.critical(
            self,
            "❌ Error de Conversión",
            f"Ocurrió un error durante la conversión:\n\n{error_message}\n\n"
            f"Revise los logs para más detalles."
        )

    def closeEvent(self, event):
        """Maneja el cierre de la aplicación."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()


def main():
    """Función principal para ejecutar la aplicación GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("Image2Excel")
    app.setApplicationVersion("2.0.0")

    window = ImageToExcelApp()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
