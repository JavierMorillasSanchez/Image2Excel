from __future__ import annotations
from typing import Optional, List, Tuple
from ...domain.models import Table, TableRow, Cell
from ...domain.ports import TableDetector

# PP-Structure usa PaddleOCR internamente
# Evitamos el import global para no romper si no está instalada.
class PaddleTableDetector(TableDetector):
    """Detecta estructura de tabla en imágenes usando PP-Structure (PaddleOCR).

    Retorna un Table con filas y celdas alineadas. Si no se puede determinar,
    retorna None para que el caso de uso haga fallback a texto por líneas.
    """

    def __init__(self) -> None:
        # Config por defecto de PP-Structure orientada a tablas.
        # El TableSystem de PaddleOCR devuelve HTML estructurado (<table><tr><td>).
        from paddleocr.ppstructure.table.predict_table import TableSystem  # type: ignore

        # model_type="structure" usa un pipeline que detecta la estructura de la tabla
        # sin necesidad de OCR de texto si no quieres (pero lo hace).
        self._table_sys = TableSystem(table_model_dir=None)  # usa modelos por defecto

    def detect_table(self, image: "Image", ocr_text: str) -> Optional[Table]:
        """
        Ejecuta table recognition. Convierte el HTML y/o celdas detectadas
        a nuestro modelo Table. Si no detecta estructura, retorna None.
        """
        import numpy as np

        # Convertimos imagen PIL/OpenCV a ndarray (PP-Structure espera ndarrays BGR)
        if hasattr(image, "to_ndarray"):  # por si fuese un wrapper
            nd = image.to_ndarray()
        elif hasattr(image, "numpy"):  # por si fuese un tensor
            nd = image.numpy()
        else:
            try:
                # Si es PIL
                from PIL import Image as PILImage
                if isinstance(image, PILImage.Image):
                    nd = np.array(image)[:, :, ::-1]  # RGB -> BGR
                else:
                    nd = np.array(image)
            except Exception:
                nd = np.array(image)

        res = self._table_sys(nd)

        # `res` suele incluir:
        # - "html": HTML string con <table><tr><td>...</td></tr></table>
        # - "cell_bbox": lista de celdas [x1,y1,x2,y2], y contenido
        # Vamos a priorizar el HTML para conservar estructura por filas.

        html = res.get("html")
        if not html:
            return None

        # Parseo HTML simple para construir filas y celdas en orden visual
        # Nota: esto no almacena "colspan/rowspan". Si quieres merges POR EXCEL
        # podrías extender el modelo para guardarlos.
        try:
            from bs4 import BeautifulSoup  # lightweight, pero si no quieres dependencia, parsea a mano
        except Exception as e:
            # Sin BeautifulSoup, intentamos un parseo básico
            return self._parse_html_naive(html)

        soup = BeautifulSoup(html, "html.parser")
        rows: List[TableRow] = []
        for tr in soup.find_all("tr"):
            cells = []
            for td in tr.find_all(["td", "th"]):
                text = (td.get_text() or "").strip()
                cells.append(Cell(text=text or ""))
            if cells:
                rows.append(TableRow(cells=cells))

        if not rows:
            return None
        return Table(rows=rows)

    # --- Auxiliar sin BeautifulSoup (naive) ---
    def _parse_html_naive(self, html: str) -> Optional[Table]:
        # Muy básico: separar por <tr> y <td>
        import re

        tr_blocks = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.IGNORECASE | re.DOTALL)
        rows: List[TableRow] = []
        for block in tr_blocks:
            tds = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", block, flags=re.IGNORECASE | re.DOTALL)
            cells = [Cell(text=self._strip_tags(td)) for td in tds]
            if cells:
                rows.append(TableRow(cells=cells))
        if not rows:
            return None
        return Table(rows=rows)

    def _strip_tags(self, s: str) -> str:
        import re
        s = re.sub(r"<[^>]+>", "", s)
        return " ".join(s.split())
