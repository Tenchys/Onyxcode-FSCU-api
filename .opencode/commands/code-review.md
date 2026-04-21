---
description: Revisa una rama contra la fase y reporta discrepancias
agent: code-reviewer
subtask: true
model: openai/gpt-5.3-codex
---
Usa la skill `fscu-phase-implementer` como referencia para identificar la fase objetivo y sus criterios.

Si se invoca como `/code-review <fase_id|rama>`, usa `$1` como referencia principal de revision. Si esta vacio, revisa la primera fase pendiente de `PHASES/status.md` contra la rama actual.

Tu trabajo es comparar lo implementado en la rama con lo indicado en la fase y reportar discrepancias, omisiones, riesgos y cobertura de pruebas.
No modifiques codigo.
Se mas exhaustivo que el implementer.

Devuelve al final:
- veredicto
- hallazgos ordenados por severidad
- discrepancias con la fase
- pruebas revisadas
- riesgos residuales
