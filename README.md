# I2E - Convertidor de Imagen a Excel v2.0

**Aplicación de escritorio profesional para convertir imágenes a Excel usando OCR avanzado**

## 🚀 Características Principales

- **OCR Inteligente**: Motor PaddleOCR optimizado con detección automática de idioma
- **Parser Avanzado**: Algoritmo inteligente de detección de tablas con métricas de calidad
- **Excel Profesional**: Exportación con formato profesional y estilos personalizables
- **Arquitectura Limpia**: Separación clara de responsabilidades y patrones SOLID
- **Logging Robusto**: Sistema de logging estructurado con rotación automática
- **Configuración Centralizada**: Gestión unificada de parámetros y entornos
- **Tests Completos**: Suite de tests unitarios y de integración
- **Manejo de Errores**: Sistema robusto de manejo de excepciones

## 🏗️ Arquitectura del Sistema

```
I2E/
├── main.py                 # Aplicación principal con UI PyQt5
├── config.py              # Configuración centralizada
├── core/                  # Modelos y interfaces del dominio
│   ├── models.py         # Modelos de datos (OCRResult, Table, etc.)
│   └── engine.py         # Interfaz abstracta para motores OCR
├── services/              # Lógica de negocio
│   ├── paddle_ocr.py     # Motor OCR con PaddleOCR
│   ├── parser.py         # Parser inteligente de tablas
│   └── exporter.py       # Exportador profesional a Excel
├── infrastructure/        # Utilidades de infraestructura
│   └── logging_config.py # Sistema de logging avanzado
└── test_app.py           # Suite completa de tests
```

## 🔧 Instalación

### Requisitos del Sistema

- **Python**: 3.11 o superior
- **Sistema Operativo**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Memoria RAM**: Mínimo 4GB, recomendado 8GB+
- **Espacio en Disco**: 2GB para la aplicación + espacio para logs

### Dependencias Principales

```bash
# Core dependencies
PyQt5>=5.15.0          # Interfaz gráfica
PaddleOCR>=2.6.0       # Motor OCR
opencv-python>=4.8.0   # Procesamiento de imágenes
Pillow>=9.0.0          # Manipulación de imágenes
numpy>=1.24.0          # Computación numérica
openpyxl>=3.1.0        # Exportación a Excel

# Development dependencies
black>=23.0.0           # Formateo de código
ruff>=0.1.0             # Linting y formateo
pytest>=7.0.0           # Framework de testing
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
# Instalar dependencias una por una
pip install PyQt5
pip install "paddlepaddle<2.5.0"
pip install "paddleocr>=2.6.0"
pip install opencv-python
pip install Pillow
pip install numpy
pip install openpyxl

# Dependencias de desarrollo
pip install black ruff pytest
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

La aplicación incluye un sistema de logging avanzado con:

- **Múltiples Handlers**: Consola, archivo, archivo de errores
- **Rotación Automática**: Evita archivos de log muy grandes
- **Niveles Configurables**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Formato Estructurado**: Timestamp, nivel, módulo, función, línea

### Configuración de Logging

```python
from infrastructure.logging_config import configure_logging

# Configuración básica
configure_logging(level=logging.INFO)

# Configuración avanzada
configure_logging(
    level=logging.DEBUG,
    log_to_file=True,
    log_to_console=True,
    log_dir="logs",
    max_file_size=50*1024*1024,  # 50MB
    backup_count=10
)
```

### Métricas de Rendimiento

```python
# Obtener estadísticas del motor OCR
ocr_engine = PaddleOCREngine()
stats = ocr_engine.get_performance_stats()
print(f"Tiempo promedio: {stats['avg_processing_time']:.2f}s")

# Métricas del parser
table, metrics = parser.parse_ocr_to_table(ocr_result)
print(f"Score de confianza: {metrics.confidence_score:.2f}")
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

### Logs de Debug

Para obtener información detallada de debug:

```python
# Configurar logging de debug
from infrastructure.logging_config import configure_development_logging
configure_development_logging()

# O habilitar debug mode
export I2E_DEBUG=true
```

## 🚀 Optimización y Rendimiento

### Configuración de GPU

```python
from services.paddle_ocr import OCRConfig

# Habilitar GPU para mejor rendimiento
gpu_config = OCRConfig(
    use_gpu=True,
    gpu_mem=1000,  # MB
    cpu_threads=20
)
```

### Optimización de Memoria

```python
# Configurar límites de memoria
config = AppConfig(
    memory_limit_mb=2048,  # 2GB
    max_worker_threads=4
)
```

### Procesamiento por Lotes

```python
# Configurar procesamiento por lotes
parser_config = ParsingConfig(
    max_columns=100,
    detect_table_structure=True
)
```

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
- Arquitectura limpia con separación de responsabilidades
- Sistema de logging avanzado con rotación automática
- Parser inteligente de tablas con métricas de calidad
- Exportador de Excel con formato profesional
- Configuración centralizada y personalizable
- Suite completa de tests unitarios y de integración

#### 🔧 Mejoras
- Mejor manejo de errores y validaciones
- Optimización de rendimiento del motor OCR
- Interfaz de usuario mejorada con barra de progreso
- Soporte para múltiples idiomas y configuraciones
- Gestión robusta de memoria y recursos

#### 🐛 Correcciones
- Corrección de problemas de memoria en procesamiento de imágenes grandes
- Mejora en la detección de separadores de columnas
- Corrección de errores en la exportación de Excel
- Mejora en el manejo de archivos de imagen corruptos

### v1.0.0 (2023-XX-XX)
- Versión inicial con funcionalidad básica de OCR y exportación

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

**I2E v2.0** - Transformando imágenes en datos estructurados con la potencia del OCR avanzado.
