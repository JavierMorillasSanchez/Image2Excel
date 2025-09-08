from __future__ import annotations
from pathlib import Path
from typing import List, Sequence, Any, Iterable
from openpyxl import Workbook
import logging

logger = logging.getLogger("ExcelExporter")

class ExcelExporter:
    """
    Exportador tolerante:
    - Acepta un objeto con .rows (y cada fila con .cells) -> Table del dominio
    - O una lista de listas de str
    """

    def __init__(self, sheet_name: str = "Texto Extraído", include_confidence: bool = True) -> None:
        self.sheet_name = sheet_name
        self.include_confidence = include_confidence
        logger.info(
            "ExcelExporter inicializado con configuración: archivo=texto_extraido.xlsx, hoja=%s, incluir_confianza=%s",
            self.sheet_name, self.include_confidence
        )

    # ------------------ API pública ------------------

    def export_table(self, table_or_rows: Any, output_dir: str | Path, filename: str) -> str:
        try:
            rows = self._to_rows(table_or_rows)
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / filename

            wb = Workbook()
            ws = wb.active
            ws.title = self.sheet_name

            for r in rows or [[]]:
                ws.append([str(c) for c in (list(r) if isinstance(r, (list, tuple)) else [r])])

            wb.save(out_path)
            return str(out_path)
        except Exception as e:
            logger.error("Error durante la exportación a Excel", exc_info=True)
            raise RuntimeError(f"Error en exportación Excel: {e}") from e

    # ------------------ Helpers ------------------

    def _to_rows(self, table_or_rows: Any) -> List[List[str]]:
        """
        Normaliza la entrada a list[list[str]] aceptando:
        - Objeto con .rows -> cada fila puede tener .cells
        - list[list[str]]
        """
        # Caso Table del dominio (duck typing)
        if hasattr(table_or_rows, "rows"):
            rows_attr = getattr(table_or_rows, "rows")
            rows_out: List[List[str]] = []
            for r in rows_attr:
                if hasattr(r, "cells"):
                    rows_out.append([str(c) for c in getattr(r, "cells")])
                elif isinstance(r, (list, tuple)):
                    rows_out.append([str(c) for c in r])
                else:
                    rows_out.append([str(r)])
            return rows_out

        # Caso lista directa
        if isinstance(table_or_rows, (list, tuple)):
            rows_out: List[List[str]] = []
            for r in table_or_rows:
                if isinstance(r, (list, tuple)):
                    rows_out.append([str(c) for c in r])
                else:
                    rows_out.append([str(r)])
            return rows_out

        raise ValueError("El parámetro 'table' debe ser Table (.rows) o list[list[str]]")
