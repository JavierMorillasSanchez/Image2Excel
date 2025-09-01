# Instrucciones de Configuración

## Instalación de Dependencias

### 1. Instalar Python
Asegúrate de tener Python 3.7 o superior instalado.

### 2. Instalar las dependencias de Python
```bash
pip install -r requirements.txt
```

### 3. Instalar PaddleOCR

PaddleOCR se instalará automáticamente con las dependencias de Python. No requiere instalación manual adicional.

### 4. Configuración de idioma (opcional)
PaddleOCR incluye soporte para múltiples idiomas. El idioma español está incluido por defecto.

## Ejecutar la Aplicación

```bash
python main.py
```

## Crear Ejecutable con PyInstaller

### Opción 1: Ejecutable simple
```bash
pyinstaller --onefile --windowed main.py
```

### Opción 2: Con icono personalizado (si tienes un archivo .ico)
```bash
pyinstaller --onefile --windowed --icon=icon.ico main.py
```

### Opción 3: Configuración avanzada
```bash
pyinstaller --onefile --windowed --name "Convertidor_Imagen_Excel" --add-data "requirements.txt;." main.py
```

El ejecutable se creará en la carpeta `dist/`.

## Personalización

### Cambiar Colores
En el archivo `main.py`, busca el diccionario `self.colors` en la clase `ImageToExcelApp` y modifica los valores hexadecimales según tus preferencias.

### Añadir Nuevos Formatos de Imagen
Modifica la línea de filtros en el método `select_image()`:
```python
"Archivos de Imagen (*.png *.jpg *.jpeg *.bmp *.tiff *.gif *.webp)"
```

### Personalizar Salida de Excel
Modifica el método `run()` en la clase `OCRWorker` para cambiar el formato del archivo Excel generado.