---
description: Prepara commit, corre tests y abre un PR
agent: FSCU-commiter
subtask: true
model: opencode-go/qwen3.5-plus
---
Usa la skill `fscu-commit-pr`.

Primero inspecciona el estado actual con:
!`git status --short`
!`git diff --stat`
!`git log --oneline -5`

Luego identifica y ejecuta las pruebas unitarias adecuadas para este repo. Si fallan, detente y reporta el error.

Si pasan, prepara un commit limpio solo con los archivos necesarios, haz push de la rama y crea el PR con `gh pr create`.

Devuelve al final:
- resumen del cambio
- pruebas ejecutadas
- URL del PR
