#!/usr/bin/env python3
"""
Script para construir el ejecutable de la aplicación
"""

import os
import subprocess
import sys

def build_executable():
    """
    Construir ejecutable usando PyInstaller
    """
    
    # Verificar que PyInstaller esté instalado
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller no está instalado. Ejecuta: pip install pyinstaller")
        return False
    
    # Comando para construir el ejecutable
    cmd = [
        'pyinstaller',
        '--onefile',          # Un solo archivo ejecutable
        '--windowed',         # Sin ventana de consola (solo para GUI)
        '--name', 'Convertidor_Imagen_Excel',  # Nombre del ejecutable
        '--clean',            # Limpiar cache antes de construir
        'main.py'             # Archivo principal
    ]
    
    print("Construyendo ejecutable...")
    print(f"Comando: {' '.join(cmd)}")
    
    try:
        # Ejecutar PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Ejecutable creado exitosamente!")
        print("📁 Busca el archivo en la carpeta 'dist/'")
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Error al crear el ejecutable:")
        print(e.stdout)
        print(e.stderr)
        return False

def clean_build_files():
    """
    Limpiar archivos temporales de construcción
    """
    import shutil
    
    # Directorios a limpiar
    dirs_to_clean = ['build', '__pycache__', 'dist']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Limpiando directorio: {dir_name}")
            shutil.rmtree(dir_name)
    
    # Limpiar archivos .spec
    for file in os.listdir('.'):
        if file.endswith('.spec'):
            print(f"Eliminando archivo: {file}")
            os.remove(file)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean_build_files()
        print("✅ Archivos de construcción limpiados")
    else:
        success = build_executable()
        if success:
            print("\n🎉 ¡Aplicación lista para distribuir!")
            print("💡 Consejo: Puedes ejecutar 'python build_exe.py clean' para limpiar archivos temporales")