from __future__ import annotations
import argparse
from pathlib import Path
import logging

try:
    from infrastructure.logging_config import configure_logging as _cfg_log
except Exception:
    _cfg_log = None

from image2excel.use_cases import RunImageToExcel, RunImageToExcelConfig
from image2excel.adapters import PaddleOcrAdapter, BasicParserAdapter, OpenpyxlExporterAdapter


def configure_logging(level: int = logging.INFO) -> None:
    if _cfg_log:
        _cfg_log(level=level)
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )


def build_use_case() -> RunImageToExcel:
    ocr = PaddleOcrAdapter()
    parser = BasicParserAdapter()
    exporter = OpenpyxlExporterAdapter()
    return RunImageToExcel(ocr=ocr, parser=parser, exporter=exporter)


def run_cli() -> int:
    ap = argparse.ArgumentParser(description="Image2Excel - OCR a Excel (modo estable sin cv2)")
    ap.add_argument("image", type=Path, help="Ruta a la imagen de entrada")
    ap.add_argument("--out", type=Path, default=Path.cwd(), help="Directorio de salida")
    ap.add_argument("--lang", default="es", help="Idioma OCR (es/en/...)")
    ap.add_argument("--filename", default="texto_extraido.xlsx", help="Nombre del .xlsx")
    ap.add_argument("--debug", action="store_true", help="Activa logging DEBUG")
    args = ap.parse_args()

    configure_logging(level=logging.DEBUG if args.debug else logging.INFO)

    use_case = build_use_case()
    xlsx = use_case(
        image_path=args.image,
        output_dir=args.out,
        cfg=RunImageToExcelConfig(lang=args.lang, output_filename=args.filename),
    )
    print(f"✅ Excel generado: {xlsx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
