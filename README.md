# I2E - Convertidor de Imagen a Excel v2.0

**Aplicación de escritorio profesional para convertir imágenes a Excel usando OCR**

## 🚀 Características Principales

- **OCR**: Extracción de texto desde imágenes con PaddleOCR
- **Parser básico**: Conversión simple de líneas a filas de tabla
- **Exportación a Excel**: Generación de archivos .xlsx con openpyxl
- **UI PyQt5**: Interfaz de escritorio sencilla para seleccionar imagen y destino
- **Logging simple**: Mensajes informativos en consola/archivo

## 🏗️ Arquitectura del Sistema

```
I2E/
├── main.py               # Aplicación principal con UI (PyQt5)
├── config.py             # Configuración básica de la app
├── core/
│   ├── models.py         # Modelos de dominio (OCRResult, Table, etc.)
│   └── engine.py         # Interfaz simple para motores OCR
├── services/
│   ├── paddle_ocr.py     # Integración con PaddleOCR
│   ├── parser.py         # Parser básico de líneas a tabla
│   └── exporter.py       # Exportación a Excel con openpyxl
├── infrastructure/
│   └── logging_config.py # Configuración de logging simple
└── test_app.py           # Tests puntuales (si se usan)
```

## Estado actual / Roadmap breve

- ✅ Limpieza de repositorio y dependencias básicas completada
- 🔜 Refactor a puertos y casos de uso (use-cases) para aislar la lógica
- 🔜 Test de integración imagen → xlsx cubriendo el flujo completo

## 🔧 Instalación

### Requisitos del Sistema

- **Python**: 3.11 o superior
- **Sistema Operativo**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Memoria RAM**: Mínimo 4GB, recomendado 8GB+
- **Espacio en Disco**: 2GB para la aplicación + espacio para logs

### Dependencias Principales

```bash
# Coinciden exactamente con requirements.txt
imgaug==0.4.0
numpy==1.26.4
opencv-contrib-python==4.6.0.66
opencv-python==4.6.0.66
paddleocr==2.7.3
pillow==10.4.0
protobuf==3.20.2
pytesseract==0.3.13
```

### Instalación Automática

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/I2E.git
cd I2E

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python main.py
```

### Instalación Manual

```bash
# Instalar exactamente los mismos paquetes/versions que requirements.txt
pip install imgaug==0.4.0
pip install numpy==1.26.4
pip install opencv-contrib-python==4.6.0.66
pip install opencv-python==4.6.0.66
pip install paddleocr==2.7.3
pip install pillow==10.4.0
pip install protobuf==3.20.2
pip install pytesseract==0.3.13
```

## 🎯 Uso de la Aplicación

### Interfaz Principal

1. **Seleccionar Imagen**: Haz clic en "Seleccionar Imagen" para elegir el archivo
2. **Seleccionar Directorio**: Elige dónde guardar el archivo Excel resultante
3. **Convertir**: Haz clic en "Convertir a Excel" para iniciar el proceso
4. **Progreso**: La barra de progreso muestra el estado del procesamiento
5. **Resultado**: El archivo Excel se genera con formato profesional

### Formatos Soportados

- **Imágenes**: PNG, JPG, JPEG, BMP, TIFF, GIF
- **Salida**: Excel (.xlsx) con formato profesional
- **Idiomas OCR**: Español (por defecto), Inglés, Francés, Alemán, etc.

### Configuración Avanzada

La aplicación se puede configurar mediante:

- **Archivo de configuración**: `config.py`
- **Variables de entorno**: `I2E_LOG_LEVEL`, `I2E_OCR_LANGUAGE`, etc.
- **Interfaz de usuario**: Ajustes en tiempo de ejecución

## ⚙️ Configuración

### Configuración por Entorno

```python
from config import get_config

# Desarrollo (logging detallado, métricas de rendimiento)
config = get_config("development")

# Producción (logging mínimo, optimizado para rendimiento)
config = get_config("production")

# Testing (sin logging, configuración mínima)
config = get_config("test")
```

### Variables de Entorno

```bash
# Logging
export I2E_LOG_LEVEL=DEBUG
export I2E_LOG_TO_FILE=true
export I2E_LOG_TO_CONSOLE=true

# OCR
export I2E_OCR_LANGUAGE=en
export I2E_OCR_USE_GPU=true
export I2E_OCR_MIN_CONFIDENCE=0.7

# Debug
export I2E_DEBUG=true
```

### Configuración Personalizada

```python
from config import AppConfig

# Crear configuración personalizada
custom_config = AppConfig(
    ocr_language="en",
    ocr_use_gpu=True,
    excel_header_bg_color="FF0000",  # Rojo
    parser_max_columns=50
)
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Ejecutar todos los tests
python test_app.py

# Ejecutar tests específicos
python -m pytest test_app.py::TestAppConfig -v

# Ejecutar con cobertura
python -m pytest test_app.py --cov=. --cov-report=html
```

### Tipos de Tests

- **Unit Tests**: Tests individuales para cada componente
- **Integration Tests**: Tests de flujo completo
- **Error Handling Tests**: Verificación de manejo de errores
- **Configuration Tests**: Validación de configuraciones

## 📊 Monitoreo y Logging

### Sistema de Logging

La aplicación incluye un sistema de logging con:

- **Consola y archivo** (configurable)
- **Niveles**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Configuración de Logging

```python
from infrastructure.logging_config import configure_logging

# Configuración básica
configure_logging(level=logging.INFO)
```

## 🔍 Troubleshooting

### Problemas Comunes

#### Error de PaddleOCR
```
Error: PaddleOCR failed to initialize
```
**Solución**: Verificar que PaddleOCR esté instalado correctamente y que haya suficiente memoria RAM.

#### Error de Memoria
```
Error: Out of memory during OCR processing
```
**Solución**: Reducir el tamaño de imagen o aumentar la memoria disponible.

#### Error de Formato de Imagen
```
Error: Unsupported image format
```
**Solución**: Convertir la imagen a un formato soportado (PNG, JPG, etc.).

## 🤝 Contribución

### Guías de Desarrollo

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Estándares de Código

- **Formateo**: Usar Black para formateo automático
- **Linting**: Usar Ruff para verificación de código
- **Tests**: Mantener cobertura de tests >90%
- **Documentación**: Docstrings estilo Google/NumPy
- **Type Hints**: Usar type hints en todas las funciones

### Estructura de Commits

```
feat: añadir nueva funcionalidad de exportación
fix: corregir error en parser de tablas
docs: actualizar documentación de API
test: añadir tests para nuevo módulo
refactor: mejorar rendimiento del motor OCR
```

## 📝 Changelog

### v2.0.0 (2024-01-XX)

#### ✨ Nuevas Características
- Parser básico de tablas
- Exportación a Excel
- UI en PyQt5
- Logging simple

#### 🔧 Mejoras
- Mejor manejo de errores y validaciones
- Interfaz de usuario con barra de progreso

#### 🐛 Correcciones
- Correcciones y estabilización de dependencias

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial* - [tu-usuario](https://github.com/tu-usuario)

## 🙏 Agradecimientos

- **PaddleOCR** por el motor de OCR de alta calidad
- **PyQt5** por el framework de interfaz gráfica
- **openpyxl** por la funcionalidad de exportación a Excel
- **Comunidad Python** por las librerías y herramientas utilizadas

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/I2E/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/tu-usuario/I2E/discussions)
- **Email**: tu-email@ejemplo.com

---

**I2E v2.0** - Transformando imágenes en datos estructurados con la potencia del OCR.
