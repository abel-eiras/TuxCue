# TuxCue — Architecture Document

**Version:** 1.2  
**Status:** Activo  
**Fuente:** Documento Maestro de Especificaciones  
**Fecha:** 2026-05-13  

---

## 1. Principios Arquitectónicos

Estos principios derivan directamente del Documento Maestro y son invariantes del proyecto:

1. **Patrón MVC con Qt**: La GUI se implementa mediante el patrón Modelo-Vista-Controlador usando los componentes nativos de Qt.
2. **Desacoplamiento estricto GUI / Audio**: El motor de audio y la interfaz gráfica están completamente separados. Se comunican exclusivamente a través del **patrón Observador (Signals/Slots de Qt)**.
3. **El audio no bloquea el hilo principal**: El procesamiento de audio no bloquea en ningún caso el hilo principal de la interfaz visual.
4. **Preparación para Fase 2**: La arquitectura de V1 soporta la futura línea de tiempo sin refactorizaciones mayores.

---

## 2. Vista General del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Proceso Principal Qt (hilo UI)                │
│                                                                     │
│  ┌─────────────────┐   Signals/Slots   ┌────────────────────────┐  │
│  │   src/gui        │ ◄───────────────► │   src/core             │  │
│  │                  │                   │                        │  │
│  │  MainWindow      │                   │  AudioController       │  │
│  │  TrackTableView  │                   │  (única fachada        │  │
│  │  TrackTableModel │                   │   hacia el audio)      │  │
│  │  ProxyModel      │                   │                        │  │
│  │  Delegates       │                   │  SessionManager        │  │
│  │  FilterBar       │                   │  Track (dataclass)     │  │
│  └─────────────────┘                   └──────────┬─────────────┘  │
│                                                    │                │
│                              Signals/Slots (QueuedConnection)       │
│                                                    │                │
│                                         ┌──────────▼─────────────┐ │
│                                         │   src/audio             │ │
│                                         │                         │ │
│                                         │   AudioEngine           │ │
│                                         │   (hilos de audio,      │ │
│                                         │   gestionados por       │ │
│                                         │   miniaudio)            │ │
│                                         └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Regla de oro**: `src/gui` nunca importa `src/audio`. `src/audio` nunca importa `src/gui`. Solo `src/core` puede importar de ambos lados, y lo hace a través de interfaces abstractas.

---

## 3. Estructura de Módulos

```
TuxCue/
├── main.py                         # Punto de entrada: crea QApplication y MainWindow
├── pyproject.toml
├── .cursorrules
│
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── track.py                # Dataclass Track (modelo de datos puro)
│   │   ├── session.py              # SessionManager: serializa/deserializa JSON
│   │   ├── audio_controller.py     # Fachada entre GUI y AudioEngine
│   │   └── interfaces.py           # Protocol IAudioEngine (permite mockear en tests)
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── engine.py               # AudioEngine: gestiona streams miniaudio
│   │   ├── stream.py               # TrackStream: encapsula un stream individual
│   │   └── probe.py                # probe_duration(): sondeo de duración sin QApp
│   │
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py          # QMainWindow: menú, toolbar, layout principal
│       ├── track_table_view.py     # QTableView con soporte drag & drop interno
│       ├── track_table_model.py    # QAbstractTableModel
│       ├── proxy_model.py          # QSortFilterProxyModel (filtros compuestos)
│       ├── delegates.py            # QStyledItemDelegate para botones y sliders
│       └── filter_bar.py           # Widget de barra de filtros (texto + segmentador)
│
├── tests/
│   ├── __init__.py
│   ├── test_session.py
│   ├── test_track_model.py
│   ├── test_proxy_model.py
│   └── test_audio_engine.py
│
└── docs/
    ├── 01_PRD.md
    ├── 02_ARCHITECTURE.md
    └── 03_TECH_STACK.md
```

---

## 4. Capa de Datos: `src/core/track.py`

### 4.1 Dataclass `Track`

El objeto `Track` es el modelo de datos canónico. Circula entre las tres capas (GUI, Core y Audio) como una estructura de datos pura, sin lógica de negocio ni referencias a Qt.

```
Track:
  id        : str    → UUID v4, inmutable, generado al crear el track
  name      : str    → Nombre editable por el usuario
  path      : Path   → Ruta absoluta al fichero de audio
  volume    : float  → Ganancia individual, rango [0.0 – 1.0], default 0.8
  loop      : bool   → Estado del toggle de bucle
  duration_s: float  → Calculado por AudioEngine al abrir el fichero (read-only desde GUI)
```

### 4.2 Invariantes del Modelo

