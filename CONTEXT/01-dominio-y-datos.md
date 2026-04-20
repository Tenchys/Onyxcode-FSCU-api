# Dominio y Datos

## Fuente
- Esquema: `SQL/deudores_morosos.sql`

## Campos relevantes
- `rut`
- `dv`
- `apellido_paterno`
- `apellido_materno`
- `nombres`
- `monto_utm`
- `cod_universidad`
- `universidad`

## Reglas
- Validar formato de RUT antes de consultar.
- Buscar por `rut + dv`.
- No exponer más datos que los necesarios.
