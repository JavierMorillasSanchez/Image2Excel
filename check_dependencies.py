#!/usr/bin/env python3
"""
Script para verificar que todas las dependencias estén instaladas correctamente.
"""

import sys
import importlib

def check_module(module_name, display_name=None):
    """Verificar si un módulo está disponible."""
    if display_name is None:
        display_name = module_name

    try:
        importlib.import_module(module_name)
        print(f"✅ {display_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {display_name} - FALLO: {e}")
        return False

def main():
    """Verificar todas las dependencias."""
    print("🔍 Verificando dependencias de I2E...")
    print("=" * 50)

    # Lista de módulos a verificar
    modules_to_check = [
        ("numpy", "NumPy"),
        ("PIL", "Pillow"),
        ("cv2", "OpenCV"),
        ("openpyxl", "OpenPyXL"),
        ("PyQt5", "PyQt5"),
        ("paddleocr", "PaddleOCR"),
    ]

    all_ok = True

    for module_name, display_name in modules_to_check:
        if not check_module(module_name, display_name):
            all_ok = False

    print("\n" + "=" * 50)

    if all_ok:
        print("🎉 ¡Todas las dependencias están instaladas correctamente!")
        print("\n📝 Puedes ejecutar la aplicación:")
        print("   python main.py")
    else:
        print("❌ Algunas dependencias no están instaladas correctamente.")
        print("\n🔧 Para instalar las dependencias faltantes:")
        print("   python install_dependencies.py")
        print("   o")
        print("   pip install -r requirements.txt")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
