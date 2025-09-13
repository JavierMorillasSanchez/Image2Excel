# contexto_general

## 📝 Introducción del proyecto
Este proyecto, llamado **Image2Excel**, consiste en el desarrollo de una aplicación de escritorio en Python cuyo propósito es **convertir una imagen (por ejemplo, una hoja impresa con datos escritos a mano o una tabla en papel) en un archivo Excel estructurado**.  
La aplicación sigue principios de **Clean Code** y **Arquitectura Limpia**, priorizando claridad, mantenibilidad y extensibilidad.

## 🎯 Objetivo
El **objetivo final** es entregar una aplicación de escritorio estable, fácil de usar y multiplataforma que permita:  
1. Subir una foto con datos (tabla manuscrita, impresa o imagen similar).  
2. Reconocer los datos y su estructura.  
3. Exportar la información a un archivo Excel correctamente estructurado.  

La meta principal es **minimizar errores de reconocimiento y dar al usuario un Excel usable directamente**.

## 🛠️ Tecnologías utilizadas
- **Lenguaje**: Python 3.11+ (última versión estable).  
- **Librerías principales**:  
  - [`paddleocr`](https://github.com/PaddlePaddle/PaddleOCR) → OCR, detección de texto y tablas.  
  - [`opencv-python`](https://pypi.org/project/opencv-python/) → Procesamiento de imágenes.  
  - [`pytesseract`](https://pypi.org/project/pytesseract/) → OCR alternativo.  
  - [`openpyxl`](https://openpyxl.readthedocs.io/) → Generación de Excel.  
  - [`PyQt5`](https://pypi.org/project/PyQt5/) → GUI de escritorio.  
  - [`logging`](https://docs.python.org/3/library/logging.html) → Gestión de logs.  
  - [`pytest`](https://docs.pytest.org/) → Testing.  
- **Arquitectura**: Clean Architecture (capas: dominio, use_cases, adapters, UI).

## ⚙️ Instrucciones para Cursor
Cuando respondas a un prompt dentro de este proyecto:

1. **Concisión y foco**: responde de manera **concreta y escueta**, limitándote a la petición exacta.  
2. **No autonomía**: no refactorices ni cambies más cosas de las pedidas explícitamente.  
3. **Aviso previo**: si detectas que para cumplir un prompt es necesario tocar más partes del código, **avísame antes** y no lo ejecutes sin aprobación.  
4. **Integración limpia**: cualquier código nuevo debe seguir **PEP8**, incluir **docstrings** claros y encajar en la arquitectura existente.  
5. **No sobrecarga**: no añadas dependencias, patrones o cambios innecesarios.  
