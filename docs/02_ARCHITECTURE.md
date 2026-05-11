# StageCue — Architecture Document

**Version:** 1.0  
**Status:** Specification  
**Date:** 2026-05-11  

---

## 1. Principios Arquitectónicos

1. **Desacoplamiento total GUI / Audio**: `src/gui` no importa nada de `src/audio` directamente. Se comunican a través de interfaces definidas en `src/core`.
2. **El hilo principal de Qt es exclusivamente para la UI**: ninguna llamada de audio, I/O de disco lento o CPU intensiva ocurre en él.
3. **Spec-Driven Development**: toda modificación relevante actualiza primero los documentos en `docs/` antes de implementarse.
4. **Preparación para V2**: el motor de audio y el modelo de datos están diseñados para soportar una línea de tiempo sin refactorizaciones mayores.

---

## 2. Vista de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                        Proceso Principal Qt                     │
│                                                                 │
│  ┌──────────────┐   signals/slots   ┌──────────────────────┐   │
│  │  src/gui     │ ◄────────────────► │   src/core           │   │
│  │  (View +     │                   │   AudioController    │   │
│  │   Delegates) │                   │   SessionManager     │   │
│  └──────────────┘                   │   TrackModel (datos) │   │
│                                     └──────────┬───────────┘   │
│                                                │ llamadas       │
│                                                │ thread-safe    │
│                                     ┌──────────▼───────────┐   │
│                                     │   src/audio          │   │
│                                     │   AudioEngine        │   │
│                                     │   (hilos de audio)   │   │
│                                     └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Estructura de Módulos

```
TuxCue/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── track.py            # Dataclass Track (modelo de datos puro)
│   │   ├── session.py          # SessionManager: serializa/deserializa JSON
│   │   ├── audio_controller.py # Fachada entre GUI y AudioEngine
│   │   └── interfaces.py       # ABCs / Protocols que AudioEngine debe cumplir
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── engine.py           # AudioEngine: gestiona streams miniaudio
│   │   └── stream.py           # TrackStream: encapsula un stream individual
│   │
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py      # QMainWindow principal
│       ├── track_table_view.py # QTableView + drag&drop
│       ├── track_table_model.py# QAbstractTableModel
│       ├── proxy_model.py      # QSortFilterProxyModel con filtros compuestos
│       ├── delegates.py        # ItemDelegates para botones y sliders
│       ├── filter_bar.py       # Widget de barra de filtros (búsqueda + segmentador)
│       └── toolbar.py          # Toolbar global (Stop All, Master Volume)
│
├── tests/
│   ├── __init__.py
│   ├── test_session.py
│   ├── test_track_model.py
│   ├── test_proxy_model.py
│   └── test_audio_engine.py
│
├── docs/
│   ├── 01_PRD.md
│   ├── 02_ARCHITECTURE.md
│   └── 03_TECH_STACK.md
│
├── .cursorrules
├── pyproject.toml
└── main.py
```

---

## 4. Capa de Datos: `src/core/track.py`

### 4.1 Dataclass `Track`

```python
# Representación de referencia — no es código de producción todavía
@dataclass
class Track:
    id: str           # UUID v4, inmutable
    name: str         # Nombre editable por el usuario
    path: Path        # Ruta absoluta al fichero
    volume: float     # 0.0 – 1.0 (por defecto 0.8)
    loop: bool        # Estado de loop
    duration_s: float # Calculado al cargar, read-only desde la UI
```

### 4.2 Invariantes

- `id` se genera al crear el Track y nunca cambia, ni al reordenar ni al editar.
- `path` es siempre absoluta. El SessionManager la resuelve al guardar.
- `duration_s` es calculado por el AudioEngine al abrir el fichero por primera vez.
- `volume` está limitado al rango `[0.0, 1.0]`; valores fuera se clampean.

---

## 5. Modelo Qt: `src/gui/track_table_model.py`

### 5.1 `TrackTableModel(QAbstractTableModel)`

Responsabilidades:
- Mantiene una lista ordenada de objetos `Track`.
- Expone datos a la vista mediante `data()`, `setData()`, `headerData()`.
- Emite `dataChanged` cuando una propiedad de una pista cambia.
- Soporta `Qt.ItemIsDropEnabled` y `Qt.ItemIsDragEnabled` para reordenación interna.
- **No conoce ni llama directamente al AudioEngine.**

