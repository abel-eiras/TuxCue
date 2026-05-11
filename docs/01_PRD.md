# TuxCue — Product Requirements Document (PRD)

**Version:** 1.1  
**Status:** Activo  
**Fuente:** Documento Maestro de Especificaciones  
**Fecha:** 2026-05-11  

---

## 1. Visión y Concepto

**TuxCue** es un software de reproducción de audio diseñado específicamente para la regiduría y el control de sonido en producciones teatrales y espectáculos en directo. Su objetivo es ofrecer precisión visual absoluta y control táctico sobre múltiples pistas, superando las limitaciones de los reproductores convencionales sin llegar a la complejidad innecesaria de un DAW completo en su etapa inicial.

### Fases del Producto

| Fase | Nombre | Descripción |
|---|---|---|
| **Fase 1** (actual) | Cartwall / Soundboard | Sistema de lista de reproducción **no lineal**. No salta automáticamente a la siguiente pista. Permite polifonía, control individual de volumen y bucles. Ideal para mantener camas de sonido ambientales mientras se disparan efectos puntuales durante una escena. |
| **Fase 2** (futura) | Línea de Tiempo | Evolución hacia un mini-DAW donde las pistas podrán colocarse en una línea temporal para ejecuciones automatizadas y complejas. |

---

## 2. Interfaz de Usuario (UI)

La interfaz debe ser **limpia** y priorizar la legibilidad rápida en **entornos de poca luz** (típico de las cabinas de control teatral).

### 2.1 Controles Superiores (Filtros)

Ubicados en una barra persistente sobre la tabla principal:

| Control | Tipo | Comportamiento |
|---|---|---|
| **Buscador de texto** | `QLineEdit` | Filtra la lista de pistas en tiempo real por nombre. La búsqueda es insensible a mayúsculas. |
| **Segmentador de tiempo** | Inputs o sliders de rango | Aísla visualmente las pistas cuya duración esté dentro de un rango específico. Se combina acumulativamente con el buscador de texto. |

### 2.2 Vista de Lista Principal (Tabla — Cartwall)

Cada fila representa un archivo de audio cargado. Las columnas son:

| # | Columna | Descripción |
|---|---|---|
| 1 | **Nombre** | Título identificativo de la pista. Editable por el usuario. |
| 2 | **Duración** | Tiempo total del audio, formateado como `MM:SS`. |
| 3 | **Play / Stop** | Botón de control de reproducción individual. Mientras la pista suena se convierte en Stop. |
| 4 | **Loop (Bucle)** | Interruptor *toggle*. Cuando está activo, el audio vuelve a empezar al terminar. |
| 5 | **Volumen** | Slider de ganancia individual. Permite normalizar audios directamente en el software sin depender de la mesa de mezclas de la sala. Rango: **0% – 100%**. |

### 2.3 Interacción del Usuario

- **Drag & Drop interno:** El usuario puede pinchar y arrastrar filas para reordenar los audios según el guion del espectáculo. El nuevo orden se refleja inmediatamente en la sesión y se persiste al guardar.
- **Carga de archivos:** Mediante menú o arrastre de archivos desde el explorador del sistema operativo.

---

## 3. Comportamiento y Lógica de Audio

El núcleo del reproductor se aleja del estándar de consumo (reproducción secuencial) para abrazar las necesidades del directo.

### 3.1 Polifonía (Multicanalidad)

Es el comportamiento fundamental:

- El usuario puede dar *Play* a la "Pista 1" (ej. ambiente de lluvia) y, mientras suena, dar *Play* a la "Pista 2" (ej. trueno).
- **Ambas pistas suenan simultáneamente** y se mezclan hacia la salida maestra sin cortes ni latencia perceptible.
- No hay límite de software en el número de pistas simultáneas; el límite es el hardware del sistema.

### 3.2 Aislamiento de Estado

- El volumen, el estado de reproducción y el estado de bucle de una pista **no afectan en absoluto a las demás**.
- Un fallo en la reproducción de una pista no interrumpe ni bloquea las otras.

### 3.3 Comportamiento de Play / Stop

- **Play** en pista inactiva: abre un stream de audio y comienza la reproducción.
- **Stop** (pulsar de nuevo Play mientras suena): detiene la reproducción y reinicia la posición al inicio.
- **Loop activo:** al llegar al final del archivo, el stream recomienza automáticamente desde el inicio.
- **Loop inactivo:** al llegar al final, el stream se cierra y el botón vuelve al estado ▶.

### 3.4 Control de Volumen en Tiempo Real

- El slider de volumen modifica la ganancia del stream **mientras suena**, sin cortes ni reinicio.
- El nivel por defecto al cargar una pista es **80%** (0.8 en escala lineal 0.0–1.0).

---

## 4. Gestión de Sesiones (Persistencia)

Para ser una herramienta de trabajo viable, la configuración de un espectáculo no puede perderse al cerrar el programa.

### 4.1 Operaciones

