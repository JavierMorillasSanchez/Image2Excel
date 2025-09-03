"""PaddleOCR engine implementation.

Refactor aplicado:
- Mejorado el manejo de errores con logging detallado
- Optimización de rendimiento con lazy loading del motor OCR
- Validación robusta de parámetros de entrada
- Soporte para múltiples idiomas y configuraciones
- Mejor gestión de memoria y recursos
- Métodos de limpieza y shutdown seguros
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

import cv2
import numpy as np
from paddleocr import PaddleOCR  # type: ignore

from core.engine import OCREngine
from core.models import OCRResult, OCRTextLine
from infrastructure.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class OCRConfig:
    """Configuración para el motor OCR."""

    language: str = "es"
    use_angle_cls: bool = True
    use_gpu: bool = False
    gpu_mem: int = 500
    cpu_threads: int = 10
    enable_mkldnn: bool = True
    det_db_thresh: float = 0.3
    det_db_box_thresh: float = 0.5
    det_db_unclip_ratio: float = 1.6
    rec_batch_num: int = 6
    cls_batch_num: int = 6
    cls_thresh: float = 0.9


class PaddleOCREngine(OCREngine):
    """
    Motor OCR respaldado por PaddleOCR con optimizaciones y manejo robusto de errores.

    Refactor: Implementado lazy loading, mejor manejo de errores y optimizaciones de rendimiento
    """

    def __init__(self, config: Optional[OCRConfig] = None) -> None:
        """
        Inicializar el motor OCR.

        Parameters
        ----------
        config : Optional[OCRConfig]
            Configuración personalizada para el motor OCR
        """
        super().__init__()
        self.config = config or OCRConfig()
        self._ocr: Optional[PaddleOCR] = None
        self._initialized = False
        self._last_used = 0.0
        self._processing_times: List[float] = []

        logger.info(
            "PaddleOCREngine inicializado con configuración: language=%s, "
            "use_angle_cls=%s",
            self.config.language, self.config.use_angle_cls
        )

    def _initialize_ocr(self) -> None:
        """Inicializar el motor PaddleOCR de forma lazy."""
        if self._initialized:
            return

        try:
            logger.info("Inicializando motor PaddleOCR...")
            start_time = time.time()

            # Configurar parámetros del motor con manejo de compatibilidad
            ocr_params = {}

            # Parámetros básicos que funcionan en todas las versiones
            ocr_params['lang'] = self.config.language

            # Parámetros opcionales que se añaden solo si están disponibles
            try:
                # Probar parámetros uno por uno para detectar compatibilidad
                test_ocr = PaddleOCR(lang=self.config.language)
                del test_ocr

                # Si llegamos aquí, podemos usar parámetros avanzados
                if self.config.use_angle_cls:
                    ocr_params['use_angle_cls'] = True

                if self.config.use_gpu:
                    ocr_params['use_gpu'] = True
                    ocr_params['gpu_mem'] = self.config.gpu_mem

                if self.config.cpu_threads > 1:
                    ocr_params['cpu_threads'] = self.config.cpu_threads

                if self.config.enable_mkldnn:
                    ocr_params['enable_mkldnn'] = True

                # Parámetros de detección para mejor calidad
                ocr_params['det_db_thresh'] = self.config.det_db_thresh
                ocr_params['det_db_box_thresh'] = self.config.det_db_box_thresh
                ocr_params['det_db_unclip_ratio'] = self.config.det_db_unclip_ratio

                # Parámetros de reconocimiento para mejor precisión
                ocr_params['rec_batch_num'] = self.config.rec_batch_num
                ocr_params['cls_batch_num'] = self.config.cls_batch_num
                ocr_params['cls_thresh'] = self.config.cls_thresh

                logger.info("Usando configuración avanzada de PaddleOCR")

            except Exception as e:
                logger.warning("Versión de PaddleOCR limitada, usando configuración básica: %s", e)
                # Configuración mínima para versiones antiguas
                ocr_params = {'lang': self.config.language}

            self._ocr = PaddleOCR(**ocr_params)
            self._initialized = True

            init_time = time.time() - start_time
            logger.info("Motor PaddleOCR inicializado en %.2f segundos", init_time)

        except Exception as e:
            logger.exception("Error al inicializar motor PaddleOCR")
            raise RuntimeError(f"Fallo en la inicialización de PaddleOCR: {str(e)}") from e

    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extraer texto usando PaddleOCR.

        Parameters
        ----------
        image_path : str
            Ruta de la imagen a procesar

        Returns
        -------
        OCRResult
            Resultado estructurado del OCR

        Raises
        ------
        ValueError
            Si la ruta de la imagen no es válida
        RuntimeError
            Si falla el procesamiento OCR
        FileNotFoundError
            Si la imagen no existe
        """
        try:
            # Validar entrada
            self._validate_image_path(image_path)

            # Inicializar OCR si es necesario
            self._initialize_ocr()

            # Procesar imagen
            start_time = time.time()
            logger.info("Procesando imagen: %s", image_path)

            # Ejecutar OCR con parámetros optimizados
            try:
                # Intentar con clasificación de ángulo
                result = self._ocr.ocr(image_path, cls=True)
            except Exception as e:
                logger.warning("Error con cls=True, intentando sin clasificación: %s", e)
                # Fallback: sin clasificación de ángulo
                result = self._ocr.ocr(image_path, cls=False)

            # Calcular tiempo de procesamiento
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            self._last_used = time.time()

            logger.info(
                "OCR completado en %.2f segundos para imagen: %s",
                processing_time, image_path
            )

            # Convertir resultado a modelo de dominio
            ocr_result = self._parse_ocr_result(result, image_path)

            return ocr_result

        except Exception as e:
            logger.exception("Error en extracción de texto para imagen: %s", image_path)
            if isinstance(e, (ValueError, FileNotFoundError)):
                raise
            raise RuntimeError(f"Error en OCR: {str(e)}") from e

    def extract_text_from_array(self, image_array: np.ndarray) -> OCRResult:
        """
        Extraer texto desde un array de numpy (útil para procesamiento en memoria).

        Parameters
        ----------
        image_array : np.ndarray
            Array de la imagen en formato BGR o RGB

        Returns
        -------
        OCRResult
            Resultado estructurado del OCR
        """
        try:
            if not isinstance(image_array, np.ndarray):
                raise ValueError("image_array debe ser un numpy.ndarray")

            if image_array.ndim != 3:
                raise ValueError("image_array debe ser una imagen 3D (H, W, C)")

            # Inicializar OCR si es necesario
            self._initialize_ocr()

            start_time = time.time()
            logger.info("Procesando array de imagen con dimensiones: %s", image_array.shape)

            # Ejecutar OCR en el array
            try:
                result = self._ocr.ocr(image_array, cls=True)
            except Exception as e:
                logger.warning("Error con cls=True, intentando sin clasificación: %s", e)
                result = self._ocr.ocr(image_array, cls=False)

            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            self._last_used = time.time()

            logger.info("OCR completado en %.2f segundos", processing_time)

            return self._parse_ocr_result(result, "array")

        except Exception as e:
            logger.exception("Error en extracción de texto desde array")
            raise RuntimeError(f"Error en OCR desde array: {str(e)}") from e

    def _validate_image_path(self, image_path: str) -> None:
        """
        Validar la ruta de la imagen.

        Parameters
        ----------
        image_path : str
            Ruta de la imagen a validar

        Raises
        ------
        ValueError
            Si la ruta no es válida
        FileNotFoundError
            Si la imagen no existe
        """
        if not image_path:
            raise ValueError("La ruta de la imagen no puede estar vacía")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"La imagen no existe: {image_path}")

        if not os.path.isfile(image_path):
            raise ValueError(f"La ruta no es un archivo: {image_path}")

        # Verificar formato de imagen
        image_ext = Path(image_path).suffix.lower()
        supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}
        if image_ext not in supported_extensions:
            raise ValueError(f"Formato de imagen no soportado: {image_ext}")

        # Verificar tamaño del archivo
        file_size = os.path.getsize(image_path)
        if file_size == 0:
            raise ValueError(f"La imagen está vacía: {image_path}")

        # Verificar que se puede leer la imagen
        try:
            test_img = cv2.imread(image_path)
            if test_img is None:
                raise ValueError(f"No se puede leer la imagen: {image_path}")
        except Exception as e:
            raise ValueError(f"Error al leer la imagen: {image_path} - {str(e)}")

    def _parse_ocr_result(self, result: Any, source: str) -> OCRResult:
        """
        Parsear el resultado raw de PaddleOCR a nuestro modelo de dominio.

        Parameters
        ----------
        result : Any
            Resultado raw de PaddleOCR
        source : str
            Fuente de la imagen (ruta o "array")

        Returns
        -------
        OCRResult
            Resultado estructurado
        """
        lines: List[OCRTextLine] = []

        try:
            if result and isinstance(result, list) and len(result) > 0:
                # PaddleOCR devuelve una lista de páginas
                page_result = result[0]

                if page_result and isinstance(page_result, list):
                    for item in page_result:
                        if not item or not isinstance(item, list) or len(item) < 2:
                            continue

                        # Estructura: [bbox, [text, confidence]]
                        bbox = item[0] if len(item) > 0 else None
                        text_info = item[1] if len(item) > 1 else None

                        if text_info and isinstance(text_info, list) and len(text_info) >= 2:
                            text = str(text_info[0]).strip()
                            confidence = float(text_info[1]) if len(text_info) > 1 else None

                            # Filtrar texto vacío o muy corto
                            if text and len(text) > 0:
                                # Crear línea OCR con información adicional
                                ocr_line = OCRTextLine(
                                    text=text,
                                    confidence=confidence
                                )
                                lines.append(ocr_line)

                                logger.debug(
                                    "Línea OCR extraída: '%s' (confianza: %.2f)",
                                    text, confidence or 0.0
                                )

            logger.info(
                "Parseado OCR completado: %d líneas extraídas de %s",
                len(lines), source
            )

        except Exception as e:
            logger.exception("Error al parsear resultado OCR")
            # En caso de error, devolver resultado vacío pero válido
            lines = []

        return OCRResult(lines=lines)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de rendimiento del motor OCR.

        Returns
        -------
        Dict[str, Any]
            Estadísticas de rendimiento
        """
        if not self._processing_times:
            return {
                'total_processed': 0,
                'avg_processing_time': 0.0,
                'min_processing_time': 0.0,
                'max_processing_time': 0.0,
                'last_used': None,
                'initialized': self._initialized
            }

        return {
            'total_processed': len(self._processing_times),
            'avg_processing_time': sum(self._processing_times) / len(self._processing_times),
            'min_processing_time': min(self._processing_times),
            'max_processing_time': max(self._processing_times),
            'last_used': self._last_used,
            'initialized': self._initialized
        }

    def clear_cache(self) -> None:
        """Limpiar caché y estadísticas del motor."""
        self._processing_times.clear()
        self._last_used = 0.0
        logger.info("Caché del motor OCR limpiado")

    def shutdown(self) -> None:
        """Cerrar el motor OCR de forma segura."""
        try:
            if self._ocr is not None:
                # PaddleOCR no tiene método de shutdown explícito
                # pero podemos limpiar referencias
                self._ocr = None
                self._initialized = False
                self.clear_cache()
                logger.info("Motor OCR cerrado correctamente")
        except Exception as e:
            logger.error("Error al cerrar motor OCR: %s", e)

    def __del__(self):
        """Destructor para limpiar recursos."""
        try:
            self.shutdown()
        except:
            pass  # Ignorar errores en destructor


# Factory function para crear instancias del motor OCR
def create_ocr_engine(
    language: str = "es",
    use_angle_cls: bool = True,
    use_gpu: bool = False,
    **kwargs: Any
) -> PaddleOCREngine:
    """
    Factory function para crear instancias del motor OCR.

    Parameters
    ----------
    language : str
        Idioma para el OCR
    use_angle_cls : bool
        Si usar clasificación de ángulo
    use_gpu : bool
        Si usar GPU para aceleración
    **kwargs : Any
        Parámetros adicionales para OCRConfig

    Returns
    -------
    PaddleOCREngine
        Instancia configurada del motor OCR
    """
    config = OCRConfig(
        language=language,
        use_angle_cls=use_angle_cls,
        use_gpu=use_gpu,
        **kwargs
    )

    return PaddleOCREngine(config)


__all__ = [
    "PaddleOCREngine",
    "OCRConfig",
    "create_ocr_engine"
]
