# main.py
"""Entry-point (composition root) y mínima UI/CLI.

PyQt5 permanece igual si ya tienes una ventana. Para simplificar,
dejamos aquí una CLI utilizable por CI y para pruebas.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import logging

from infrastructure.logging_config import configure_logging
from config import get_config
from image2excel.use_cases import RunImageToExcel, RunImageToExcelConfig
from image2excel.adapters import PaddleOcrAdapter, BasicParserAdapter, OpenpyxlExporterAdapter


def build_use_case() -> RunImageToExcel:
    ocr = PaddleOcrAdapter()
    parser = BasicParserAdapter()
    exporter = OpenpyxlExporterAdapter()
    return RunImageToExcel(ocr=ocr, parser=parser, exporter=exporter)


def run_cli() -> int:
    ap = argparse.ArgumentParser(description="Image2Excel - OCR a Excel")
    ap.add_argument("image", type=Path, help="Ruta a la imagen")
    ap.add_argument("--out", type=Path, default=Path.cwd(), help="Directorio de salida")
    ap.add_argument("--lang", default="es", help="Idioma OCR (ej. es, en)")
    ap.add_argument("--max-cols", type=int, default=None, help="Límite de columnas del parser")
    ap.add_argument("--filename", default="texto_extraido.xlsx", help="Nombre de salida")
    args = ap.parse_args()

    cfg = get_config("production")
    configure_logging(level=logging.INFO if not cfg.debug else logging.DEBUG)

    use_case = build_use_case()
    xlsx = use_case(
        image_path=args.image,
        output_dir=args.out,
        cfg=RunImageToExcelConfig(lang=args.lang, max_cols=args.max_cols, output_filename=args.filename),
    )
    print(f"✅ Excel generado: {xlsx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
