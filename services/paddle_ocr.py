"""
OCR service: PRIORIDAD PaddleOCR (preciso). Fallback a Tesseract SOLO si el ejecutable existe.
- Import de PaddleOCR es lazy (dentro del método) para no fallar en import-time.
- Mapeo de lang: 'es' -> 'latin' (PaddleOCR usa 'latin' para lenguas romances).
"""
from __future__ import annotations
from pathlib import Path
from typing import List
import os
from shutil import which

# --- Utils ---

def _paddle_lang(lang: str) -> str:
    lang = (lang or "en").lower()
    # Paddle soporta 'en', 'ch', 'latin', 'korean', 'japan', 'fr', 'german', etc.
    if lang in {"es", "pt", "it", "ca", "ro", "nl"}:
        return "latin"
    return lang

def _tesseract_available() -> bool:
    # Evita llamar a pytesseract si no existe el ejecutable
    return bool(which("tesseract") or os.getenv("TESSERACT_CMD"))

# --- Servicio ---

class PaddleOcrService:
    """Servicio OCR preferentemente con PaddleOCR, fallback a Tesseract si está disponible."""

    def __init__(self, lang_default: str = "es") -> None:
        self._lang_default = lang_default
        self._paddle = None  # instancia de PaddleOCR (lazy)

    def extract_words(self, image_path: str, lang: str | None = None) -> List[dict]:
        img_path = str(Path(image_path))
        lang = lang or self._lang_default

        # 1) Intentar SIEMPRE PaddleOCR primero
        try:
            return self._extract_with_paddle(img_path, _paddle_lang(lang))
        except Exception as paddle_err:
            # 2) Si hay Tesseract disponible (ejecutable), usar fallback
            if _tesseract_available():
                try:
                    return self._extract_with_tesseract(img_path, lang)
                except Exception as tess_err:
                    raise RuntimeError(
                        "PaddleOCR falló y el fallback Tesseract también falló."
                    ) from tess_err
            # 3) Sin Tesseract, propagar error de Paddle con mensaje claro
            raise RuntimeError(
                "OCR con PaddleOCR falló y Tesseract no está instalado en el sistema.\n"
                "Soluciones: (a) corrige Paddle (ver logs), o (b) instala Tesseract y añade al PATH."
            ) from paddle_err

    # ----------------- Implementaciones -----------------

    def _ensure_paddle(self, lang: str) -> None:
        if self._paddle is not None:
            return
        # Import lazy para no romper en import-time
        from paddleocr import PaddleOCR  # type: ignore
        self._paddle = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            det=True,
            rec=True,
            show_log=False,
        )

    def _extract_with_paddle(self, image_path: str, lang: str) -> List[dict]:
        self._ensure_paddle(lang)
        assert self._paddle is not None
        result = self._paddle.ocr(image_path, cls=True) or []
        words: List[dict] = []
        if not result:
            return words
        for box, (text, conf) in result[0]:
            xs = [int(pt[0]) for pt in box]
            ys = [int(pt[1]) for pt in box]
            x, y = min(xs), min(ys)
            w, h = max(xs) - x, max(ys) - y
            words.append({"text": text, "confidence": float(conf), "bbox": [x, y, w, h]})
        return words

    def _extract_with_tesseract(self, image_path: str, lang: str) -> List[dict]:
        # Importar dentro (evita dependencia si no se usa)
        import pytesseract  # type: ignore
        from PIL import Image

        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)
        words: List[dict] = []
        n = len(data.get("text", []))
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            try:
                conf = float(data["conf"][i])
            except Exception:
                conf = 0.0
            x = int(data["left"][i]); y = int(data["top"][i])
            w = int(data["width"][i]); h = int(data["height"][i])
            words.append({"text": text, "confidence": conf if conf >= 0 else 0.0, "bbox": [x, y, w, h]})
        return words