- `id` se genera en la construcción y **nunca cambia**, ni al reordenar ni al editar nombre.
- `path` es siempre **absoluta**; `SessionManager` la resuelve en el guardado.
- `duration_s` es calculado por el `AudioEngine`; la GUI no lo calcula.
- `volume` está clampado al rango `[0.0, 1.0]`; valores fuera se rechazan.
- El estado `is_playing` **no forma parte del `Track`**: es responsabilidad del `AudioController`.

---

## 5. Modelo Qt: `src/gui/track_table_model.py`

### 5.1 `TrackTableModel(QAbstractTableModel)`

Implementa `QAbstractTableModel` según el patrón MVC de Qt. Es el **único dueño** de la lista ordenada de objetos `Track` en la capa GUI.

**Responsabilidades:**
- Mantener la lista ordenada de `Track`.
- Exponer datos a la vista (`data()`, `setData()`, `headerData()`).
- Emitir `dataChanged` cuando una propiedad cambia.
- Soportar drag & drop interno para reordenación.
- **No llama directamente al AudioEngine ni al AudioController.** Solo emite señales.

#### Columnas definidas como `IntEnum`:

```python
class Column(IntEnum):
    NAME     = 0
    DURATION = 1
    PLAY     = 2
    LOOP     = 3
    VOLUME   = 4
    SEEK     = 5   # Seek slider + progress indicator
```

#### Roles personalizados para los delegados:

```python
class TrackRole:
    PlayState   = Qt.UserRole + 1   # bool: ¿está reproduciendo?
    LoopState   = Qt.UserRole + 2   # bool
    Volume      = Qt.UserRole + 3   # float 0.0–1.0
    TrackId     = Qt.UserRole + 4   # str UUID
    DurationS   = Qt.UserRole + 5   # float segundos
    MissingFile = Qt.UserRole + 6   # bool: fichero no encontrado
    PauseState  = Qt.UserRole + 7   # bool: ¿está en pausa?
    SeekPos     = Qt.UserRole + 8   # float 0.0–1.0: posición de reproducción
```

### 5.2 Drag & Drop Interno

El modelo soporta reordenación interna mediante los métodos estándar de Qt:

- `flags()`: incluye `Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled` en cada fila.
- `supportedDragActions()` / `supportedDropActions()` → `Qt.MoveAction`.
- `mimeData()`: serializa las filas origen.
- `dropMimeData()`: reordena la lista interna usando `beginMoveRows`/`endMoveRows`.

El drag & drop externo (desde el SO) para añadir pistas se gestiona en `TrackTableView`, no en el modelo.

---

## 6. Proxy Model: `src/gui/proxy_model.py`

### 6.1 `TrackFilterProxyModel(QSortFilterProxyModel)`

Implementa los dos filtros de la UI sin alterar los datos del modelo base, según el Documento Maestro.

**Filtros acumulativos** (ambos deben pasar para que una fila sea visible):

1. **Filtro de texto**: `filterRegularExpression` con `Qt.CaseInsensitive`. Se actualiza en tiempo real al escribir en el buscador.
2. **Filtro de duración**: Lógica personalizada en `filterAcceptsRow()` que lee `TrackRole.DurationS`.

```
filterAcceptsRow(row, parent):
    return (
        QSortFilterProxyModel.filterAcceptsRow(self, row, parent)  # filtro texto
        AND self._duration_filter_passes(row, parent)               # filtro duración
    )
```

### 6.2 Segmentos de Duración

El segmentador de tiempo expone estos rangos (configurables desde la `FilterBar`):

```python
class DurationSegment(IntEnum):
    ALL       = 0   # Sin filtro
    UNDER_30S = 1   # duration_s < 30
    S30_TO_2M = 2   # 30 <= duration_s < 120
    M2_TO_5M  = 3   # 120 <= duration_s < 300
    OVER_5M   = 4   # duration_s >= 300
```

Alternativamente, la UI puede exponer inputs de rango libre (min/max en segundos) en lugar de segmentos fijos; la lógica de filtro es la misma.

---

## 7. Delegados: `src/gui/delegates.py`

El Documento Maestro especifica el uso de **`QStyledItemDelegate`** (o `setIndexWidget`) para los botones y sliders dentro de las celdas. La implementación preferida es mediante delegados puros (sin widgets persistentes) para máxima eficiencia con listas largas.

### 7.1 `PlayButtonDelegate(QStyledItemDelegate)`

- `paint()`: dibuja ▶ o ⏸ según `TrackRole.PlayState` / `TrackRole.PauseState`.
- `editorEvent()`: detecta `MouseButtonRelease` y emite `play_stop_requested(track_id: str)`.
- No crea widgets persistentes; el estado se actualiza via `dataChanged`.

### 7.2 `LoopButtonDelegate(QStyledItemDelegate)`

- Igual que `PlayButtonDelegate` pero para el estado de loop.
- Emite `loop_toggled(track_id: str)`.

### 7.3 `VolumeSliderDelegate(QStyledItemDelegate)`

