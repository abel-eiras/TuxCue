# TuxCue — Decisiones, Errores y Lecciones Aprendidas

Este documento es la **memoria viva del proyecto**. Se actualiza con cada decisión no trivial,
error encontrado durante el desarrollo y lección aprendida. Sirve como contexto para cualquier
colaborador (humano o agente) que se incorpore al proyecto.

Formato de cada entrada:

```
### [YYYY-MM-DD] Título breve
**Contexto:** qué se estaba haciendo
**Problema / Decisión:** qué ocurrió o qué se decidió
**Causa raíz:** por qué ocurrió (solo para errores)
**Resolución:** qué se hizo
**Lección:** qué no repetir / qué aplicar en el futuro
```

---

## Fase de Especificación (Spec-Driven Development)

### [2026-05-11] El Documento Maestro es la única fuente de verdad para nombres propios

**Contexto:** Durante la fase de spec inicial, el asistente extrapoló el nombre del proyecto
a partir del brief en lugar de tomarlo literalmente del Documento Maestro.

**Causa raíz:** Error de asunción. El Documento Maestro existía y era explícito; no había
ninguna ambigüedad que justificase la extrapolación.

**Resolución:** Todos los documentos, extensiones de fichero y referencias se corrigieron para
coincidir exactamente con el Documento Maestro.

**Lección:** El Documento Maestro es la fuente de verdad. Nunca extrapolar nombres propios;
copiarlos literalmente. Si hay ambigüedad real, preguntar antes de escribir.

---

### [2026-05-11] Rama `main` no existía al crear la primera PR

**Contexto:** Se intentó crear una PR al finalizar la fase de spec en un repositorio recién
inicializado que solo tenía la rama de trabajo activa.

**Problema:** La API de GitHub devolvió `422 Validation Failed` — no había rama `main` como
destino de la PR.

**Causa raíz:** Los repositorios nuevos sin push inicial a `main` no tienen esa rama por defecto.
El flujo "crear repo → primera rama de feature" omite crear `main` explícitamente.

**Resolución:** Se creó `main` apuntando al commit actual de la rama de trabajo via GitHub MCP.

**Consecuencia secundaria:** Como `main` quedó apuntando al mismo commit que la rama de trabajo,
la PR habría mostrado 0 diferencias. Se decidió continuar implementando Fase 0 sobre la misma
rama para que la PR incluya diff real de código.

**Lección:** En repositorios nuevos, crear y hacer push a `main` con un commit inicial antes de
crear ramas de feature. El orden correcto es:
`git init → commit inicial en main → push main → crear rama de feature → PR`.

---

## Fase 0 — Contrato Compartido (Core Contracts)

### [2026-05-11] PySide6 requiere libEGL en entornos headless

**Contexto:** Al ejecutar los tests de `AudioController` (que instancian `QObject` y emiten
señales Qt) en el entorno de desarrollo (contenedor Linux sin display), los tests se marcaban
como SKIPPED porque la importación de `PySide6.QtWidgets` lanzaba:
`ImportError: libEGL.so.1: cannot open shared object file: No such file or directory`.

**Problema:** El check `_qt_available = True/False` se evaluaba en tiempo de importación del
módulo de test. Como la importación fallaba, la variable quedaba `False` y todos los tests del
módulo se marcaban como SKIPPED en lugar de FAILED, ocultando la causa real.

**Causa raíz:** PySide6 enlaza dinámicamente con `libEGL.so.1` en el momento de importar el
módulo C extension, independientemente de la plataforma de renderizado elegida
(`QT_QPA_PLATFORM`). El entorno no tenía instalado el paquete del sistema `libegl1`.

**Resolución (dos pasos):**
1. Se añadió `tests/conftest.py` con `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")`
   para asegurar que Qt use el backend offscreen en entornos sin display.
2. Se instaló la dependencia del sistema: `apt-get install -y libegl1`.

**Lección:**
- `QT_QPA_PLATFORM=offscreen` solo evita que Qt intente conectar a un display real en
  *runtime*; no elimina la dependencia de `libEGL.so.1` en tiempo de *import*.
- En entornos CI o contenedores, añadir `libegl1` (o `libegl-mesa0`) al Dockerfile/setup.
- El patrón `try/except ImportError → pytestmark.skipif` es útil para tests opcionales
  (p.ej. si PySide6 no está instalado), pero enmascara errores de entorno. Documentar
  siempre las dependencias del sistema en `docs/03_TECH_STACK.md`.

### [2026-05-11] Decisión: callbacks como Callables en IAudioEngine, no Qt signals

**Contexto:** Diseño de cómo el `AudioEngine` notifica al `AudioController` cuando un stream
arranca, termina o falla.

**Opciones consideradas:**
1. Que `AudioEngine` emita señales Qt directamente.
2. Que `AudioEngine` reciba callbacks Python planos (`Callable[[str], None]`).

