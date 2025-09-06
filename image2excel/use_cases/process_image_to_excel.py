from __future__ import annotations

from pathlib import Path
from typing import Optional, List

from ..domain.models import Table, TableRow, Cell, ExportResult
from ..domain.ports import ImageLoader, Preprocessor, OcrEngine, ExcelExporter


class ProcessImageToExcel:
    """Caso de uso: dado un path de imagen, genera un Excel con la tabla detectada."""

    def __init__(
        self,
        *,
        image_loader: ImageLoader,
        preprocessor: Optional[Preprocessor],
        ocr_engine: OcrEngine,
        excel_exporter: ExcelExporter,
        default_output_name: str = "texto_extraido.xlsx",
    ) -> None:
        self._image_loader = image_loader
        self._preprocessor = preprocessor
        self._ocr_engine = ocr_engine
        self._excel_exporter = excel_exporter
        self._default_output_name = default_output_name

    def execute(self, image_path: Path, output_dir: Path) -> ExportResult:
        image = self._image_loader.load(image_path)

        if self._preprocessor:
            image = self._preprocessor.preprocess(image)

        ocr = self._ocr_engine.run_ocr(image)

        if ocr.table and ocr.table.rows:
            table = ocr.table
        else:
            # Si no hay tabla estructurada, generamos una con el texto línea por línea
            lines: List[str] = [ln for ln in (ocr.text or "").splitlines() if ln.strip()]
            rows = [TableRow(cells=[Cell(text=line)]) for line in lines]
            table = Table(rows=rows)

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / self._default_output_name

        return self._excel_exporter.export_table(table, output_path)
