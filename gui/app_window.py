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




class OCRWorker(QThread):
    """Worker thread para procesar OCR sin bloquear la UI."""

    finished = pyqtSignal(str)  # Ruta del archivo Excel generado
    error = pyqtSignal(str)     # Mensaje de error
    progress = pyqtSignal(int)  # Progreso (0-100)
    log_message = pyqtSignal(str)  # Mensaje de log para mostrar en UI

    def __init__(self, image_path: str, output_dir: str, config: AppConfig, template_path: str = None):
        super().__init__()
        self.image_path = image_path
        self.output_dir = output_dir
        self.config = config
        self.template_path = template_path

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

            # Generar nombre de archivo basado en la imagen
            image_name = Path(self.image_path).stem
            excel_filename = f"imagen_a_excel_{image_name}.xlsx"
            output_xlsx = str(output_dir / excel_filename)

            self.log_message.emit("🚀 Iniciando procesamiento con plantilla...")
            self.progress.emit(20)

            # Procesar con plantilla si está disponible
            if self.template_path:
                output_path = self.process_with_template(
                    str(image_path),
                    "default_template",
                    self.template_path,
                    output_xlsx
                )
            else:
                # Procesamiento sin plantilla (fallback al método anterior)
                output_path = self.process_without_template(str(image_path), output_xlsx)

            self.log_message.emit("✅ Procesamiento completado exitosamente")
            self.progress.emit(90)

            # Verificar que el archivo se creó
            if not Path(output_path).exists():
                raise FileNotFoundError(f"El archivo Excel no se generó: {output_path}")

            file_size = Path(output_path).stat().st_size
            self.log_message.emit(f"📊 Archivo Excel generado: {file_size} bytes")
            self.progress.emit(100)

            self.log_message.emit("🎉 ¡Conversión completada exitosamente!")
            self.finished.emit(output_path)

        except Exception as e:
            error_msg = f"❌ Error en procesamiento: {e}"
            self.log_message.emit(error_msg)
            logging.error(f"Error en procesamiento OCR: {e}", exc_info=True)
            self.error.emit(str(e))

    def process_with_template(self, img_path: str, template_name: str, template_img_path: str, out_xlsx: str) -> str:
        """Procesa imagen usando plantilla."""
        import os
        import time
        import numpy as np
        from pathlib import Path
        import cv2
        from image2excel.core.template_manager import TemplateManager, GridSpec, Cell
        from image2excel.core.aligner import ImageAligner
        from image2excel.core.grid_extractor import GridExtractor
        from image2excel.core.ocr_engine import OCREngine
        from image2excel.core.postprocess import postprocess_by_column
        from image2excel.core.exporter_excel import export_rows_xlsx

        # Configuración de debug
        DEBUG_DUMP = True  # ponlo a False en producción
        DEBUG_DIR = os.path.join("debug", time.strftime("%Y%m%d-%H%M%S"))

        def debug_dump_image(name: str, img):
            if not DEBUG_DUMP:
                return
            os.makedirs(DEBUG_DIR, exist_ok=True)
            cv2.imwrite(os.path.join(DEBUG_DIR, f"{name}.png"), img)

        def debug_dump_crop(cell, crop):
            if not DEBUG_DUMP:
                return
            row = f"r{cell.row:02d}"
            col = f"c{cell.col:02d}"
            nm = (cell.name or "cell").replace(" ", "_")
            path = os.path.join(DEBUG_DIR, f"{row}_{col}_{nm}.png")
            cv2.imwrite(path, crop)

        self.log_message.emit("📋 Cargando plantilla...")
        tm = TemplateManager()
        spec = tm.load(template_name)  # ya creado (ver apartado siguiente)

        # 1) Cargar imágenes
        self.log_message.emit("🖼️ Cargando imágenes...")
        img_bgr = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        tmpl_bgr = TemplateManager.image_from_any(template_img_path)
        self.progress.emit(30)

        # 2) Alinear
        self.log_message.emit("🔧 Alineando imagen con plantilla...")
        aligner = ImageAligner(target_w=spec.width, target_h=spec.height)
        img_aligned = aligner.align(img_bgr, tmpl_bgr)
        self.progress.emit(50)

        # 3) Recortar celdas
        self.log_message.emit("✂️ Extrayendo celdas de la cuadrícula...")
        extractor = GridExtractor(spec, pad=6)
        crops = extractor.crop_cells(img_aligned)
        self.progress.emit(60)

        # Debug: guardar imagen alineada
        debug_dump_image("00_aligned", img_aligned)

        # 4) OCR por celda
        self.log_message.emit("🔍 Realizando OCR por celda...")
        ocr = OCREngine(lang=self.config.ocr_language)
        values = {}
        for cell, crop in crops:
            debug_dump_crop(cell, crop)  # guarda el recorte de cada celda
            col_name = cell.name or f"C{cell.col}"
            try:
                text = ocr.read_cell(crop) or ""   # <- nunca None
            except Exception as e:
                # Trazamos pero no paramos; así nunca verás el 'NoneType' repetido
                print(f"[WARN] OCR falló en r{cell.row} c{cell.col} ({col_name}): {type(e).__name__}: {e}")
                text = ""
            values[(cell.row, col_name)] = postprocess_by_column(col_name, text)
        self.progress.emit(75)

        # 5) Reconstruir filas ordenadas
        self.log_message.emit("📊 Reconstruyendo estructura de datos...")
        # Asumimos cabecera fija: ["DXO", "Marca", "Peso"] y una col A con "vehicle/ID"
        headers = ["Etiqueta", "DXO", "Marca", "Peso"]
        # Determina número de filas por el máximo row detectado en spec
        max_row = max(c.row for c in spec.cells)
        rows = []
        for r in range(1, max_row + 1):
            rows.append({
                "Etiqueta": values.get((r, "Etiqueta"), ""),
                "DXO":      values.get((r, "DXO"), ""),
                "Marca":    values.get((r, "Marca"), ""),
                "Peso":     values.get((r, "Peso"), ""),
            })

        # 6) Exportar
        self.log_message.emit("📄 Exportando a Excel...")
        out_path = export_rows_xlsx(headers, rows, out_xlsx)
        return out_path

    def process_without_template(self, img_path: str, out_xlsx: str) -> str:
        """Procesamiento sin plantilla (fallback)."""
        self.log_message.emit("⚠️ Procesando sin plantilla (modo básico)...")

        # Usar el método anterior como fallback
        try:
            ocr = PaddleOcrAdapter()
            parser = BasicParserAdapter()
            exporter = OpenpyxlExporterAdapter()
            use_case = RunImageToExcel(ocr=ocr, parser=parser, exporter=exporter)

            config = RunImageToExcelConfig(
                lang=self.config.ocr_language,
                output_filename=Path(out_xlsx).name
            )

            output_path = use_case(
                image_path=Path(img_path),
                output_dir=Path(out_xlsx).parent,
                cfg=config
            )
            return str(output_path)

        except Exception as e:
            raise RuntimeError(f"Error en procesamiento sin plantilla: {e}")