#### Roles personalizados:

```python
class TrackRole:
    PlayState  = Qt.UserRole + 1   # bool: ¿está sonando?
    LoopState  = Qt.UserRole + 2   # bool
    Volume     = Qt.UserRole + 3   # float 0.0–1.0
    TrackId    = Qt.UserRole + 4   # str UUID
    DurationS  = Qt.UserRole + 5   # float segundos
```

#### Columnas:

```python
class Column(IntEnum):
    NAME     = 0
    DURATION = 1
    PLAY     = 2
    LOOP     = 3
    VOLUME   = 4
```

### 5.2 Operaciones de Drag & Drop

- `supportedDragActions()` → `Qt.MoveAction`
- `supportedDropActions()` → `Qt.MoveAction`
- `mimeData()` serializa los índices de fila origen.
- `dropMimeData()` reordena la lista interna y emite `layoutChanged`.
- El origen y destino son siempre internos a la misma tabla.

---

## 6. Proxy Model: `src/gui/proxy_model.py`

### 6.1 `TrackFilterProxyModel(QSortFilterProxyModel)`

Combina dos filtros de forma acumulativa:

1. **Filtro de nombre**: `filterRegularExpression` con `setCaseSensitivity(Qt.CaseInsensitive)`.
2. **Filtro de duración**: lógica personalizada en `filterAcceptsRow()` que lee `TrackRole.DurationS`.

```
filterAcceptsRow(row, parent):
    track_passes_name_filter = QSortFilterProxyModel.filterAcceptsRow(self, row, parent)
    track_passes_duration_filter = self._duration_filter_passes(row, parent)
    return track_passes_name_filter AND track_passes_duration_filter
```

### 6.2 Segmentos de duración

```python
class DurationSegment(IntEnum):
    ALL       = 0
    UNDER_30S = 1   # duration_s < 30
    S30_TO_2M = 2   # 30 <= duration_s < 120
    M2_TO_5M  = 3   # 120 <= duration_s < 300
    OVER_5M   = 4   # duration_s >= 300
```

---

## 7. Delegados: `src/gui/delegates.py`

Los delegados permiten renderizar y gestionar la interacción con widgets complejos dentro de las celdas de la tabla sin necesidad de `QTableWidget` ni `setCellWidget`.

### 7.1 `PlayButtonDelegate(QStyledItemDelegate)`

- `paint()`: dibuja un botón ▶ o ■ según `TrackRole.PlayState`.
- `editorEvent()`: detecta `QEvent.MouseButtonRelease` dentro del rect del botón y emite una señal `play_stop_requested(track_id: str)`.
- Sin widget persistente: el estado visual se actualiza vía `dataChanged`.

### 7.2 `LoopButtonDelegate(QStyledItemDelegate)`

- Igual que `PlayButtonDelegate` pero para el estado de loop.
- Emite `loop_toggled(track_id: str)`.

### 7.3 `VolumeSliderDelegate(QStyledItemDelegate)`

- `paint()`: dibuja un slider horizontal con el valor de `TrackRole.Volume`.
- `createEditor()`: devuelve un `QSlider` real durante la edición activa.
- `setEditorData()` / `setModelData()`: sincroniza el valor entre el modelo y el editor.
- Emite cambios en tiempo real via `commitData` para que el AudioController los propague al stream.

---

## 8. Controlador de Audio: `src/core/audio_controller.py`

### 8.1 `AudioController`

Fachada que actúa como mediador entre la UI y el AudioEngine. Es el **único punto de entrada** al subsistema de audio desde la capa de presentación.

```
GUI  ──signals──►  AudioController  ──llamadas──►  AudioEngine (hilos propios)
GUI  ◄──signals──  AudioController  ◄──callbacks──  AudioEngine
```

#### API pública (desde la UI):

```python
def play(track_id: str) -> None
def stop(track_id: str) -> None
def stop_all() -> None
def set_volume(track_id: str, volume: float) -> None
def set_loop(track_id: str, loop: bool) -> None
def set_master_volume(volume: float) -> None
```

#### Señales emitidas hacia la UI (QObject signals):

```python
track_started    = Signal(str)          # track_id
track_stopped    = Signal(str)          # track_id
track_error      = Signal(str, str)     # track_id, error_message
playback_ended   = Signal(str)          # track_id (fin natural, sin loop)
```

### 8.2 Flujo de Play

