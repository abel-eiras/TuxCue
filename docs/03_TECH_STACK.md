# TuxCue — Tech Stack & Dependencias

**Version:** 1.1  
**Status:** Activo  
**Fuente:** Documento Maestro de Especificaciones  
**Fecha:** 2026-05-11  

---

## 1. Stack Tecnológico (según Documento Maestro)

El Documento Maestro de TuxCue especifica explícitamente los siguientes componentes:

| Componente | Tecnología | Justificación del Documento Maestro |
|---|---|---|
| **Lenguaje** | Python 3 | Productividad, ecosistema maduro, multiplataforma |
| **GUI (Frontend)** | PySide6 (Qt) | Framework Qt oficial, patrón MVC nativo, componentes necesarios |
| **Audio (Backend)** | miniaudio | Polifonía nativa, control de ganancia por stream, sin bloqueos |
| **Patrón de comunicación** | Signals/Slots (Qt) | Desacoplamiento total GUI ↔ Audio, patrón Observador |

---

## 2. Lenguaje: Python 3.11+

- Versión mínima: **3.11** (`tomllib` en stdlib, `match` statements, mejor soporte de typing).
- El código usa type hints completos; mypy en modo estricto no debe reportar errores.

---

## 3. GUI Framework: PySide6

### ¿Por qué PySide6 y no PyQt6?

| Criterio | PySide6 | PyQt6 |
|---|---|---|
| Licencia | **LGPL v3** | GPL v3 / Comercial |
| Mantenedor | The Qt Company (oficial) | Riverbank Computing (tercero) |
| API | Idéntica a Qt6 C++ (referencia oficial) | Similar, con diferencias menores |
| Integración Qt Designer | Nativa (`pyside6-designer`) | Requiere conversión |

**Decisión**: PySide6 por licencia LGPL (distribución sin coste) y API oficial de Qt6.

### Componentes Qt utilizados en TuxCue

| Componente | Uso |
|---|---|
| `QMainWindow` | Ventana principal con menú y toolbar |
| `QTableView` | Vista principal del Cartwall |
| `QAbstractTableModel` | Modelo de datos de las pistas |
| `QSortFilterProxyModel` | Filtros de texto y duración sin alterar datos base |
| `QStyledItemDelegate` | Renderizado de botones Play/Loop y slider de volumen en celdas |
| `QSlider` | Editor de volumen dentro del delegado |
| `QLineEdit` | Barra de búsqueda |
| `QButtonGroup` / botones de radio | Segmentador de rangos de duración |
| `QFileDialog` | Apertura de ficheros de audio y sesiones |
| `QSettings` | Persistencia de preferencias de UI (tamaño de ventana, último directorio) |

---

## 4. Audio Backend: miniaudio

### Justificación

miniaudio es una librería de audio en C de cabecera única con bindings Python oficiales. Satisface exactamente los requisitos del Documento Maestro: **instanciación concurrente de flujos** y **control de ganancia por stream**.

| Requisito del Doc. Maestro | Cómo lo satisface miniaudio |
|---|---|
| Polifonía (N streams simultáneos) | Cada `stream_file` / `stream_with_callbacks` es independiente |
| Control de ganancia en tiempo real | Se aplica multiplicando las muestras en el callback de audio |
| Sin bloqueos en el hilo principal | API callback-based; los streams corren en hilos propios |
| Loop nativo | Parámetro `loop=True` en la apertura del stream |
| Formatos WAV, MP3, OGG, FLAC | Soportados vía dr_wav, dr_mp3, stb_vorbis, dr_flac embebidos |
| Sin dependencias del SO | Librería C embebida; acceso directo a ALSA/PulseAudio/PipeWire |

### Alternativas consideradas y descartadas

| Librería | Razón de descarte |
|---|---|
| `pygame.mixer` | No permite control de volumen en tiempo real sin reiniciar el canal; API limitada |
| `sounddevice` + `soundfile` | Boilerplate manual de threading; sin soporte MP3 nativo |
| `python-vlc` | Overhead de libvlc del sistema; API no diseñada para soundboards |
| `pyaudio` (PortAudio) | Problemas frecuentes con PulseAudio en Linux; mantenimiento irregular |
| GStreamer | Excesivo para V1; overhead de dependencias; curva de aprendizaje alta |
| `simpleaudio` | Solo WAV; sin control de volumen; sin loop nativo |

### Nota sobre servidores de audio en Linux

miniaudio detecta automáticamente ALSA, PulseAudio y PipeWire (vía el protocolo PulseAudio que PipeWire expone). No requiere configuración adicional en ninguno de los tres entornos.

---

## 5. Dependencias del Proyecto

### 5.1 Dependencias de producción

```toml
[project.dependencies]
PySide6 = ">=6.6"
miniaudio = ">=1.60"
```

### 5.2 Dependencias de desarrollo

```toml
[project.optional-dependencies.dev]
pytest = ">=8.0"
pytest-mock = ">=3.0"
pytest-qt = ">=4.0"    # Fixture QApplication para tests de modelos Qt
ruff = ">=0.4"
mypy = ">=1.0"
PySide6-stubs = "*"    # Type stubs para mypy
```

---

## 6. Herramientas de Desarrollo

### 6.1 uv — Gestión de entorno y dependencias

Resolución de dependencias 10–100x más rápida que pip, lockfiles reproducibles.

```bash
uv sync                        # Instalar todas las dependencias
uv add miniaudio               # Añadir dependencia
uv run python main.py          # Ejecutar la aplicación
uv run pytest                  # Ejecutar tests
```

### 6.2 ruff — Linting y formatting

Linter + formatter unificado en una sola herramienta.

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]
```

### 6.3 mypy — Type checking estático

```toml
[tool.mypy]
python_version = "3.11"
strict = true
```

### 6.4 pytest — Tests

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

| Fichero de test | Qué prueba |
|---|---|
| `test_session.py` | Serialización/deserialización JSON; tolerancia a rutas no encontradas |
| `test_track_model.py` | `QAbstractTableModel`: data(), setData(), drag & drop, roles |
| `test_proxy_model.py` | Filtros de texto y duración, combinación acumulativa |
| `test_audio_engine.py` | `AudioEngine` con mock de miniaudio; polifonía, stop, loop, volumen |

---

## 7. `pyproject.toml` de Referencia

```toml
[project]
name = "tuxcue"
version = "1.0.0"
description = "Cartwall / Soundboard para espectáculos teatrales — Fase 1"
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.6",
    "miniaudio>=1.60",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.0",
    "pytest-qt>=4.0",
    "ruff>=0.4",
    "mypy>=1.0",
    "PySide6-stubs",
]

[project.scripts]
tuxcue = "main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 8. Entorno de Ejecución Objetivo

| Componente | Requisito |
|---|---|
| Sistema operativo | Linux x86_64 (Ubuntu 22.04+, Fedora 38+, Arch Linux) |
| Python | 3.11 – 3.13 |
| Display server | X11 o Wayland (PySide6 soporta ambos nativamente) |
| Servidor de audio | ALSA, PulseAudio o PipeWire |
| RAM mínima | 256 MB para sesiones de hasta 100 pistas |
| Disco | Los ficheros de audio no se copian; se leen desde su ruta original |
