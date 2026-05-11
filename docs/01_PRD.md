# StageCue — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Specification  
**Date:** 2026-05-11  

---

## 1. Visión General

StageCue es una aplicación de escritorio para Linux orientada a técnicos de sonido y directores de escena que necesitan disparar efectos de sonido, músicas de ambiente y cues de audio durante espectáculos teatrales, performances en directo o ensayos.

El paradigma de V1 es un **Cartwall / Soundboard** avanzado: un tablero donde cada fila representa una pista de audio que puede reproducirse de forma totalmente independiente, con su propio volumen y estado de loop, sin bloquear ni interferir con el resto.

---

## 2. Alcance de V1

### 2.1 Lo que StageCue V1 ES

- Un reproductor polifónico de archivos de audio.
- Un gestor de sesiones/proyectos persistentes.
- Una interfaz limpia y rápida, apta para uso en oscuridad (high-contrast opcional).
- Una herramienta diseñada para teclado y ratón en igualdad de condiciones.

### 2.2 Lo que StageCue V1 NO ES

- Un editor de audio (sin recorte, fade manual ni procesado).
- Un secuenciador o DAW con línea de tiempo (reservado para V2).
- Una herramienta de red o colaboración en tiempo real.

---

## 3. Usuarios Objetivo

| Rol | Necesidad principal |
|---|---|
| Técnico de sonido teatral | Disparar cues de forma precisa y sin latencia perceptible |
| Director de escena | Gestionar listas de sonidos por función/acto |
| Músico/DJ en directo | Layering de loops y ambientes simultáneos |

---

## 4. Requisitos Funcionales

### RF-01 — Carga de Archivos de Audio

- El usuario puede añadir archivos de audio mediante:
  - Menú `Archivo > Añadir pistas...` (selector de archivos múltiples).
  - Drag & Drop de archivos desde el explorador del sistema operativo al área de la tabla.
- Formatos soportados mínimos: **WAV**, **MP3**, **OGG**, **FLAC**.
- Cada pista añadida aparece como una nueva fila en la tabla principal.

### RF-02 — Tabla Principal (Cartwall)

La tabla principal es la UI central. Cada fila representa una pista con las siguientes columnas:

| # | Columna | Tipo de widget | Descripción |
|---|---|---|---|
| 1 | **Nombre** | Texto editable | Nombre legible de la pista (por defecto: nombre del fichero sin extensión) |
| 2 | **Duración** | Texto (read-only) | Duración total formateada como `MM:SS` |
| 3 | **Play / Stop** | Botón (delegado) | Alterna entre ▶ (inactiva) y ■ (reproduciendo) |
| 4 | **Loop** | Botón toggle (delegado) | Indica si la pista está en bucle (🔁 activo / off) |
| 5 | **Volumen** | Slider (delegado) | Rango 0–100%, muesca visible en 80% (nivel de carga por defecto) |
| 6 | **Ruta** | Texto (oculto/opcional) | Ruta absoluta al fichero; visible en modo diagnóstico |

### RF-03 — Controles Globales (Toolbar / Header)

- **Parar todo**: Detiene inmediatamente todos los streams activos.
- **Volumen Master**: Slider global que escala todos los volúmenes individuales.
- **Indicador de nivel (VU)**: Medidor visual simple del output total (opcional en V1, requerido en V1.1).

### RF-04 — Filtros Superiores

Ubicados en una barra persistente encima de la tabla:

- **Barra de búsqueda**: Filtra filas por nombre de pista (búsqueda en tiempo real, `QSortFilterProxyModel`).
- **Segmentador de duración**: Un widget de selección por rangos:
  - `Todos` | `< 30s` | `30s–2m` | `2m–5m` | `> 5m`
  - Filtra las filas visibles según la duración de la pista.
  - Se puede combinar con la búsqueda por nombre (filtros acumulativos).

### RF-05 — Comportamiento de Reproducción (Polifonía)

- Se pueden reproducir **N pistas simultáneamente** sin restricción de hardware impuesta por la aplicación.
- Cada pista es un stream de audio independiente gestionado por el motor de audio.
- Al pulsar **Play** en una pista inactiva: se abre un stream y comienza la reproducción.
- Al pulsar **Stop** (≡ Play de nuevo mientras suena): se detiene y reinicia la posición al inicio.
- **Loop activado**: al llegar al final del archivo, el stream recomienza automáticamente desde el inicio.
- **Loop desactivado**: al llegar al final, el stream se cierra y la UI actualiza el botón a ▶.

### RF-06 — Control de Volumen por Pista

- El volumen individual actúa como multiplicador del volumen del stream.
- El cambio de volumen se aplica **en tiempo real** sin reiniciar el stream.
- El valor por defecto al cargar una pista es **80%**.
- El rango visible del slider es 0%–100%; internamente puede mapearse a un rango lineal 0.0–1.0.

### RF-07 — Reordenación por Drag & Drop

- Las filas de la tabla son reordenables mediante drag & drop interno.
- El orden se preserva en la sesión y en el fichero de guardado.
- No se permite drag & drop externo de filas (solo archivos desde el SO para añadir pistas).

### RF-08 — Gestión de Sesiones / Proyectos

