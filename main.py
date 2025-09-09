"""
Aplicación principal Image2Excel.

Punto de entrada para la aplicación de escritorio que convierte imágenes a Excel.
"""

from __future__ import annotations
import sys
import logging
from pathlib import Path

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

def main():
    """Función principal que inicia la aplicación GUI."""
    try:
        from PyQt5.QtWidgets import QApplication
        from gui.app_window import ImageToExcelApp

        # Crear aplicación Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Image2Excel")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("I2E Team")

        # Crear y mostrar ventana principal
        window = ImageToExcelApp()
        window.show()

        # Ejecutar aplicación
        return app.exec_()

    except ImportError as e:
        print(f"❌ Error: No se pudo importar PyQt5. {e}")
        print("💡 Instala PyQt5 con: pip install PyQt5")
        return 1
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
