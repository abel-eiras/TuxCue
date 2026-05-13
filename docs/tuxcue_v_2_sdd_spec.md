# TuxCue v2 — Documentación técnica SDD

## 0. Propósito del documento

Este documento define una hoja de ruta técnica para evolucionar **TuxCue v1** hacia una hipotética **TuxCue v2** con una interfaz más profesional, modular y preparada para directo.

La filosofía es **SDD — Specification Driven Development**: antes de programar una funcionalidad, se define su comportamiento esperado, su modelo de datos, su impacto en arquitectura, sus criterios de aceptación y sus pruebas.

La idea no es reconstruir TuxCue desde cero, sino convertir la versión actual en una base estable sobre la que añadir capas de funcionalidad de forma progresiva.

---

## 1. Estado actual de TuxCue v1

### 1.1 Funcionalidad actual

TuxCue v1 es un reproductor de audio para regiduría y técnicos de sonido en producciones teatrales. Su objetivo es permitir lanzar pistas independientes, controlar volumen, usar loops, organizar cues según el guion y guardar sesiones.

Funciones actuales:

- Reproducción polifónica de múltiples pistas.
- Play / Stop independiente por pista.
- Loop por pista.
- Volumen individual modificable durante la reproducción.
- Cálculo automático de duración.
- Drag & drop externo de archivos de audio.
- Drag & drop interno para reordenar cues.
- Filtro por nombre.
- Filtro por duración.
- Sesiones `.tuxcue.json`.
- Nombre editable por pista.
- Marcado visual de archivos no encontrados.
- Configuración básica de idioma.
- Motor de audio desacoplado de Qt.
- Tests en modo offscreen.

### 1.2 Arquitectura actual

Estructura conceptual:

```text
TuxCue/
├── src/
│   ├── audio/      # Motor de audio miniaudio, sin Qt
│   ├── core/       # Track, sesiones, AudioController, interfaces
│   ├── gui/        # MainWindow, tabla, delegates, proxy model, filtros
│   ├── i18n/       # Traducciones
│   └── config.py   # Preferencias persistentes
├── tests/
├── docs/
├── main.py
└── install.sh
```

La decisión arquitectónica más importante de V1 es que `src/audio` no depende de Qt. Esto debe mantenerse en V2.

### 1.3 Restricciones que debe respetar V2

TuxCue no debe convertirse en una DAW completa. Debe seguir siendo una herramienta de directo:

- rápida;
- fiable;
- clara;
- controlable bajo presión;
- pensada para técnicos no necesariamente expertos;
- segura ante errores humanos durante una función.

---

## 2. Visión de producto para TuxCue v2

### 2.1 Frase de producto

**TuxCue v2 será una consola de cues de audio para teatro, con organización avanzada, disparo rápido, inspector de pista, fades, hotkeys, etiquetas, buses y monitorización básica, manteniendo la sencillez operativa de V1.**

### 2.2 Objetivos principales

1. Profesionalizar la interfaz sin perder claridad.
2. Separar mejor los conceptos de lista de cues, cartwall y edición de propiedades.
3. Añadir funciones críticas para directo: fades, hotkeys, panic stop y modo función.
4. Mejorar la preparación previa al espectáculo: tags, tipos de cue, notas, búsqueda avanzada.
5. Mejorar la confianza técnica: indicadores de estado, medidores, errores visibles y logs.
6. Preparar arquitectura para futuras funciones: buses, grupos, automatización y línea de tiempo.

### 2.3 No objetivos iniciales

Estas funciones no deberían entrar en la primera fase de V2:

- edición destructiva de audio;
- mezcla multipista avanzada tipo DAW;
- plugins VST/LV2;
- grabación;
- sincronización MIDI compleja;
- automatización de show completa desde el primer día;
- edición visual detallada de waveform como Audacity.

---

## 3. Principios de diseño de interfaz

### 3.1 Principios generales

- **Todo lo importante debe verse de un vistazo.**
- **Toda acción peligrosa debe tener un camino de emergencia.**
- **Durante una función, la interfaz debe reducir el riesgo de error.**
- **Los controles de edición no deben molestar al disparo de cues.**
- **Las pistas activas deben ser evidentes.**
- **Los errores deben ser visibles pero no bloquear innecesariamente.**

### 3.2 Distribución propuesta