- `paint()`: dibuja un slider horizontal con el valor de `TrackRole.Volume`.
- `editorEvent()`: intercepta `MouseButtonPress`/`MouseMove`; convierte la posición X del ratón en volumen [0,1] y escribe con `setData(index, volume, TrackRole.Volume)`.

### 7.4 `SeekSliderDelegate(QStyledItemDelegate)`

- `paint()`: dibuja un `QStyleOptionSlider` con el valor de `TrackRole.SeekPos` [0.0–1.0]. Cuando la pista no está reproduciendo, el slider se pinta deshabilitado (`State_Enabled` eliminado del state).
- `editorEvent()`: intercepta `MouseButtonPress`/`MouseMove`; calcula la fracción de posición a partir de la coordenada X y emite `seek_requested(track_id: str, fraction: float)` solo si la pista está activa.
- No crea widgets persistentes; el estado de posición se actualiza via `dataChanged` desde el `QTimer` de polling.

> **Nota sobre `setIndexWidget`**: Para filas con pocos elementos, `setIndexWidget` es válido como alternativa más simple. Para listas de más de ~100 pistas, los delegados `paint()`-based son significativamente más eficientes.

---

## 8. Controlador de Audio: `src/core/audio_controller.py`

### 8.1 `AudioController(QObject)`

Es la **única fachada** entre la capa GUI y el motor de audio. Toda comunicación entre ambas capas pasa por aquí mediante el **patrón Observador (Signals/Slots de Qt)**, tal como especifica el Documento Maestro.

```
GUI  ──llamadas──►  AudioController  ──llamadas directas──►  AudioEngine
GUI  ◄──signals──   AudioController  ◄──callbacks──           AudioEngine
```

#### API pública (llamada desde la GUI):

```
play(track_id, path, volume, loop)  → None
stop(track_id)                      → None
stop_all()                          → None
set_volume(track_id, volume)        → None
set_loop(track_id, loop)            → None
pause(track_id)                     → None    # Fase 2
resume(track_id)                    → None    # Fase 2
is_paused(track_id)                 → bool    # Fase 2
seek(track_id, fraction)            → None    # Fase 3 — fraction: [0.0, 1.0]
get_position(track_id)              → float   # Fase 3 — fracción de avance
is_playing(track_id)                → bool
```

#### Señales Qt emitidas hacia la GUI:

```python
track_started  = Signal(str)        # track_id: inicio de reproducción confirmado
track_stopped  = Signal(str)        # track_id: parada confirmada (Stop explícito)
playback_ended = Signal(str)        # track_id: fin natural (sin loop)
track_paused   = Signal(str)        # track_id: pausa activada
track_resumed  = Signal(str)        # track_id: reanudación tras pausa
track_error    = Signal(str, str)   # track_id, mensaje_de_error
```

### 8.2 Ciclo de estados del botón Play

El botón PLAY implementa un ciclo de tres estados:

```
[Detenido ▶]  →  play()   →  [Reproduciendo ⏸]
                                    │
                          pulsación → pause()
                                    ↓
                             [En pausa ▶ (sunken)]
                                    │
                          pulsación → resume()
                                    ↓
                             [Reproduciendo ⏸]
```

- `MainWindow._on_play_stop()` comprueba `is_playing()` e `is_paused()` para decidir qué acción ejecutar.
- El modelo `TrackTableModel` mantiene dos flags independientes: `_play_states` y `_pause_states`.

### 8.3 Flujo de Play (end-to-end)

```
[Usuario pulsa ▶ en la fila]
        │
        ▼
PlayButtonDelegate.editorEvent()
        │ emite: play_stop_requested(track_id)
        ▼
MainWindow._on_play_stop(track_id)
        │ llama a: AudioController.play(track_id, path, volume, loop)
        ▼
AudioEngine._open_stream(...)     ← hilo de audio de miniaudio
        │ stream abierto con éxito
        │ callback thread-safe vía Qt.QueuedConnection
        ▼
AudioController emite: track_started(track_id)
        │ conectado al hilo principal vía QueuedConnection
        ▼
TrackTableModel.set_play_state(track_id, playing=True)
        │ emite dataChanged(index)
        ▼
[Vista repinta la celda → botón cambia a ⏸]
```

### 8.4 Actualización de posición (Seek polling)

La posición de reproducción no se propaga mediante callbacks (evita overhead en el hilo de audio). En su lugar, `MainWindow` usa un `QTimer` a 100 ms:

```
QTimer(100ms) → _on_position_poll()
    para cada track_id activo:
        pos = AudioController.get_position(track_id)   # lee _frames_played/_total_frames
        TrackTableModel.set_seek_pos(track_id, pos)    # emite dataChanged(SeekPos)
        → SeekSliderDelegate.paint() repinta el slider
```

