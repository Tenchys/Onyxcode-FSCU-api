# API FastAPI

## Endpoint principal
- `GET /v1/rut/{rut}`

## Respuesta
- `found`
- `rut`
- `dv`
- `nombre`
- `universidad`
- `monto_utm`
- `monto_clp`
- `utm_fecha`

## Errores
- `400` formato inválido
- `404` no encontrado
- `429` exceso de solicitudes
- `500` error interno