La interfaz conceptual de V2 se dividirá en cinco zonas:

```text
┌────────────────────────────────────────────────────────────┐
│ Header / Toolbar / Panic Stop                              │
├──────────────┬──────────────────────────┬──────────────────┤
│ Sidebar      │ Cue List + Cartwall      │ Inspector        │
│ navegación   │ zona principal           │ propiedades      │
├──────────────┴──────────────────────────┴──────────────────┤
│ Bottom dock: master meter, playing cues, log, system status │
└────────────────────────────────────────────────────────────┘
```

### 3.3 Header superior

Debe contener:

- nombre de la aplicación;
- icono TuxCue;
- sesión activa;
- acciones principales:
  - Nueva sesión;
  - Abrir;
  - Guardar;
  - Añadir cue;
  - Exportar;
- botón **Panic Stop** muy visible;
- estado del motor de audio.

### 3.4 Sidebar izquierda

Debe servir para navegar y filtrar:

- sesión actual;
- All Cues;
- Music;
- FX;
- Voices;
- Loops;
- Missing Files;
- favoritos o cues destacados;
- tags;
- búsqueda.

### 3.5 Zona central

Debe tener dos modos principales:

1. **Cue List**: tabla detallada, ideal para preparación y edición.
2. **Cartwall**: botones grandes, ideal para directo.

En una primera V2, ambos pueden convivir en vertical:

- tabla arriba;
- cartwall debajo.

En una fase posterior, podrán convertirse en pestañas o layouts configurables.

### 3.6 Inspector derecho

Panel contextual para el cue seleccionado:

- nombre;
- archivo;
- waveform preview;
- play/stop;
- volumen;
- loop;
- fade in;
- fade out;
- hotkey;
- tipo;
- tags;
- notas;
- salida/bus.

### 3.7 Bottom dock

Debe mostrar información operativa:

- master output meter;
- cues actualmente reproduciéndose;
- log de eventos;
- estado del motor de audio;
- sample rate;
- buffer;
- uso de CPU aproximado;
- errores recientes.

---

## 4. Modelo de datos V2

### 4.1 Problema actual

Actualmente `Track` representa una pista de audio con campos mínimos. Para V2, el concepto debe evolucionar de `Track` a `Cue`, aunque se puede mantener `Track` temporalmente para no romper toda la app.

### 4.2 Entidad principal: Cue

Propuesta:

```python
@dataclass
class Cue:
    id: str
    number: str
    name: str
    path: Path
    type: CueType = CueType.MUSIC
    volume: float = 0.8
    loop: bool = False
    duration_s: float = 0.0
    missing_file: bool = False
    fade_in_s: float = 0.0
    fade_out_s: float = 0.0
    hotkey: str | None = None
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    color: str | None = None
    output_bus: str = "main"
    enabled: bool = True
    locked: bool = False
```

### 4.3 Tipos de cue

```python
class CueType(Enum):
    MUSIC = "music"
    FX = "fx"
    VOICE = "voice"
    LOOP = "loop"
    OTHER = "other"
```

### 4.4 Estado de reproducción

No debe guardarse directamente en `Cue`. Debe gestionarse aparte como estado runtime.

```python
@dataclass
class PlaybackState:
    cue_id: str
    status: PlaybackStatus
    started_at: float | None
    position_s: float
    effective_volume: float
    error: str | None = None
```

```python
class PlaybackStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    PLAYING = "playing"
    FADING_IN = "fading_in"
    FADING_OUT = "fading_out"
    LOOPING = "looping"
    ERROR = "error"
```

### 4.5 Sesión V2

```python
@dataclass
class Session:
    version: str
    name: str
    cues: list[Cue]
    tags: list[Tag]
    buses: list[Bus]
    preferences: SessionPreferences
    created_at: str
    updated_at: str
```

### 4.6 Compatibilidad con sesiones V1

La carga de sesiones debe ser migrable:

- Si `version == "1.0"`, convertir `Track` a `Cue`.
- Añadir valores por defecto para campos nuevos.
- Guardar ya en formato `2.0` solo cuando el usuario lo confirme o haga “Guardar como”.

### 4.7 Formato JSON propuesto

