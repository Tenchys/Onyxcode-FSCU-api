---
description: Corrige una rama a partir del informe del reviewer
agent: code-fixer
subtask: true
model: openai/gpt-5.3-codex
---
Usa la skill `fscu-phase-implementer` como referencia de la fase y lee el informe del reviewer pasado como argumento.

Si se invoca como `/code-fix <ruta_informe_reviewer>`, usa `$1` como archivo de entrada principal. La ruta debe apuntar al `.md` generado por `code-reviewer` en `.opencode/reports/reviewer/`.

Tu trabajo es corregir solo los hallazgos descritos en ese informe, ejecutar las pruebas necesarias y dejar un informe final en `.opencode/reports/fixer/`.
No amplias alcance ni cambias la fase.
Debes justificar el porque de cada solucion propuesta.

Devuelve al final:
- resumen de correcciones
- razon tecnico de la solucion
- pruebas ejecutadas
- ruta del informe final
