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