```json
{
  "version": "2.0",
  "name": "Midnight Theatre",
  "cues": [
    {
      "id": "uuid",
      "number": "001",
      "name": "Opening Theme",
      "path": "/home/user/show/audio/opening.wav",
      "path_relative": "audio/opening.wav",
      "type": "music",
      "volume": 0.7,
      "loop": false,
      "fade_in_s": 3.0,
      "fade_out_s": 3.0,
      "hotkey": "1",
      "tags": ["opening", "act-1"],
      "notes": "Fade up from black.",
      "output_bus": "main",
      "enabled": true,
      "locked": false
    }
  ],
  "buses": [
    {"id": "main", "name": "Main L/R", "volume": 1.0, "muted": false}
  ]
}
```

---

## 5. Arquitectura técnica propuesta

### 5.1 Objetivo arquitectónico

Mantener separación estricta:

```text
GUI Qt ───────> Core/Application ───────> Audio Engine
   │                    │                       │
   │                    │                       └── miniaudio / backend
   │                    └── session, models, commands
   └── views, delegates, widgets
```

La GUI no debe hablar directamente con `TrackStream`. El motor de audio no debe conocer Qt.

### 5.2 Capas

#### 5.2.1 `src/domain/`

Nueva capa opcional para entidades puras:

```text
src/domain/
├── cue.py
├── session.py
├── bus.py
├── tag.py
└── playback_state.py
```

#### 5.2.2 `src/core/`

Capa de aplicación:

```text
src/core/
├── audio_controller.py
├── session_service.py
├── cue_service.py
├── command_bus.py
├── migration.py
└── interfaces.py
```

#### 5.2.3 `src/audio/`

Motor de audio:

```text
src/audio/
├── engine.py
├── stream.py
├── fade.py
├── meter.py
├── probe.py
└── backend_miniaudio.py
```

#### 5.2.4 `src/gui/`

Interfaz:

```text
src/gui/
├── main_window.py
├── widgets/
│   ├── sidebar.py
│   ├── cue_table.py
│   ├── cartwall.py
│   ├── inspector.py
│   ├── bottom_dock.py
│   ├── waveform_widget.py
│   └── meter_widget.py
├── models/
│   ├── cue_table_model.py
│   ├── cue_filter_proxy.py
│   └── cartwall_model.py
└── delegates/
    ├── play_delegate.py
    ├── loop_delegate.py
    ├── volume_delegate.py
    └── tag_delegate.py
```

### 5.3 Migración gradual desde V1

No hace falta mover todo de golpe. Fases recomendadas:

1. Ampliar `Track` con campos nuevos mínimos.
2. Renombrar conceptualmente en UI: “track” → “cue”.
3. Introducir `Cue` como alias o evolución de `Track`.
4. Crear `SessionService` sin romper `session.py`.
5. Extraer widgets de `MainWindow`.
6. Sustituir tabla única por layout modular.

---

## 6. Especificación de funcionalidades V2

## 6.1 Panic Stop

### Descripción

Botón rojo global que detiene todo el audio de forma inmediata o con fade ultracorto configurable.

### Requisitos funcionales

- Debe estar siempre visible.
- Debe funcionar aunque haya un campo de texto enfocado.
- Debe tener atajo global dentro de la app, por ejemplo `Esc` o `Ctrl+Space`.
- Debe parar todos los streams activos.
- Debe actualizar el estado visual de todos los cues.
- Debe registrar evento en log.

### Requisitos técnicos

- `AudioEngine.stop_all()` debe ser seguro frente a deadlocks.
- `AudioController.stop_all()` debe emitir una señal global `all_stopped`.
- El modelo de tabla debe poder limpiar todos los estados de reproducción.

### Criterios de aceptación

- Dado que hay 3 cues sonando, al pulsar Panic Stop todos pasan a stopped en menos de 100 ms.
- La UI no se bloquea.
- El log muestra: `Panic stop triggered`.
- El botón funciona desde cualquier foco de la ventana.

### Tests

- Test unitario anti-deadlock de `AudioEngine.stop_all()`.
- Test de controller verificando emisión de `all_stopped`.
- Test GUI con `pytest-qt` simulando hotkey.

---

## 6.2 Fade In / Fade Out

### Descripción

Cada cue podrá tener fade in y fade out configurables en segundos.

### Requisitos funcionales

- Fade in al iniciar reproducción.
- Fade out al parar manualmente.
- Fade out opcional al final del archivo.
- Valores editables desde tabla e inspector.
- Valores guardados en sesión.

