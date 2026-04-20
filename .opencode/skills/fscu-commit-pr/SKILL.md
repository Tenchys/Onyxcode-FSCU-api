---
name: fscu-commit-pr
description: Flujo reusable para validar, commitear y abrir pull requests
---
## Objetivo
Crear un flujo seguro y repetible para preparar un commit y abrir un PR.

## Procedimiento
1. Verifica el estado del repo con `git status` y `git diff`.
2. Confirma la rama actual y el branch base si aplica.
3. Identifica el comando de pruebas unitarias del proyecto.
4. Ejecuta las pruebas unitarias relevantes antes del commit.
5. Si las pruebas fallan, detente y reporta el fallo.
6. Stagea solo los archivos necesarios.
7. Crea un commit con mensaje breve, específico y centrado en el motivo.
8. Publica la rama si es necesario.
9. Abre el PR con `gh pr create` y resume:
   - objetivo del cambio
   - pruebas ejecutadas
   - riesgos o notas relevantes

## Reglas
- No usar `--force`.
- No tocar secretos, credenciales ni archivos no relacionados.
- No abrir PR si las pruebas unitarias no pasan.
- Preferir cambios mínimos y mensajes de commit claros.
