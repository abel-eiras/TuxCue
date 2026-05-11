# StageCue — Tech Stack & Dependencies

**Version:** 1.0  
**Status:** Specification  
**Date:** 2026-05-11  

---

## 1. Resumen de Dependencias

| Categoría | Librería / Tool | Versión mínima | Justificación |
|---|---|---|---|
| Lenguaje | Python | 3.11 | `tomllib` stdlib, `match` statements, mejor typing |
| GUI Framework | PySide6 | 6.6 | Qt6 oficial, LGPL, mejor soporte Wayland/X11 |
| Audio Backend | miniaudio | 1.60 | Ver sección 3 |
| Empaquetado | pyproject.toml (PEP 517) | — | Estándar moderno sin setup.py |
| Build/Venv | uv | 0.4+ | Resolución de deps ultrarrápida, lockfiles |
| Tests | pytest | 8.x | Ecosystem maduro, fixtures, parametrize |
| Mocking Audio | pytest-mock | 3.x | Para mockear `AudioEngine` en tests de UI |
| Linting | ruff | 0.4+ | Linter + formatter unificado, veloz |
| Type checking | mypy | 1.x | Verificación estática; configurado en modo estricto |

---

## 2. GUI Framework: PySide6

### ¿Por qué PySide6 y no PyQt6?

| Criterio | PySide6 | PyQt6 |
|---|---|---|
| Licencia | LGPL v3 | GPL v3 / comercial |
| Mantenedor | The Qt Company (oficial) | Riverbank Computing (tercero) |
| API | Idéntica a Qt6 C++ | Muy similar pero con diferencias de naming |
| Integración con Qt Designer | Nativa (`pyside6-designer`) | Requiere conversión |
| Señales tipadas | `Signal(type)` estándar | Igual |

**Decisión**: PySide6 porque la licencia LGPL permite distribución sin coste y la API es la referencia oficial de Qt6.

### Componentes Qt utilizados

| Componente Qt | Uso en StageCue |
|---|---|
| `QMainWindow` | Ventana principal con menú, toolbar y statusbar |
| `QTableView` | Vista de la tabla principal (Cartwall) |
| `QAbstractTableModel` | Modelo de datos de las pistas |
| `QSortFilterProxyModel` | Filtrado en tiempo real por nombre y duración |
| `QStyledItemDelegate` | Renderizado de botones Play/Loop y slider de volumen |
| `QSlider` | Editor de volumen dentro del delegado |
| `QToolBar` | Controles globales (Stop All, Master Volume) |
| `QLineEdit` | Barra de búsqueda |
| `QButtonGroup` | Segmentador de duración (radio buttons) |
| `QFileDialog` | Apertura de ficheros de audio y sesiones |
| `QThread` / `QRunnable` | Si se necesita trabajo auxiliar en background (cálculo de duración) |
| `QSettings` | Persistencia de preferencias de UI (tamaño de ventana, último directorio) |

---

## 3. Audio Backend: miniaudio

### ¿Por qué miniaudio?

miniaudio es una librería de audio en C de cabecera única con bindings Python oficiales (`pip install miniaudio`).

| Requisito | Solución en miniaudio |
|---|---|
| Polifonía (N streams simultáneos) | Cada `stream_file` es independiente; se gestionan N en paralelo |
| Control de volumen en tiempo real | Se aplica en el callback de audio frame a frame, sin reiniciar el stream |
| Baja latencia | Buffer configurable; acceso directo a ALSA/PulseAudio/PipeWire |
| Loop nativo | Parámetro `loop=True` en `stream_with_callbacks` |
| Sin dependencias del sistema | Librería C embebida, no requiere instalar librerías del SO |
| Formatos: WAV, MP3, OGG, FLAC | Soportados nativamente vía dr_wav, dr_mp3, stb_vorbis, dr_flac |
| API no bloqueante | `stream_with_callbacks` corre en hilo de audio propio |

### Alternativas consideradas y descartadas

| Librería | Razón de descarte |
|---|---|
| `pygame.mixer` | No permite control de volumen en tiempo real sin reiniciar el canal; API limitada |
| `sounddevice` + `soundfile` | Requiere gestión manual del threading; más boilerplate; no soporta MP3 nativo |
| `python-vlc` | Overhead enorme; dependencia de libvlc del sistema; API no pensada para soundboards |
| `pyaudio` (PortAudio) | API callback compleja; problemas frecuentes en Linux con PulseAudio; mantenimiento irregular |
| GStreamer | Potente pero excesivo para V1; overhead de dependencias; curva de aprendizaje elevada |
| `simpleaudio` | Solo WAV; sin control de volumen; sin loop nativo |

### Nota sobre PipeWire

miniaudio detecta automáticamente si el sistema usa PulseAudio o PipeWire (via el protocolo PulseAudio que PipeWire expone) y funciona de forma transparente en ambos entornos. No se requiere configuración adicional.

---

## 4. Herramientas de Desarrollo

### 4.1 uv (gestión de entorno y dependencias)

```bash
# Instalar dependencias del proyecto
uv sync

# Añadir una nueva dependencia
uv add miniaudio

# Ejecutar la aplicación
uv run python main.py

# Ejecutar tests
uv run pytest
```

**¿Por qué uv?** Resolución de dependencias 10-100x más rápida que pip, lockfiles reproducibles (`uv.lock`), manejo de virtualenvs integrado.

### 4.2 ruff (linting + formatting)

Configuración objetivo en `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]
```

### 4.3 mypy (type checking)

```toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = false
```

Los módulos de PySide6 tienen stubs (`PySide6-stubs`); se incluyen como dependencia de desarrollo.

### 4.4 pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

Estrategia de tests:

- `tests/test_session.py`: pruebas de serialización/deserialización JSON.
- `tests/test_track_model.py`: pruebas del `QAbstractTableModel` (requiere `QApplication` fixture).
- `tests/test_proxy_model.py`: pruebas de los filtros combinados.
- `tests/test_audio_engine.py`: pruebas del `AudioEngine` con mock de miniaudio.

---

## 5. `pyproject.toml` de Referencia

```toml
[project]
name = "stagecue"
version = "1.0.0"
description = "Cartwall / Soundboard para espectáculos teatrales"
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
stagecue = "main:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 6. Entorno de Ejecución Objetivo

| Componente | Requisito |
|---|---|
| SO | Linux x86_64 (Ubuntu 22.04+, Fedora 38+, Arch) |
| Python | 3.11 – 3.13 |
| Display server | X11 o Wayland (PySide6 soporta ambos) |
| Audio server | ALSA, PulseAudio, o PipeWire |
| RAM mínima | 256 MB (para sesiones de hasta 100 pistas cargadas en memoria) |
| CPU | Cualquier CPU moderna; el decode de audio es ligero |
| Disco | Los ficheros de audio no se copian; se leen desde su ubicación original |