### Requisitos técnicos

El fade debe implementarse en el motor de audio, no en la GUI.

Propuesta:

```python
class FadeState:
    mode: FadeMode
    start_time: float
    duration_s: float
    start_volume: float
    target_volume: float
```

`TrackStream` debe calcular el volumen efectivo por bloque:

```text
effective_volume = cue_volume * fade_multiplier
```

### Criterios de aceptación

- Un cue con `fade_in_s = 3.0` llega al volumen final de forma progresiva en 3 segundos.
- Un cue con `fade_out_s = 2.0` no se corta bruscamente al pulsar stop.
- Si `fade_out_s = 0`, el stop es inmediato.
- El cambio de volumen manual durante fade no rompe la transición.

### Tests

- Tests puros de cálculo de curva de fade.
- Test de `TrackStream.set_volume()` durante fade.
- Test de stop con fade.

---

## 6.3 Hotkeys por cue

### Descripción

Cada cue podrá tener una tecla asignada para dispararse rápidamente.

### Requisitos funcionales

- Asignar hotkey desde inspector.
- Mostrar hotkey en tabla y cartwall.
- Detectar conflictos.
- Permitir limpiar hotkey.
- Guardar hotkeys en sesión.

### Requisitos técnicos

Crear un `HotkeyRegistry`:

```python
class HotkeyRegistry:
    def assign(self, cue_id: str, key_sequence: str) -> None: ...
    def remove(self, cue_id: str) -> None: ...
    def resolve(self, key_sequence: str) -> str | None: ...
```

La GUI captura eventos de teclado y consulta el registro.

### Criterios de aceptación

- Al pulsar `1`, se dispara el cue con hotkey `1`.
- Si otro cue ya usa `1`, la app muestra advertencia.
- En modo función, las hotkeys siguen activas aunque no esté seleccionada la tabla.

---

## 6.4 Tags y tipos de cue

### Descripción

Permitir organizar cues por etiquetas y tipo.

### Requisitos funcionales

- Tipos: Music, FX, Voice, Loop, Other.
- Tags libres: Act 1, Opening, Finale, etc.
- Filtro por tipo.
- Filtro por tag.
- Colores opcionales por tag.

### Requisitos técnicos

Añadir campos a `Cue`:

```python
type: CueType
tags: list[str]
```

Crear modelo de tags de sesión.

### Criterios de aceptación

- Un cue puede tener varios tags.
- Sidebar muestra tags usados y número de cues por tag.
- Filtrar por tag no modifica el orden real de la sesión.

---

## 6.5 Inspector de cue

### Descripción

Panel lateral para editar el cue seleccionado sin saturar la tabla.

### Campos iniciales

- Nombre.
- Archivo.
- Tipo.
- Volumen.
- Loop.
- Fade in.
- Fade out.
- Hotkey.
- Tags.
- Notas.
- Output bus.

### Requisitos funcionales

- El inspector refleja el cue seleccionado.
- Los cambios se aplican al modelo.
- Si el cue está sonando, cambios como volumen y loop se aplican en tiempo real.
- Los cambios editables deben marcar la sesión como “dirty”.

### Criterios de aceptación

- Al seleccionar una fila, el inspector se actualiza.
- Al cambiar volumen en inspector, cambia también en tabla.
- Al cambiar nombre, la tabla refleja el cambio.
- Si no hay cue seleccionado, el inspector muestra estado vacío.

---

## 6.6 Cartwall

### Descripción

Vista de botones grandes para disparo rápido de cues durante directo.

### Requisitos funcionales

- Mostrar cues filtrados o favoritos.
- Cada pad debe mostrar:
  - número/hotkey;
  - nombre;
  - tipo/icono;
  - duración;
  - estado;
  - progreso si está sonando.
- Click en pad: play/stop según modo.
- Colores por tipo/tag.

### Requisitos técnicos

Crear `CartwallWidget` independiente de la tabla.

```python
class CartwallWidget(QWidget):
    cue_triggered = Signal(str)
    cue_stop_requested = Signal(str)
```

### Criterios de aceptación

- El cartwall y la tabla comparten el mismo modelo de cues.
- Si un cue empieza desde la tabla, el pad se actualiza.
- Si un cue empieza desde el pad, la tabla se actualiza.

---

## 6.7 Waveform preview

### Descripción

