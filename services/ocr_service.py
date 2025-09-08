# services/ocr_service.py
from __future__ import annotations
from pathlib import Path
from typing import List

try:
    import pytesseract  # type: ignore
    from PIL import Image
    _HAS_TESS = True
except Exception:
    _HAS_TESS = False


class PaddleOcrService:
    """
    Servicio OCR ligero para ejecución local/CLI (sin cv2).
    Firma compatible con el adapter: extract_words(...) -> list[dict].
    """
    def __init__(self, lang_default: str = "es") -> None:
        self._lang_default = lang_default
        self._paddle_ocr = None  # se usa solo si no hay pytesseract

    def extract_words(self, image_path: str, lang: str | None = None) -> List[dict]:
        lang = (lang or self._lang_default).lower()
        path = str(Path(image_path))

        if _HAS_TESS:
            return self._extract_with_tesseract(path, lang)

        # Último recurso: carga lazy de PaddleOCR (si lo tuvieras instalado).
        return self._extract_with_paddle_lazy(path, lang)

    def _extract_with_tesseract(self, image_path: str, lang: str) -> List[dict]:
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
            x, y, w, h = int(data["left"][i]), int(data["top"][i]), int(data["width"][i]), int(data["height"][i])
            words.append({"text": text, "confidence": conf if conf >= 0 else 0.0, "bbox": [x, y, w, h]})
        return words

    def _extract_with_paddle_lazy(self, image_path: str, lang: str) -> List[dict]:
        from paddleocr import PaddleOCR  # type: ignore
        if self._paddle_ocr is None:
            self._paddle_ocr = PaddleOCR(use_angle_cls=True, lang=lang, det=True, rec=True, show_log=False)

        result = self._paddle_ocr.ocr(image_path, cls=True) or []
        words: List[dict] = []
        if not result:
            return words
        for box, (text, conf) in result[0]:
            xs = [int(pt[0]) for pt in box]
            ys = [int(pt[1]) for pt in box]
            x, y = min(xs), min(ys)
            w = max(xs) - x
            h = max(ys) - y
            words.append({"text": text, "confidence": float(conf), "bbox": [x, y, w, h]})
        return words