- **Guardar sesión** (`Ctrl+S`): serializa el estado actual a un fichero `.stagecue.json`.
- **Guardar como** (`Ctrl+Shift+S`): selector de ruta para el fichero.
- **Abrir sesión** (`Ctrl+O`): carga un fichero `.stagecue.json` y restaura el estado completo.
- **Nueva sesión** (`Ctrl+N`): limpia la tabla (con confirmación si hay cambios sin guardar).

#### Estructura del fichero `.stagecue.json`:

```json
{
  "version": "1.0",
  "tracks": [
    {
      "id": "uuid-v4",
      "name": "Lluvia exterior",
      "path": "/home/user/sounds/rain.wav",
      "volume": 0.75,
      "loop": true
    }
  ]
}
```

### RF-09 — Estados de Pista y Retroalimentación Visual

| Estado | Color de fila / indicador |
|---|---|
| Inactiva | Color por defecto del tema |
| Reproduciendo | Fondo suavemente resaltado (verde/azul) |
| Reproduciendo en loop | Fondo resaltado + icono 🔁 animado (opcional) |
| Archivo no encontrado | Fondo rojo tenue + tooltip de error |

### RF-10 — Accesibilidad y Atajos de Teclado

- Navegación completa por teclado en la tabla.
- `Espacio`: Play/Stop de la fila seleccionada.
- `L`: Toggle de Loop de la fila seleccionada.
- `Supr`: Eliminar pista seleccionada (con confirmación).
- `Ctrl+A`: Seleccionar todas las pistas.
- `Esc`: Limpiar selección.

---

## 5. Requisitos No Funcionales

### RNF-01 — Latencia de Audio

- La latencia entre la pulsación de Play y el inicio del audio **no debe superar 50ms** en hardware moderno bajo condiciones normales.
- El buffer del stream de audio debe ser configurable (por defecto: 1024 frames).

### RNF-02 — Estabilidad y Aislamiento

- Un fallo en la reproducción de una pista no debe bloquear la UI ni afectar a las demás pistas.
- El motor de audio se ejecuta en hilos separados del hilo principal de Qt.

### RNF-03 — Rendimiento de la UI

- La tabla debe responder fluidamente con hasta **500 pistas** cargadas.
- Los filtros deben aplicarse con latencia imperceptible (< 16ms).

### RNF-04 — Compatibilidad

- **SO**: Linux (Ubuntu 22.04+, Fedora 38+, Arch Linux).
- **Python**: 3.11+.
- **Dependencias de sistema**: ALSA o PulseAudio (gestionadas por miniaudio transparentemente).

### RNF-05 — Portabilidad de Sesiones

- Las rutas en el JSON deben guardarse como absolutas.
- Al cargar una sesión con rutas inaccesibles, la app informa pero carga el resto.

---

## 6. Casos de Uso Principales

### CU-01: Técnico prepara sesión pre-función

1. Abre StageCue.
2. Arrastra 20 ficheros WAV/MP3 a la tabla.
3. Renombra cada pista con el nombre del cue.
4. Ajusta volúmenes individualmente.
5. Activa loop en las pistas de ambiente.
6. Guarda la sesión como `funcion_01.stagecue.json`.
7. Cierra y reabre: el estado se restaura íntegramente.

### CU-02: Ejecución de cues en directo

1. El técnico tiene la sesión cargada, tabla visible.
2. Filtra por nombre "Acto 1" para ver solo las pistas relevantes.
3. Pulsa Play en "Música entrada actores" — empieza a sonar.
4. Dos minutos después, pulsa Play en "Ambiente lluvia" (ambas suenan simultáneamente).
5. Pulsa Stop en "Música entrada actores" para silenciarla.
6. "Ambiente lluvia" sigue en loop hasta que el técnico la para.

### CU-03: Ajuste de última hora

1. El técnico necesita bajar el volumen de una pista que ya está sonando.
2. Mueve el slider de esa fila — el cambio es inmediato y sin cortes.

---

## 7. Criterios de Aceptación (DoD — Definition of Done para V1)

- [ ] Las pistas se cargan y muestran en la tabla con nombre y duración correctos.
- [ ] Play/Stop funciona de forma independiente por pista.
- [ ] Se pueden reproducir al menos 8 pistas simultáneamente sin degradación audible.
- [ ] El slider de volumen modifica el nivel en tiempo real mientras suena.
- [ ] El toggle de loop funciona correctamente (la pista vuelve al inicio al terminar).
- [ ] El filtro por nombre y el segmentador de duración funcionan de forma combinada.
- [ ] Drag & Drop interno reordena las filas y el orden persiste en la sesión guardada.
- [ ] Guardar y cargar una sesión restaura el estado completo (nombre, ruta, volumen, loop, orden).
- [ ] Las pistas con archivos no encontrados no bloquean la carga de la sesión.
- [ ] La UI no se congela durante ninguna operación de audio.

---

## 8. Roadmap

| Versión | Hito principal |
|---|---|
| V1.0 | Cartwall funcional con polifonía, sesiones JSON, filtros |
| V1.1 | VU meter global, waveform thumbnail en la fila, exportar lista de cues a PDF |
| V2.0 | Línea de tiempo (mini-DAW), automatización de volumen, grupos/buses de audio |