Mostrar una miniatura de waveform en el inspector o en la tabla.

### Fase inicial

No es necesario crear un editor. Solo preview.

### Requisitos funcionales

- Calcular waveform al cargar archivo.
- Guardar caché por path + mtime + size.
- Mostrar waveform en inspector.
- Mostrar duración y posición aproximada si está sonando.

### Requisitos técnicos

```text
src/audio/waveform.py
src/cache/waveform_cache.py
src/gui/widgets/waveform_widget.py
```

### Criterios de aceptación

- Cargar 30 cues no bloquea la UI.
- La waveform puede generarse en background.
- Si falla el análisis, la app sigue funcionando.

---

## 6.8 Master output meter

### Descripción

Medidor visual básico del nivel de salida.

### Requisitos funcionales

- Mostrar nivel L/R o nivel mono aproximado.
- Actualizar varias veces por segundo.
- No afectar a la reproducción.
- Mostrar saturación/clipping si se detecta.

### Requisitos técnicos

El motor debe exponer RMS/peak agregado o por stream.

```python
@dataclass
class MeterFrame:
    left_peak: float
    right_peak: float
    left_rms: float
    right_rms: float
```

### Criterios de aceptación

- El meter responde cuando suena audio.
- El meter vuelve a cero al parar todo.
- No introduce cortes ni latencia audible.

---

## 6.9 Currently Playing panel

### Descripción

Panel inferior con cues activos.

### Requisitos funcionales

- Mostrar lista de cues sonando.
- Mostrar tiempo transcurrido.
- Mostrar barra de progreso.
- Permitir parar individualmente.
- Identificar loops.

### Criterios de aceptación

- Al iniciar un cue, aparece en el panel.
- Al terminar, desaparece o pasa a estado terminado brevemente.
- Si hay error, aparece mensaje asociado.

---

## 6.10 Log de eventos

### Descripción

Registro de acciones importantes durante la sesión.

### Eventos mínimos

- Sesión abierta.
- Sesión guardada.
- Cue iniciado.
- Cue detenido.
- Loop activado/desactivado.
- Panic stop.
- Archivo missing.
- Error de reproducción.

### Requisitos técnicos

Crear `EventLogService` simple en memoria.

```python
@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    cue_id: str | None = None
```

### Criterios de aceptación

- El log se actualiza sin bloquear.
- Se puede limpiar.
- Se puede exportar a `.txt` en una fase posterior.

---

## 6.11 Buses de salida

### Descripción

Agrupar cues por salida lógica: Main, Ambience, Voice, FX.

### Fase inicial

En V2.0 se puede implementar como bus lógico de volumen, aunque físicamente todo salga por Main L/R.

### Requisitos funcionales

- Cada cue tiene `output_bus`.
- Cada bus tiene volumen y mute.
- El volumen efectivo es:

```text
stream_volume = cue_volume * bus_volume * master_volume
```

### Criterios de aceptación

- Mutear bus FX silencia cues FX asignados.
- Cambiar volumen de bus afecta a cues en reproducción.
- La sesión guarda configuración de buses.

---

## 6.12 Modo función

### Descripción

Modo seguro para directo.

### Requisitos funcionales

Al activar modo función:

- se bloquea edición accidental;
- se bloquea drag & drop;
- se bloquea borrado de cues;
- se resaltan controles de directo;
- hotkeys y cartwall siguen activos;
- Panic Stop sigue activo.

### Criterios de aceptación

- En modo función no se puede cambiar nombre por doble clic.
- No se puede eliminar cue sin desbloquear.
- Se puede lanzar y parar audio con normalidad.

---

## 7. Plan de desarrollo por fases

## Fase 0 — Estabilización de V1

Objetivo: asegurar que la base no tiene fallos críticos antes de ampliar.

Tareas:

- Corregir `AudioEngine.stop_all()` para evitar deadlocks.
- Añadir test anti-deadlock.
- Parar audio activo antes de nueva sesión o abrir sesión.
- Evitar `probe_duration()` en archivos missing.
- Revisar `install.sh` para no ocultar errores graves.
- Crear release `v1.0.1`.

Resultado esperado:

- V1 estable.
- Base segura para V2.

---

## Fase 1 — Preparar modelo de datos V2

Objetivo: ampliar datos sin cambiar radicalmente la UI.

Tareas:

