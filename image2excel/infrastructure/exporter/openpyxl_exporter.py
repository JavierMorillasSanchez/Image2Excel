from __future__ import annotations
from pathlib import Path
from openpyxl import Workbook
from ...domain.models import Table, ExportResult, Cell, TableRow
from ...domain.ports import ExcelExporter


class OpenpyxlExcelExporter(ExcelExporter):
    """Adaptador concreto para exportar tablas a Excel usando Openpyxl."""

    def export_table(self, table: Table, output_path: Path) -> ExportResult:
        if not table.rows:
            raise ValueError("Tabla vacía: no hay filas que exportar.")

        wb = Workbook()
        ws = wb.active
        ws.title = "Texto Extraído"

        for r_idx, row in enumerate(table.rows, start=1):
            for c_idx, cell in enumerate(row.cells, start=1):
                ws.cell(row=r_idx, column=c_idx, value=cell.text)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path.as_posix())

        return ExportResult(output_path=output_path)
