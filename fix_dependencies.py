#!/usr/bin/env python3
"""
Script para solucionar conflictos de dependencias en I2E.
Limpia dependencias conflictivas e instala versiones compatibles.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Ejecutar comando y mostrar resultado."""
    print(f"\n{description}...")
    print(f"Comando: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"{description} completado exitosamente")
        if result.stdout:
            print(f"Salida: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error en {description}: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def clean_conflicting_packages():
    """Limpiar paquetes que causan conflictos."""
    print("\nLimpiando paquetes conflictivos...")

    conflicting_packages = [
        "opencv-python",
        "opencv-python-headless",
        "numpy",
        "paddleocr",
        "paddlepaddle",
        "imgaug"
    ]

    for package in conflicting_packages:
        print(f"Desinstalando {package}...")
        run_command(f"{sys.executable} -m pip uninstall {package} -y", f"Desinstalando {package}")

    return True

def install_compatible_versions():
    """Instalar versiones compatibles en orden correcto."""
    print("\nInstalando versiones compatibles...")

    # Orden específico para evitar conflictos
    installation_steps = [
        ("numpy==1.24.3", "NumPy compatible"),
        ("opencv-python==4.6.0.66", "OpenCV compatible con PaddleOCR"),
        ("paddlepaddle==2.5.2", "PaddlePaddle estable"),
        ("paddleocr==2.7.0", "PaddleOCR compatible"),
        ("Pillow", "Pillow para procesamiento de imágenes"),
        ("openpyxl", "OpenPyXL para Excel"),
        ("PyQt5", "PyQt5 para interfaz gráfica")
    ]

    for package, description in installation_steps:
        if not run_command(f"{sys.executable} -m pip install {package}", f"Instalando {description}"):
            print(f"Error al instalar {package}")
            return False

    return True

def verify_compatibility():
    """Verificar que las dependencias sean compatibles."""
    print("\nVerificando compatibilidad...")

    try:
        # Verificar NumPy y OpenCV
        result = subprocess.run([
            sys.executable, "-c",
            "import numpy; import cv2; print('NumPy:', numpy.__version__); print('OpenCV:', cv2.__version__)"
        ], capture_output=True, text=True, check=True)

        print(result.stdout.strip())

        # Verificar PaddleOCR
        result = subprocess.run([
            sys.executable, "-c",
            "import paddleocr; print('PaddleOCR:', paddleocr.__version__)"
        ], capture_output=True, text=True, check=True)

        print(result.stdout.strip())

        print("\n¡Todas las dependencias son compatibles!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error en verificación: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def main():
    """Función principal de limpieza y reinstalación."""
    print("I2E - Solucionador de Conflictos de Dependencias")
    print("=" * 60)

    # Limpiar paquetes conflictivos
    if not clean_conflicting_packages():
        print("Error limpiando paquetes conflictivos")
        return 1

    # Instalar versiones compatibles
    if not install_compatible_versions():
        print("Error instalando versiones compatibles")
        return 1

    # Verificar compatibilidad
    if not verify_compatibility():
        print("Error en verificación de compatibilidad")
        return 1

    print("\n¡Conflictos de dependencias resueltos exitosamente!")
    print("\nProximos pasos:")
    print("1. Ejecuta: python main.py")
    print("2. Si tienes problemas, ejecuta: python test_app.py")

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nProceso cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)