- Añadir campos a `Track` o crear `Cue`.
- Añadir `fade_in_s`, `fade_out_s`, `hotkey`, `type`, `tags`, `notes`.
- Actualizar session save/load.
- Añadir migración V1 → V2.
- Añadir tests de sesión.

Resultado esperado:

- El programa puede guardar/cargar sesiones con campos nuevos.
- La UI aún puede ser parecida a V1.

---

## Fase 2 — Fades y Panic Stop

Objetivo: mejorar seguridad y suavidad en directo.

Tareas:

- Implementar fade engine.
- Añadir fade in/out a `TrackStream`.
- Añadir botón Panic Stop.
- Añadir shortcut de Panic Stop.
- Añadir señales globales de parada.
- Añadir tests de audio.

Resultado esperado:

- Paradas suaves.
- Parada de emergencia fiable.

---

## Fase 3 — Inspector básico

Objetivo: separar edición de la tabla.

Tareas:

- Crear `CueInspectorWidget`.
- Conectar selección de tabla con inspector.
- Editar nombre, volumen, loop, fade, notas.
- Sincronizar cambios tabla ↔ inspector.

Resultado esperado:

- La tabla puede simplificarse.
- La edición avanzada vive en el inspector.

---

## Fase 4 — Tags, tipos y filtros avanzados

Objetivo: organizar sesiones grandes.

Tareas:

- Añadir tipos visuales.
- Añadir tags.
- Crear sidebar de navegación.
- Añadir filtros por tipo/tag/status.
- Añadir contador por categoría.

Resultado esperado:

- Sesiones de 50–100 cues siguen siendo manejables.

---

## Fase 5 — Cartwall

Objetivo: crear modo de disparo rápido.

Tareas:

- Crear `CartwallWidget`.
- Crear pads configurables.
- Sincronizar con modelo principal.
- Añadir hotkeys visibles.
- Añadir estado visual de reproducción.

Resultado esperado:

- El usuario puede usar TuxCue como lanzador de pads durante función.

---

## Fase 6 — Waveform y bottom dock

Objetivo: mejorar feedback visual.

Tareas:

- Crear waveform preview.
- Crear caché de waveform.
- Crear panel Currently Playing.
- Crear Event Log.
- Crear Master Meter básico.

Resultado esperado:

- La app comunica mejor qué está pasando.

---

## Fase 7 — Buses y modo función

Objetivo: profesionalizar operación en directo.

Tareas:

- Añadir buses lógicos.
- Añadir volumen por bus.
- Añadir mute por bus.
- Añadir modo función.
- Bloquear edición accidental.

Resultado esperado:

- TuxCue v2 ya se comporta como herramienta de directo madura.

---

## 8. Propuesta de issues GitHub

### Epic 1 — Stabilize V1

- Fix deadlock in `AudioEngine.stop_all()`.
- Add stop_all anti-deadlock test.
- Stop active audio before clearing/loading sessions.
- Skip duration probing for missing files.
- Improve install.sh error handling.

### Epic 2 — Cue Data Model V2

- Add Cue dataclass.
- Add CueType enum.
- Add fade fields.
- Add hotkey field.
- Add tags and notes.
- Implement session migration V1 to V2.

### Epic 3 — Playback Improvements

- Implement fade calculation.
- Add fade in on play.
- Add fade out on stop.
- Add immediate stop option.
- Add panic stop.

### Epic 4 — New UI Shell

- Create app shell with header/sidebar/main/inspector/bottom dock.
- Extract current table into CueTableWidget.
- Add toolbar actions.
- Add persistent layout settings.

### Epic 5 — Inspector

- Create CueInspectorWidget.
- Add waveform placeholder.
- Add editable cue fields.
- Sync inspector and model.

### Epic 6 — Organization

- Add cue types.
- Add tags.
- Add sidebar filters.
- Add missing files view.

### Epic 7 — Cartwall

- Create CartwallWidget.
- Create CuePadWidget.
- Add play/stop behavior.
- Add visual playing state.
- Add progress indicator.

### Epic 8 — Monitoring

- Add currently playing panel.
- Add event log.
- Add master meter.
- Add system status panel.

### Epic 9 — Live Mode

- Add show mode toggle.
- Disable editing in show mode.
- Keep playback controls enabled.
- Add visual indicator.

---

## 9. Testing strategy

