---
description: Implementa la siguiente fase pendiente del plan
agent: FSCU-phase-implementer
subtask: true
model: opencode-go/minimax-m2.7
---
Usa la skill `fscu-phase-implementer`.

Si se invoca como `/implement-phase <fase_id>`, usa `$1` como fase objetivo. Si esta vacio, implementa la primera fase pendiente en `PHASES/status.md`.

Antes de implementar, crea o reutiliza la rama `feature/fase-{numero_de_fase}` correspondiente y cambiate a ella.

Tu trabajo es implementar solo una fase por ejecucion, con pruebas unitarias y sin avanzar a fases futuras.
Al finalizar, actualiza el estado de la fase en `PHASES/status.md`.
Si la fase termina, agrega un bloque de cierre en el archivo de la fase.
Usa este formato exacto para el cierre:

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
