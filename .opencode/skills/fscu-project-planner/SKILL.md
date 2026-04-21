---
name: fscu-project-planner
description: Guía para descomponer requerimientos del proyecto en fases, tareas atómicas y deltas de ampliación
---

## Objetivo
Convertir un requerimiento funcional, una ampliación de alcance o un fallo reportado en un plan técnico ejecutable por otro subagente.
El plan debe materializarse en archivos dentro de `PHASES/` en la raíz del repositorio.

## Contexto del proyecto
- API pública en FastAPI + Postgres.
- Consulta exacta de RUT chileno en una base local.
- Prioridad en seguridad, rate limit, concurrencia limitada, timeouts y respuestas mínimas.
- No proponer búsquedas parciales, listados masivos ni SQL dinámico.

## Modos de entrada
1. `plan_base`: crea el plan inicial del proyecto o de una funcionalidad nueva.
2. `extender_plan`: agrega fases nuevas o ajusta fases existentes para ampliar alcance o corregir fallos.

## Reglas de descomposición
- Cada tarea debe ser atómica y verificable.
- Cada tarea debe describir cambios a nivel de código, no solo intención funcional.
- Cada tarea debe incluir pruebas unitarias asociadas.
- Cada tarea debe tener una respuesta esperada o criterio de aceptación.
- Las dependencias entre tareas deben quedar explícitas.
- Si una tarea depende de otra, debe indicarlo con `depende_de`.
- Si el pedido es un bugfix, la primera fase debe contemplar reproducción o confirmación del fallo.

## Persistencia del plan
- Cada fase debe guardarse en un archivo `.md` independiente dentro de `PHASES/`.
- La carpeta `PHASES/` debe crearse si no existe.
- `PHASES/status.md` debe existir y reflejar:
  - tareas completadas
  - tareas pendientes
  - total de tareas
- La salida estructurada y los archivos guardados deben mantenerse sincronizados.
- Si el plan cambia, deben actualizarse los archivos de fase y `PHASES/status.md`.

## Reglas para `extender_plan`
- No rehacer el plan completo salvo que el usuario lo pida.
- Emitir un delta: fases nuevas, fases afectadas y dependencias actualizadas.
- Marcar qué tareas quedan obsoletas, se reemplazan o se mantienen.
- Si el alcance crece, insertar la nueva fase en el lugar correcto del flujo.
- Si el pedido es un fallo reportado, priorizar reproducción, fix mínimo y prueba de regresión.

## Formato de salida
La salida debe ser una lista de fases. Cada fase debe contener:
- `fase_id`
- `titulo`
- `objetivo`
- `tipo`: `plan_base` o `extender_plan`
- `dependencias`
- `tareas`

Cada fase debe persistirse en un archivo como `PHASES/01-<titulo>.md`, `PHASES/02-<titulo>.md`, etc.

`PHASES/status.md` debe incluir al menos estos campos:
- `completed_tasks`
- `pending_tasks`
- `total_tasks`

Cada tarea debe contener:
- `tarea_id`
- `titulo`
- `que_hacer_a_nivel_de_codigo`
- `archivos_o_modulos_impactados`
- `dependencias`
- `pruebas_unitarias`
- `respuesta_esperada`
- `criterio_de_listo`

## Criterios de calidad
- Mantener el plan mínimo y preciso.
- Evitar tareas demasiado amplias.
- Alinear el plan con las reglas del proyecto: exactitud, seguridad y control de abuso.
- Incluir pruebas unitarias para validación de RUT, errores `400/404/429/500`, rate limit o lógica nueva, según aplique.