class ImageToExcelApp(QMainWindow):
    """Ventana principal de la aplicación Image2Excel."""

    def __init__(self):
        super().__init__()
        self.config = AppConfig()
        self.selected_image_path: Optional[str] = None
        self.selected_output_dir: Optional[str] = None
        self.worker: Optional[OCRWorker] = None
        self.last_output_dir: Optional[str] = None  # Para recordar el último directorio usado
        self.template_path = ""  # Para almacenar la ruta de la plantilla

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


        # Sección de plantillas
        template_section = self.create_template_section()
        main_layout.addWidget(template_section)

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

    def create_template_section(self) -> QWidget:
        """Crea la sección para manejar plantillas."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 15, 0, 15)

        # Título de sección
        title = QLabel("📋 Plantillas")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)

        # Layout horizontal para botones
        h_layout = QHBoxLayout()
        h_layout.setSpacing(10)

        # Botón para subir plantilla
        self.btn_upload_tpl = QPushButton("Subir plantilla")
        self.btn_upload_tpl.clicked.connect(self.on_upload_template)
        h_layout.addWidget(self.btn_upload_tpl)

        layout.addLayout(h_layout)

        # Label para mostrar plantilla actual
        self.template_label = QLabel("Plantilla: (ninguna)")
        self.template_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.template_label)

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

        # Iniciar conversión normal
        self.start_normal_mode()


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

    def on_upload_template(self):
        """Maneja la subida de plantillas desde archivos de referencia."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from pathlib import Path

        # Diálogo para seleccionar archivo de referencia
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar plantilla", "",
            "Documentos (*.docx *.pdf *.xlsx);;Imágenes (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;Todos los archivos (*)"
        )
        if not path:
            return

        try:
            # Guardar la ruta de la plantilla
            self.template_path = path
            file_name = Path(path).name
            self.template_label.setText(f"Plantilla: {file_name}")

            QMessageBox.information(self, "Plantilla", f"✅ Plantilla cargada:\n{file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Error plantilla", f"Error al cargar plantilla:\n{str(e)}")

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
        if self.template_path:
            self.log_text.append(f"📋 Plantilla: {Path(self.template_path).name}")
        self.log_text.append("")

        # Crear y configurar worker
        self.worker = OCRWorker(
            self.selected_image_path,
            self.selected_output_dir,
            self.config,
            self.template_path
        )

        # Conectar señales
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_conversion_error)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self.on_log_message)
        self.worker.start()

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
        self.log_text.append("✅ ¡CONVERSIÓN COMPLETADA EXITOSAMENTE!")
        self.log_text.append("=" * 50)
        self.log_text.append(f"📄 Archivo generado: {Path(excel_path).name}")
        self.log_text.append(f"📂 Ubicación: {excel_path}")
        self.log_text.append("")

        # Mostrar mensaje de éxito
        QMessageBox.information(
            self,
            "Conversión Exitosa",
            f"El archivo Excel se ha generado correctamente:\n\n{excel_path}"
        )

        # Restaurar estado de la UI
        self.reset_ui_state()

    def on_conversion_error(self, error_message: str):
        """Maneja errores durante la conversión."""
        self.log_text.append("")
        self.log_text.append("=" * 50)
        self.log_text.append("❌ ERROR EN LA CONVERSIÓN")
        self.log_text.append("=" * 50)
        self.log_text.append(f"Error: {error_message}")
        self.log_text.append("")

        # Restaurar estado de la UI
        self.reset_ui_state()

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
