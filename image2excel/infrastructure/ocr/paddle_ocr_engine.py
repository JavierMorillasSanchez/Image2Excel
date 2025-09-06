from __future__ import annotations
from typing import Optional
from ...domain.models import OcrResult, Table
from ...domain.ports import OcrEngine, TableDetector


class PaddleOcrEngine(OcrEngine):
    """OCR + table (si hay) usando PaddleOCR + PP-Structure."""

    def __init__(self, *, table_detector: Optional[TableDetector] = None, lang: str = "en") -> None:
        self._table_detector = table_detector
        self._lang = lang
        self._ocr = None  # lazy

    def _ensure_ocr(self) -> None:
        if self._ocr is None:
            from paddleocr import PaddleOCR  # type: ignore
            # `use_angle_cls=True` mejora textos inclinados; ajusta `lang` si quieres "es"
            self._ocr = PaddleOCR(use_angle_cls=True, lang=self._lang, show_log=False)

    def run_ocr(self, image: "Image") -> OcrResult:
        self._ensure_ocr()
        # Extrae texto general (para fallback cuando no hay tabla estructurada)
        # Resultado es lista de líneas con (bbox, (text, score))
        result = self._ocr.ocr(image, cls=True)
        lines = []
        if result and isinstance(result, list):
            for page in result:
                for _, (txt, _score) in page:
                    if txt:
                        lines.append(txt)

        text = "\n".join(lines)

        table: Optional[Table] = None
        if self._table_detector:
            try:
                table = self._table_detector.detect_table(image, text)
            except Exception:
                table = None

        return OcrResult(text=text, table=table)
