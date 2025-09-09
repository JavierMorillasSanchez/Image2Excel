# image2excel/adapters.py
"""Adapters: implementaciones concretas de los puertos usando servicios ligeros.

Sin dependencia de services.parser: parser básico embebido aquí.
"""

from __future__ import annotations
from pathlib import Path
from typing import Iterable, List, Tuple

from .ports import OcrEngine, TableParser, ExcelExporter, OcrWord, Table, TableRow

# Servicio OCR (Paddle), SIN Tesseract
from services.paddle_ocr import PaddleOcrService  # usa este servicio ya corregido

# Exportador a Excel (openpyxl)
from services.exporter import ExcelExporter as ExcelExporterImpl


# -------------------------- OCR Adapter --------------------------

class PaddleOcrAdapter(OcrEngine):
    """
    Adaptador OCR que usa exclusivamente PaddleOcrService y
    convierte la salida cruda de PaddleOCR -> lista[OcrWord].
    """
    def __init__(self):
        # PaddleOcrService acepta profile y use_gpu
        self._svc = PaddleOcrService(profile="precision", use_gpu=False)

    def extract_words(self, image_path: str, lang: str = "es") -> List[OcrWord]:
        """
        Devuelve una lista de OcrWord con coordenadas de bounding box,
        que es lo que el parser / use_case esperan.
        """
        # Salida PaddleOCR: [ [poly([[x,y]x4]), (text, conf)] , ... ]
        results: List[Tuple[List[List[int]], Tuple[str, float]]] = self._svc.extract_words(
            str(Path(image_path)), lang=lang
        )
        words: List[OcrWord] = []

        for poly, (txt, conf) in results:
            if not txt or not str(txt).strip():
                continue
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            x_min, x_max = float(min(xs)), float(max(xs))
            y_min, y_max = float(min(ys)), float(max(ys))
            w = max(1.0, x_max - x_min)
            h = max(1.0, y_max - y_min)
            words.append(
                OcrWord(text=str(txt).strip(), confidence=float(conf), x=int(x_min), y=int(y_min), w=int(w), h=int(h))
            )
        return words


# ------------------------ Parser Adapter -------------------------

class BasicParserAdapter(TableParser):
    """Parser mínimo: agrupa por línea (Y) y ordena por X. Cada palabra = una celda."""
    # ⚠️ Importante: NO tiene __init__ ni usa BasicTableParser

    def words_to_table(self, words: Iterable[OcrWord], max_cols: int | None = None) -> Table:
        items = [w for w in words if (w.text or "").strip()]
        if not items:
            return Table(rows=[])

        # Orden global por Y, luego X
        items.sort(key=lambda t: (t.y, t.x))

        # Umbral de agrupación vertical basado en altura media
        avg_h = max(1, int(sum(t.h for t in items) / len(items)))
        y_threshold = max(4, avg_h // 2)

        rows: list[list[OcrWord]] = []
        current: list[OcrWord] = [items[0]]

        for w in items[1:]:
            if abs(w.y - current[-1].y) <= y_threshold:
                current.append(w)
            else:
                rows.append(sorted(current, key=lambda t: t.x))
                current = [w]
        rows.append(sorted(current, key=lambda t: t.x))

        # Convierte a TableRow
        table_rows: list[TableRow] = []
        for line in rows:
            cells = [w.text for w in line]
            if max_cols and max_cols > 0 and len(cells) > max_cols:
                head = cells[: max_cols - 1]
                tail = " ".join(cells[max_cols - 1 :])
                cells = head + [tail]
            table_rows.append(TableRow(cells=cells if cells else [""]))

        return Table(rows=table_rows)


# ----------------------- Exporter Adapter ------------------------

class OpenpyxlExporterAdapter(ExcelExporter):
    def __init__(self) -> None:
        self._svc = ExcelExporterImpl()

    def export(self, table: Table, output_dir: Path, filename: str) -> Path:
        out = self._svc.export_table([r.cells for r in table.rows], str(output_dir), filename)
        return Path(out)