**Decisión:** Se eligió la opción 2 (callbacks Python).

**Razonamiento:**
- La opción 1 requeriría que `AudioEngine` heredara de `QObject` o tuviera referencia a Qt,
  lo que viola el principio de que `src/audio` no depende de `src/gui` ni de Qt.
- Con la opción 2, `AudioEngine` es puro Python + miniaudio: no importa PySide6 en absoluto.
  Esto lo hace testeable sin `QApplication`, portable a otros backends (JACK, etc.) y
  ejecutable en contextos sin display.
- `AudioController` (que sí es `QObject`) recibe los callbacks y los convierte en señales Qt.
  La emisión de señales Qt es thread-safe, por lo que los callbacks pueden llamarse desde
  el hilo de audio de miniaudio sin riesgo.

---

## Rama A — Motor de Audio

### [2026-05-11] Posible doble-priming del generador en TrackStream.start()

**Contexto:** En `src/audio/stream.py`, el método `start()` prima el generador con `next(gen)`
antes de pasarlo a `miniaudio.PlaybackDevice.start(gen)`. La duda es si `PlaybackDevice.start()`
vuelve a llamar `next()` internamente, lo que consumiría el primer chunk de audio dos veces.

**Impacto potencial:** Si `PlaybackDevice` llama `next()` internamente, el primer chunk de
1024 frames (≈23 ms a 44100 Hz) se descartaría silenciosamente. En audio de teatro esto es
imperceptible, pero es incorrecto por principio.

**Estado:** ✅ RESUELTO — comportamiento correcto confirmado inspeccionando el código fuente
de miniaudio.

**Resolución:** El docstring de `PlaybackDevice.start()` dice explícitamente:
_"The generator should already be started before passing it in."_
Esto confirma que miniaudio **no** llama `next()` internamente — requiere que el caller lo
prime. El `next(gen)` en `TrackStream.start()` es correcto y necesario.

**Lección:** Antes de registrar una duda como "pendiente de hardware", inspeccionar el código
fuente de la librería con `inspect.getsource()`. Habría resuelto esto sin necesidad de hardware.
Los tests hardware-free son necesarios pero no suficientes; complementar con integración real.

---

## Rama B — Interfaz Gráfica

### [2026-05-11] DeprecationWarning de PySide6 6.11 para invalidateFilter() / invalidateRowsFilter()

**Contexto:** Al implementar `TrackFilterProxyModel.set_duration_segment()`, se llamó a
`self.invalidateFilter()` para refrescar el proxy tras cambiar el segmento de duración.

**Problema:** PySide6 6.11.0 emite `DeprecationWarning` tanto para `invalidateFilter()` como
para `invalidateRowsFilter()`, aunque ambos métodos siguen siendo parte de la API pública de Qt6.

**Causa raíz:** Regresión en los bindings Python de PySide6 6.11 — los wrappers C++ de estos
métodos están marcados con el decorador de deprecación de Qt aunque la función subyacente no
está eliminada. El método `invalidate()` (QObject slot) también está disponible pero tiene
semántica ligeramente distinta (invalida también el orden, no solo el filtro).

**Resolución:** Se mantiene `invalidateFilter()` porque su semántica es la correcta para
refrescar solo el filtro. La advertencia es cosmética y no afecta el comportamiento ni los
tests (51/51 passing). Se suprimirá si PySide6 publica un fix de bindings.

**Lección:** En PySide6, las `DeprecationWarning` de los bindings no siempre coinciden con
las deprecaciones reales de Qt. Verificar siempre en la documentación oficial de Qt6 antes de
migrar a una alternativa.

---

## Integración — SessionManager

### [2026-05-11] Raw string check en JSON contaminated by pytest tmp_path name

**Contexto:** Test `test_is_playing_never_serialized` verificaba que `"is_playing"` no
apareciera en el JSON serializado usando `assert "is_playing" not in raw` sobre el texto
completo del fichero.

**Problema:** pytest construye directorios temporales cuyo nombre deriva del id del test:
`/tmp/pytest-of-root/pytest-8/test_is_playing_never_serializ0/sound.wav`. El fragmento
`is_playing` queda embebido en el campo `"path"` del JSON, haciendo fallar la aserción
aunque el comportamiento del código es correcto.

**Causa raíz:** El test usaba una comprobación de substring sobre el JSON completo en lugar
de inspeccionar la estructura de datos parseada. Una ruta de fichero que contiene el string
buscado contamina el resultado.

**Resolución:** Se reemplazó la comprobación raw por una que parsea el JSON y comprueba que
ninguna clave del diccionario de cada track sea `"is_playing"`.

**Lección:** Nunca verificar la ausencia de un string en un JSON serializado mediante
búsqueda de substring en el texto crudo; el valor de algún campo (p.ej. una ruta de fichero)
puede contenerlo por coincidencia. Parsear y comprobar la estructura.
