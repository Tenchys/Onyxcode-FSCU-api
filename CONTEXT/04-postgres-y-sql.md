# Postgres y SQL

## Acceso
- Solo `SELECT` en producción.

## Estrategia
- Consulta exacta por `rut + dv`.
- Índice recomendado sobre `(rut, dv)`.

## Reglas
- Queries parametrizadas.
- `statement_timeout` activo.
- No usar búsquedas libres.
- Mantener la tabla de solo lectura.
