---
name: fscu-phase-implementer
description: Ejecuta una sola fase pendiente del plan de forma atomica, con codigo limpio y pruebas unitarias
---

## Objetivo
Convertir una fase pendiente del plan en cambios concretos de codigo, pruebas y actualizacion minima de estado.

## Alcance
- Una sola fase pendiente por ejecucion.
- Si el usuario indica `fase_id`, usarla.
- Si no, elegir la primera fase pendiente en `PHASES/status.md`.
- No avanzar a fases futuras.
- No reescribir fases ya completadas salvo dependencia critica minima.

## Reglas
- Revisar `PHASES/` y `PHASES/status.md` antes de tocar codigo.
- Confirmar dependencias de la fase.
- Aplicar clean architecture y clean code.
- Usar SQLAlchemy parametrizado y configuracion por entorno.
- No hardcodes de URLs, credenciales, limites ni timeouts.
- Toda logica critica debe tener pruebas unitarias.
- Priorizar cambios minimos, seguros y verificables.
- Si falta un prerrequisito, detenerse y reportar bloqueo.
- Al terminar la fase, actualizar `PHASES/status.md` con `completed_tasks`, `pending_tasks` y `total_tasks`.
- Si la fase se completo, dejar trazado en el archivo de la fase correspondiente.
- El trazado de cierre debe incluir un resumen corto, fecha y estado final de la fase.
- El bloque de cierre debe seguir exactamente este formato:
  ```md
  ## Cierre de fase

  - `estado`: completada
  - `fecha`: YYYY-MM-DD
  - `resumen`: ...
  - `pruebas_ejecutadas`:
    - `...`
  - `resultado`: exitoso | fallido
  - `pendientes`: ninguna | ...
  ```

## Flujo
1. Identificar la fase pendiente.
2. Leer tareas y dependencias.
3. Implementar solo esa fase.
4. Agregar o ajustar pruebas de la fase.
5. Ejecutar validacion.
6. Actualizar el estado de la fase en `PHASES/status.md` y agregar el bloque de cierre en el archivo de la fase.
7. Reportar resumen y siguiente fase pendiente.

## Criterios de salida
- Fase implementada.
- Archivos tocados.
- Pruebas ejecutadas.
- Resultado de validacion.
- Bloqueos o riesgos pendientes.

## Notas operativas
- La implementacion debe ser atomica.
- Si una tarea requiere cambios fuera del alcance de la fase, documentarlo pero no extender la ejecucion.
- Si hay multiples tareas dentro de la fase, implementa el conjunto minimo necesario para dejar la fase completa y verificable.
