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

### [2026-05-11] Nombre del proyecto: StageCue → TuxCue

**Contexto:** El primer borrador de docs usaba "StageCue" como nombre (derivado del brief inicial
del asistente). El Documento Maestro proporcionado por el usuario usa "TuxCue".

**Problema:** Los ficheros `docs/01_PRD.md`, `docs/02_ARCHITECTURE.md`, `.cursorrules` y el
nombre de la extensión de sesión (`.stagecue.json`) no coincidían con el Documento Maestro.

**Causa raíz:** El nombre fue extrapolado del brief en lugar de tomarse literalmente del
Documento Maestro. Error de asunción durante la fase de spec inicial.

**Resolución:** En la segunda iteración de los docs se renombraron todas las referencias a
"TuxCue" y la extensión de sesión a `.tuxcue.json`.

**Lección:** El Documento Maestro es la fuente de verdad. Nunca extrapolar nombres propios;
copiarlos literalmente. Si hay ambigüedad, preguntar antes de escribir.

---

### [2026-05-11] Rama `main` no existía al crear la PR

**Contexto:** Se intentó crear una PR desde `claude/stagecue-spec-phase-rUv82` hacia `main`
al finalizar la fase de spec.

**Problema:** La API de GitHub devolvió `422 Validation Failed` porque el repositorio no tenía
rama `main` (era un repo nuevo con un solo commit en la rama de trabajo).

**Causa raíz:** Los repositorios nuevos sin push inicial a `main` no tienen esa rama por defecto.
El flujo habitual de "crear repo → primera rama de feature" omite crear `main` explícitamente.

**Resolución:** Se creó `main` apuntando al commit actual de la rama de spec via GitHub MCP
(`create_branch main from claude/stagecue-spec-phase-rUv82`).

**Consecuencia secundaria:** Como `main` quedó apuntando al mismo commit que la rama de spec,
la PR habría mostrado 0 diferencias. Se decidió continuar implementando Fase 0 sobre la misma
rama, de forma que la PR incluya diff real (código de Fase 0) cuando se abra.

**Lección:** En repositorios nuevos, crear y hacer push a `main` con un commit inicial vacío
(o el README) antes de crear ramas de feature. El orden correcto es:
`git init → commit inicial en main → push main → crear rama de feature → PR`.

---

## Fase 0 — Contrato Compartido (Core Contracts)

<!-- Las entradas de Fase 0 se añadirán aquí durante la implementación -->