El seek iniciado por el usuario sigue el camino inverso: `SeekSliderDelegate.editorEvent()` → `seek_requested(track_id, fraction)` → `AudioController.seek()` → `TrackStream.seek()` (escribe `_seek_frame`). El generador de audio detecta `_seek_frame` en el siguiente ciclo y reabre `miniaudio.stream_file(seek_frame=N)`.

---

## 9. Motor de Audio: `src/audio/`

### 9.1 `AudioEngine` (`engine.py`)

- Instancia única en la aplicación (creada por `AudioController`).
- Mantiene un diccionario `{track_id: TrackStream}` de streams activos.
- Cada `TrackStream` encapsula un stream de miniaudio independiente.
- Los streams corren en **hilos propios gestionados por miniaudio** (API callback-based).
- `AudioEngine` **nunca llama a Qt directamente**. Notifica al `AudioController` vía callbacks registrados, que a su vez emiten señales Qt con `Qt.QueuedConnection`.

### 9.2 `TrackStream` (`stream.py`)

Encapsula por stream:

- El generador/iterator de frames de audio de miniaudio.
- El volumen actual, aplicado frame a frame.
- El estado de loop.
- Un método `stop()` thread-safe.
- **Pausa** (`pause()`/`resume()`): el generador detecta `_paused` y devuelve `array("h", [0]*len)` (silencio) sin avanzar `_frames_played`. La posición del decodificador se preserva porque `miniaudio.stream_file` no se avanza.
- **Seek** (`seek(fraction)`): escribe `_seek_frame = int(fraction * _total_frames)`. El generador detecta el valor en el siguiente ciclo, rompe el bucle interno y reabre `miniaudio.stream_file(seek_frame=_seek_frame)`.
- **Posición** (`position_fraction()`): devuelve `min(_frames_played / _total_frames, 1.0)`. `_total_frames` se obtiene via `miniaudio` al inicializar el stream.

### 9.3 Control de Volumen en Tiempo Real

El volumen se aplica **multiplicando las muestras en el callback de audio**, antes de enviarlas al dispositivo de salida. Esto permite cambios instantáneos sin reiniciar el stream, satisfaciendo RF-06 del PRD.

### 9.4 Aislamiento de Fallos

- Cada apertura de stream está envuelta en `try/except`.
- Un error en un stream no lanza excepciones al hilo principal.
- El error se notifica al `AudioController` via callback, que lo propaga a la GUI como señal `track_error`.

---

## 10. Gestión de Sesiones: `src/core/session.py`

### 10.1 `SessionManager`

Serializa y deserializa exactamente los cuatro campos definidos en el Documento Maestro:
ruta absoluta, orden, volumen y estado de loop.

```
save(tracks: list[Track], path: Path) → None
load(path: Path) → tuple[list[Track], list[str]]
    # Retorna (tracks_cargados, lista_de_errores_de_rutas_no_encontradas)
```

- Serializa con `json.dumps` estándar (sin dependencias externas).
- Valida la estructura mínima del JSON antes de procesar.
- Si `path` no existe: el `Track` se incluye con bandera de error; la GUI lo resalta visualmente.
- El campo `is_playing` **no se serializa nunca**: la sesión carga con todo detenido.

---

## 11. Patrón MVC en Qt — Resumen Visual

```
┌────────────┐  setData/signals  ┌──────────────────┐
│   View     │ ─────────────────►│     Model        │
│            │                   │                  │
│ TableView  │ ◄─────────────── │ TrackTableModel  │
│ Delegates  │   dataChanged     │ (lista de Track) │
│ FilterBar  │                   └────────┬─────────┘
└────────────┘                            │ no llama al audio
                                          │
                               ┌──────────▼──────────┐
                               │  AudioController    │  ← patrón Observador
                               │  (src/core)         │     vía Signals/Slots
                               └──────────┬──────────┘
                                          │ IAudioEngine (Protocol)
                               ┌──────────▼──────────┐
                               │  AudioEngine         │
                               │  (src/audio)         │
                               │  hilos de miniaudio  │
                               └─────────────────────┘
```

---

## 12. Preparación para Fase 2 (Línea de Tiempo)

Las siguientes decisiones de V1 facilitan la evolución sin reescrituras:

| Decisión en V1 | Beneficio en Fase 2 |
|---|---|
| `Track` con `id` UUID inmutable | La línea de tiempo referencia tracks por id, no por posición en la lista |
| `AudioController` como fachada | En Fase 2 se extiende con `seek()`, `schedule_at(t)` sin cambiar la GUI |
| `AudioEngine` independiente de Qt | Puede portarse a C++ o sustituirse por JACK sin tocar la GUI |
| `QAbstractTableModel` puro | En Fase 2 el mismo modelo de datos puede usarse en una vista de timeline |
| `SessionManager` con campo `version` | Permite migrations de formato entre V1 y V2 sin romper sesiones antiguas |
