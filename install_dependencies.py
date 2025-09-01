#!/usr/bin/env python3
"""
Script de instalación automática de dependencias para I2E.
Maneja la instalación de todas las librerías necesarias y resuelve problemas comunes.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Ejecutar comando y mostrar resultado."""
    print(f"\n🔧 {description}...")
    print(f"Comando: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado exitosamente")
        if result.stdout:
            print(f"Salida: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Verificar versión de Python."""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")

    if version < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        return False

    print("✅ Versión de Python compatible")
    return True

def check_pip():
    """Verificar que pip esté disponible."""
    try:
        import pip
        print("✅ pip disponible")
        return True
    except ImportError:
        print("❌ Error: pip no está disponible")
        return False

def upgrade_pip():
    """Actualizar pip a la última versión."""
    return run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Actualizando pip"
    )

def install_basic_dependencies():
    """Instalar dependencias básicas."""
    basic_deps = [
        "numpy>=1.24.0",
        "Pillow>=9.0.0",
        "opencv-python>=4.8.0",
        "openpyxl>=3.1.0"
    ]

    for dep in basic_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Instalando {dep}"):
            return False

    return True

def install_pyqt5():
    """Instalar PyQt5 con manejo de errores."""
    print("\n🎨 Instalando PyQt5...")

    # Intentar instalación estándar
    if run_command(f"{sys.executable} -m pip install PyQt5", "Instalando PyQt5"):
        return True

    print("⚠️  PyQt5 falló, intentando alternativas...")

    # Alternativa 1: Solo binarios
    if run_command(f"{sys.executable} -m pip install PyQt5 --only-binary=all", "Instalando PyQt5 (solo binarios)"):
        return True

    # Alternativa 2: PySide2
    print("🔄 Intentando con PySide2 como alternativa...")
    if run_command(f"{sys.executable} -m pip install PySide2", "Instalando PySide2"):
        print("✅ PySide2 instalado. La aplicación funcionará con esta alternativa.")
        return True

    # Alternativa 3: PySide6
    print("🔄 Intentando con PySide6 como alternativa...")
    if run_command(f"{sys.executable} -m pip install PySide6", "Instalando PySide6"):
        print("✅ PySide6 instalado. La aplicación funcionará con esta alternativa.")
        return True

    print("❌ No se pudo instalar ninguna interfaz gráfica")
    return False

def install_paddleocr():
    """Instalar PaddleOCR con manejo de errores."""
    print("\n🤖 Instalando PaddleOCR...")

    # Instalar PaddlePaddle primero - versión compatible
    print("📦 Instalando PaddlePaddle...")
    paddlepaddle_commands = [
        "paddlepaddle>=2.5.1",
        "paddlepaddle",
        "paddlepaddle==2.5.2"
    ]

    paddlepaddle_installed = False
    for cmd in paddlepaddle_commands:
        if run_command(f"{sys.executable} -m pip install {cmd}", f"Instalando PaddlePaddle ({cmd})"):
            paddlepaddle_installed = True
            break

    if not paddlepaddle_installed:
        print("❌ No se pudo instalar PaddlePaddle")
        return False

    # Instalar PaddleOCR
    print("📦 Instalando PaddleOCR...")
    paddleocr_commands = [
        "paddleocr>=2.6.0",
        "paddleocr",
        "paddleocr==2.7.0"
    ]

    paddleocr_installed = False
    for cmd in paddleocr_commands:
        if run_command(f"{sys.executable} -m pip install {cmd}", f"Instalando PaddleOCR ({cmd})"):
            paddleocr_installed = True
            break

    if not paddleocr_installed:
        print("❌ No se pudo instalar PaddleOCR")
        return False

    return True

def install_dev_dependencies():
    """Instalar dependencias de desarrollo (opcionales)."""
    dev_deps = [
        "black>=23.0.0",
        "ruff>=0.1.0",
        "pytest>=7.0.0"
    ]

    print("\n🛠️  Instalando dependencias de desarrollo...")

    for dep in dev_deps:
        try:
            run_command(f"{sys.executable} -m pip install {dep}", f"Instalando {dep}")
        except:
            print(f"⚠️  {dep} no se pudo instalar (opcional)")

    return True

def verify_installation():
    """Verificar que todas las dependencias estén instaladas."""
    print("\n🔍 Verificando instalación...")

    required_modules = [
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("numpy", "NumPy"),
        ("openpyxl", "OpenPyXL")
    ]

    # Verificar módulos básicos
    for module, name in required_modules:
        try:
            __import__(module)
            print(f"✅ {name} disponible")
        except ImportError:
            print(f"❌ {name} no disponible")
            return False

    # Verificar interfaz gráfica
    gui_available = False
    for gui_module in ["PyQt5", "PySide2", "PySide6"]:
        try:
            __import__(gui_module)
            print(f"✅ {gui_module} disponible")
            gui_available = True
            break
        except ImportError:
            continue

    if not gui_available:
        print("❌ Ninguna interfaz gráfica disponible")
        return False

    # Verificar PaddleOCR
    try:
        import paddleocr
        print("✅ PaddleOCR disponible")
    except ImportError:
        print("❌ PaddleOCR no disponible")
        return False

    print("\n🎉 ¡Todas las dependencias están instaladas correctamente!")
    return True

def main():
    """Función principal de instalación."""
    print("🚀 I2E - Instalador de Dependencias")
    print("=" * 50)

    # Verificaciones iniciales
    if not check_python_version():
        return 1

    if not check_pip():
        return 1

    # Actualizar pip
    upgrade_pip()

    # Instalar dependencias
    if not install_basic_dependencies():
        print("❌ Error instalando dependencias básicas")
        return 1

    if not install_pyqt5():
        print("❌ Error instalando interfaz gráfica")
        return 1

    if not install_paddleocr():
        print("❌ Error instalando PaddleOCR")
        return 1

    # Dependencias de desarrollo (opcionales)
    install_dev_dependencies()

    # Verificar instalación
    if not verify_installation():
        print("❌ Error en la verificación de dependencias")
        return 1

    print("\n🎯 Instalación completada exitosamente!")
    print("\n📝 Próximos pasos:")
    print("1. Ejecuta: python main.py")
    print("2. Si tienes problemas, ejecuta: python test_app.py")
    print("3. Consulta el README.md para más información")

    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
