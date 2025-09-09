# services/paddle_ocr.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np
from paddleocr import PaddleOCR


@dataclass(frozen=True)
class OCRPrecisionProfile:
    det_db_thresh: float = 0.25
    det_db_box_thresh: float = 0.35
    det_db_unclip_ratio: float = 1.8
    use_dilation: bool = True
    use_angle_cls: bool = True


def _get_profile(name: str | None) -> OCRPrecisionProfile:
    k = (name or "precision").lower()
    if k == "fast":
        return OCRPrecisionProfile(0.30, 0.55, 1.5, False, True)
    if k in ("balanced", "balanceado"):
        return OCRPrecisionProfile(0.28, 0.45, 1.6, True, True)
    return OCRPrecisionProfile()


class PaddleOcrService:
    """
    Servicio OCR basado EXCLUSIVAMENTE en PaddleOCR.
    No importa ni usa pytesseract; no existe fallback a Tesseract.
    API pública:
      - extract_words(image_path: str, lang: str = "es") -> List[ (poly4, (text, conf)) ]
    """

    def __init__(self, profile: str = "precision", use_gpu: bool = False):
        self._prof = _get_profile(profile)
        # Idioma por defecto “es”; si quieres cambiarlo por llamada, se hace en extract_words
        self._use_gpu = use_gpu
        self._lang_default = "es"
        # Inicializamos con el idioma por defecto; si luego llega otro idioma, recreamos ocr.
        self._ocr = PaddleOCR(
            use_angle_cls=self._prof.use_angle_cls,
            lang=self._lang_default,
            use_gpu=self._use_gpu,
            det_db_thresh=self._prof.det_db_thresh,
            det_db_box_thresh=self._prof.det_db_box_thresh,
            det_db_unclip_ratio=self._prof.det_db_unclip_ratio,
            use_dilation=self._prof.use_dilation,
            show_log=False,
            rec_algorithm="CRNN",
        )

    @staticmethod
    def _preprocess(img_bgr: np.ndarray) -> np.ndarray:
        """Binarización ligera para manuscrito; devuelve BGR con texto oscuro."""
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        th = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 19, 9
        )
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8), iterations=1)
        return cv2.cvtColor(255 - th, cv2.COLOR_GRAY2BGR)

    def _ensure_lang(self, lang: str):
        if lang and lang != self._lang_default:
            # recrea el objeto OCR con el idioma solicitado
            self._lang_default = lang
            self._ocr = PaddleOCR(
                use_angle_cls=self._prof.use_angle_cls,
                lang=self._lang_default,
                use_gpu=self._use_gpu,
                det_db_thresh=self._prof.det_db_thresh,
                det_db_box_thresh=self._prof.det_db_box_thresh,
                det_db_unclip_ratio=self._prof.det_db_unclip_ratio,
                use_dilation=self._prof.use_dilation,
                show_log=False,
                rec_algorithm="CRNN",
            )

    def extract_words(self, image_path: str, lang: str = "es") -> List[Tuple[List[List[int]], Tuple[str, float]]]:
        """OCR → devuelve lista de (poly4, (text, conf)) como PaddleOCR estándar."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"No se pudo leer la imagen: {image_path}")
        self._ensure_lang(lang or "es")
        pre = self._preprocess(img)
        result = self._ocr.ocr(pre, cls=self._prof.use_angle_cls)
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], list):
            return result[0]
        return result