### 9.1 Unit tests

Prioridad:

- modelos de datos;
- migraciones;
- sesiones;
- fades;
- hotkey registry;
- bus volume calculation;
- audio engine state.

### 9.2 Integration tests

- cargar sesión V1 y guardar como V2;
- iniciar cue desde tabla y verlo en cartwall;
- iniciar cue desde cartwall y verlo en tabla;
- cambiar volumen en inspector y aplicar al motor;
- activar Panic Stop con varios cues sonando.

### 9.3 GUI tests

Con `pytest-qt`:

- selección de cue actualiza inspector;
- filtros actualizan tabla;
- modo función bloquea edición;
- hotkeys lanzan cues;
- botones principales emiten señales correctas.

### 9.4 Manual QA para directo

Checklist antes de una release:

- abrir sesión con 50 cues;
- reproducir 5 cues simultáneos;
- cambiar volumen en directo;
- activar y desactivar loops;
- lanzar hotkeys rápidamente;
- usar Panic Stop;
- abrir sesión con archivos perdidos;
- cambiar de idioma;
- guardar y recargar sesión;
- probar con WAV, MP3, FLAC y OGG.

---

## 10. Riesgos técnicos

### 10.1 Complejidad de UI

Riesgo: intentar construir toda la interfaz v2 de golpe.

Mitigación:

- extraer widgets por fases;
- mantener tabla actual funcionando;
- crear layout nuevo detrás de una bandera experimental.

### 10.2 Audio en tiempo real

Riesgo: fades, meters y waveform pueden introducir carga.

Mitigación:

- mantener audio engine simple;
- waveform en background;
- meter con datos agregados ligeros;
- no hacer trabajo pesado en callbacks de audio.

### 10.3 Formato de sesión

Riesgo: romper sesiones V1.

Mitigación:

- migración explícita;
- tests con fixtures V1;
- guardar backups automáticos al convertir.

### 10.4 Sobrecargar TuxCue

Riesgo: convertirlo en una DAW.

Mitigación:

- cada feature debe responder a una necesidad de directo;
- rechazar edición avanzada de audio;
- mantener flujo principal: cargar, ordenar, disparar, parar.

---

## 11. Definition of Done para TuxCue v2.0

TuxCue v2.0 se puede considerar listo cuando:

- carga sesiones V1 y V2;
- permite crear sesiones nuevas;
- reproduce cues con loop, volumen y fades;
- tiene Panic Stop seguro;
- tiene tabla de cues con tipos, tags, hotkeys y estados;
- tiene cartwall operativo;
- tiene inspector funcional;
- guarda y carga todos los campos nuevos;
- muestra cues actualmente sonando;
- tiene log de eventos;
- tiene tests automatizados para core, audio y GUI;
- no se bloquea con varios cues simultáneos;
- la interfaz permite modo preparación y modo función.

---

## 12. Primer sprint recomendado

Duración sugerida: 1–2 semanas.

Objetivo: preparar una `v1.1-alpha` con cimientos de V2, pero sin rediseño completo.

Tareas:

1. Corregir `stop_all()`.
2. Añadir test anti-deadlock.
3. Añadir campos `fade_in_s`, `fade_out_s`, `hotkey`, `notes` al modelo.
4. Actualizar sesiones para guardar estos campos.
5. Añadir columnas opcionales Fade In / Fade Out / Hotkey.
6. Implementar fade out básico al parar.
7. Añadir botón Panic Stop en toolbar.
8. Añadir log interno simple por consola o panel básico.

Resultado:

- TuxCue sigue pareciéndose a V1.
- Pero ya empieza a tener el corazón de V2.

---

## 13. Decisión recomendada

No empezaría por rediseñar toda la ventana.

Empezaría por este orden:

1. **Seguridad del audio**: stop_all, panic stop, fade out.
2. **Modelo de datos V2**: cue, tags, hotkeys, notes.
3. **Inspector**: porque descarga complejidad de la tabla.
4. **Cartwall**: cuando el modelo ya esté preparado.
5. **Bottom dock y meters**: cuando el flujo principal esté estable.
6. **Buses y modo función**: como cierre profesional de V2.

La maqueta visual es una buena brújula, pero no debe convertirse en el primer objetivo técnico. El primer objetivo técnico debe ser que TuxCue siga siendo fiable aunque crezca.

