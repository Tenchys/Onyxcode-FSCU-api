# Docker y Dokploy

## Servicios
- `api`
- `postgres`

## Reglas
- Configuración por variables de entorno.
- Exponer `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_PER_IP`, `RATE_LIMIT_PER_RUT`, `RATE_LIMIT_BURST` y `RATE_LIMIT_WINDOW_SECONDS` en el despliegue.
- Healthchecks en ambos servicios.
- Volumen persistente para Postgres.
- Exponer solo lo necesario para Dokploy.

## Despliegue
- Imagen reproducible.
- `docker compose` listo para producción.
- Sin secretos en el repo.
