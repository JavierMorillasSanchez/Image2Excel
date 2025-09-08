# image2excel/adapters.py
"""Adapters: implementaciones concretas de los puertos usando servicios ligeros.

Sin dependencia de services.parser: parser básico embebido aquí.
"""

from __future__ import annotations
from pathlib import Path
from typing import Iterable, List

from .ports import OcrEngine, TableParser, ExcelExporter, OcrWord, Table, TableRow

# OCR ligero (pytesseract + PIL; sin cv2).
from services.paddle_ocr import PaddleOcrService  # usa este servicio ya corregido

# Exportador a Excel (openpyxl)
from services.exporter import ExcelExporter as ExcelExporterImpl


# -------------------------- OCR Adapter --------------------------

class PaddleOcrAdapter(OcrEngine):
    def __init__(self, lang_default: str = "es") -> None:
        self._svc = PaddleOcrService(lang_default)

    def extract_words(self, image_path: Path, lang: str) -> List[OcrWord]:
        result = self._svc.extract_words(str(image_path), lang=lang)
        words: List[OcrWord] = [
            OcrWord(
                text=w["text"],
                confidence=float(w.get("confidence", 0.0)),
                x=int(w["bbox"][0]),
                y=int(w["bbox"][1]),
                w=int(w["bbox"][2]),
                h=int(w["bbox"][3]),
            )
            for w in result
            if (w.get("text") or "").strip()
        ]
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
        # Pasamos el objeto Table directamente, porque services/exporter.py valida table.rows
        out = self._svc.export_table(table, str(output_dir), filename)
        return Path(out)