| Acción | Atajo | Descripción |
|---|---|---|
| **Guardar** | `Ctrl+S` | Serializa el estado actual al fichero de sesión activo. |
| **Guardar como** | `Ctrl+Shift+S` | Permite elegir la ruta del fichero de sesión. |
| **Cargar / Abrir** | `Ctrl+O` | Carga un fichero `.tuxcue.json` y restaura el estado completo. |
| **Nueva sesión** | `Ctrl+N` | Limpia la tabla (con confirmación si hay cambios sin guardar). |

### 4.2 Formato de Datos: JSON

El archivo guardará exactamente los siguientes datos, conforme al Documento Maestro:

1. La **ruta absoluta** de cada archivo de audio cargado.
2. El **orden exacto** en el que aparecen en la lista.
3. El **nivel de volumen** configurado en el slider de cada pista.
4. El **estado del botón Loop** (activo/inactivo) de cada pista.

#### Estructura de referencia del fichero `.tuxcue.json`:

```json
{
  "version": "1.0",
  "tracks": [
    {
      "id": "uuid-v4",
      "name": "Ambiente lluvia",
      "path": "/home/user/sounds/rain.wav",
      "volume": 0.8,
      "loop": true
    },
    {
      "id": "uuid-v4",
      "name": "Trueno",
      "path": "/home/user/sounds/thunder.wav",
      "volume": 1.0,
      "loop": false
    }
  ]
}
```

> **Nota:** El estado de reproducción (`is_playing`) nunca se serializa. Las sesiones siempre cargan con todos los tracks detenidos.

### 4.3 Tolerancia a Fallos de Carga

- Si al cargar una sesión un archivo no se encuentra en la ruta guardada, la aplicación:
  - Informa al usuario del problema (visual y/o diálogo).
  - Carga el resto de pistas sin bloquear la operación.
  - Marca visualmente las pistas con archivo no encontrado.

---

## 5. Requisitos No Funcionales

| ID | Requisito | Criterio |
|---|---|---|
| RNF-01 | **Latencia de audio** | < 50 ms entre pulsación de Play y inicio del sonido en hardware moderno. |
| RNF-02 | **Estabilidad** | La UI no se congela en ninguna operación de audio. El motor corre en hilos separados. |
| RNF-03 | **Rendimiento de la UI** | Fluidez con hasta 500 pistas cargadas; los filtros responden en < 16 ms. |
| RNF-04 | **Compatibilidad de SO** | Linux x86_64 (Ubuntu 22.04+, Fedora 38+, Arch Linux). |
| RNF-05 | **Legibilidad en oscuridad** | Interfaz de alto contraste, tipografía clara, sin elementos decorativos que distraigan. |

---

## 6. Casos de Uso Principales

### CU-01: Preparación pre-función

1. El técnico abre TuxCue.
2. Arrastra los ficheros de audio a la tabla.
3. Renombra cada pista con el nombre del cue del guion.
4. Ajusta el volumen individual de cada pista para compensar diferencias de ganancia.
5. Activa Loop en las pistas de ambiente.
6. Guarda la sesión como `funcion_sabado_noche.tuxcue.json`.
7. Cierra y reabre: el estado se restaura íntegramente (orden, nombres, volúmenes, loops).

### CU-02: Ejecución en directo

1. El técnico tiene la sesión cargada.
2. Filtra por "Acto 1" para ver solo las pistas relevantes.
3. Da Play a "Música entrada actores" — empieza a sonar.
4. Dos minutos después, da Play a "Ambiente lluvia" — ambas suenan simultáneamente.
5. Da Stop a "Música entrada actores" para silenciarla; "Ambiente lluvia" sigue en loop.
6. Ajusta el volumen de "Ambiente lluvia" en tiempo real sin cortes.

### CU-03: Ajuste de emergencia

1. Una pista suena demasiado alta durante la función.
2. El técnico mueve el slider de esa fila: el cambio es inmediato y sin reiniciar el audio.

---

## 7. Criterios de Aceptación — V1 (Definition of Done)

- [ ] Las pistas se cargan y muestran en tabla con nombre y duración correctos.
- [ ] Play/Stop funciona de forma independiente por pista.
- [ ] Al menos 8 pistas suenan simultáneamente sin degradación audible.
- [ ] El slider de volumen modifica el nivel en tiempo real mientras la pista suena.
- [ ] El toggle de Loop hace que la pista recomience al llegar al final.
- [ ] El buscador de texto filtra por nombre en tiempo real.
- [ ] El segmentador de tiempo filtra por rango de duración.
- [ ] Ambos filtros se combinan de forma acumulativa.
- [ ] Drag & Drop interno reordena las filas; el orden se persiste en la sesión.
- [ ] Guardar y cargar una sesión restaura: nombre, ruta, volumen, estado de loop y orden.
- [ ] Las pistas con archivos no encontrados no bloquean la carga de la sesión.
- [ ] La UI no se congela en ninguna operación de audio.

---

## 8. Roadmap

| Versión | Entregable |
|---|---|
| V1.0 | Cartwall funcional: polifonía, filtros, drag & drop, sesiones JSON |
| V1.1 | VU meter global, waveform thumbnail por pista, exportar lista de cues |
| V2.0 | Línea de tiempo (mini-DAW), automatización de volumen, grupos/buses |
