# AGENTS.md

Repositorio para una API pública en FastAPI + Postgres que permite buscar un RUT chileno en `SQL/deudores_morosos.sql`.

## Reglas base
- Priorizar seguridad, consultas exactas y respuestas mínimas.
- Evitar búsquedas parciales, listados masivos y SQL dinámico.
- Controlar concurrencia, rate limit y timeouts.
- Implementar solo una fase por ejecución; no avanzar ni mezclar fases futuras.

## Contexto
- `CONTEXT/00-overview.md`
- `CONTEXT/01-dominio-y-datos.md`
- `CONTEXT/02-api-fastapi.md`
- `CONTEXT/03-seguridad-y-anticoncurrencia.md`
- `CONTEXT/04-postgres-y-sql.md`
- `CONTEXT/05-utm-a-peso-chileno.md`
- `CONTEXT/06-docker-y-dokploy.md`
- `CONTEXT/07-operacion-y-observabilidad.md`
- `CONTEXT/08-checklist.md`