```
Usuario pulsa ▶
    │
    ▼
PlayButtonDelegate.editorEvent()
    │ emite play_stop_requested(track_id)
    ▼
MainWindow slot → AudioController.play(track_id)
    │ thread-safe call
    ▼
AudioEngine._open_stream(track_id, path, volume, loop)  [hilo de audio]
    │ callback al terminar
    ▼
AudioController emite track_started(track_id)
    │ Qt.QueuedConnection → hilo principal
    ▼
TrackTableModel.set_play_state(track_id, playing=True)
    │ emite dataChanged
    ▼
Vista repinta el botón ■
```

---

## 9. Motor de Audio: `src/audio/engine.py`

### 9.1 `AudioEngine`

- Instancia única (singleton de aplicación).
- Internamente mantiene un `dict[str, TrackStream]` (track_id → stream activo).
- Cada `TrackStream` envuelve un `miniaudio.stream_file` o equivalente.
- Los streams se ejecutan en hilos gestionados por miniaudio (callback-based o thread-based según la API elegida).
- El `AudioEngine` **nunca llama a Qt** directamente; notifica al `AudioController` via callbacks thread-safe (p.ej. `QMetaObject.invokeMethod` con `Qt.QueuedConnection`).

### 9.2 `TrackStream` (`src/audio/stream.py`)

Encapsula:
- El generador/iterator de frames de audio.
- El volumen actual aplicado frame a frame.
- El estado de loop.
- Un método `stop()` que cierra el stream de forma segura desde cualquier hilo.

### 9.3 Aislamiento de Fallos

- Cada apertura de stream está envuelta en `try/except`.
- Un error en un stream no propaga excepciones al hilo principal.
- El `AudioController` recibe la notificación de error y la reenvía a la UI via señal.

---

## 10. Gestión de Sesiones: `src/core/session.py`

### 10.1 `SessionManager`

```python
def save(tracks: list[Track], path: Path) -> None
def load(path: Path) -> tuple[list[Track], list[str]]
    # retorna (tracks_cargadas, errores_de_rutas_no_encontradas)
```

- Serializa a JSON con `json.dumps` (sin dependencias externas).
- Al cargar, valida la estructura con un schema mínimo antes de procesar.
- Si `path` no existe: incluye el track con `duration_s=0` y una bandera de error; la UI lo resalta visualmente.
- El estado de reproducción (`is_playing`) **nunca se serializa**: las sesiones siempre cargan con todos los tracks detenidos.

---

## 11. Patrón de Comunicación General (MVC adaptado a Qt)

```
┌──────────┐   setData / signals    ┌──────────────────┐
│  View    │ ──────────────────────► │  Model           │
│ (QTable  │                         │ (TrackTable      │
│  View +  │ ◄────────────────────── │  Model)          │
│ Delegate)│   dataChanged signal    └────────┬─────────┘
└──────────┘                                  │ no audio calls
                                              │
                                   ┌──────────▼─────────┐
                                   │  AudioController   │
                                   │  (Core / Control.) │
                                   └──────────┬─────────┘
                                              │ IAudioEngine
                                   ┌──────────▼─────────┐
                                   │  AudioEngine       │
                                   │  (src/audio)       │
                                   └────────────────────┘
```

### Reglas estrictas del patrón:

- `src/gui` **no importa** `src/audio` — jamás.
- `src/audio` **no importa** `src/gui` — jamás.
- `src/core` es el único módulo que puede importar de ambos lados, y lo hace a través de la interfaz `IAudioEngine` (`src/core/interfaces.py`), lo que permite mockear el engine en tests.

---

## 12. Preparación para V2 (mini-DAW)

Las siguientes decisiones de diseño en V1 facilitan la evolución a V2 sin reescrituras:

| Decisión V1 | Beneficio en V2 |
|---|---|
| `Track` con `id` UUID inmutable | La línea de tiempo referencia tracks por id, no por posición |
| `AudioController` como fachada desacoplada | En V2, se extiende con métodos `seek()`, `schedule()` sin cambiar la GUI |
| `AudioEngine` independiente de Qt | Se puede portar a C++ o sustituir por JACK sin tocar la GUI |
| `QAbstractTableModel` puro (sin lógica de negocio) | En V2, el mismo modelo se puede usar en una vista de timeline |
| `SessionManager` con versión en el JSON | Permite migrations de formato entre V1 y V2 |
