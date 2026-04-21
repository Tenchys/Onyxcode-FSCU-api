# Operación — Onyxcode FSCU API

## Endpoints operativos

- `GET /v1/health`: estado básico de API.
- `GET /metrics`: snapshot interno de métricas (status codes y latencias API/UTM).

## Verificación pre-publicación

Ejecutar smoke tests mínimos exigidos:

```bash
pytest -q tests/smoke/test_pre_release_checklist.py
```

Cobertura esperada en smoke:

- contratos de error 400/404/429/500
- healthcheck
- presencia de configuración Docker/healthchecks
- existencia de documentación operativa

## Despliegue Docker

- Imagen construible desde `Dockerfile`.
- Stack local con `docker-compose.yml` (API + Postgres + healthchecks).
