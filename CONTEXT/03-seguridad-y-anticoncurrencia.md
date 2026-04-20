# Seguridad y Anticoncurrencia

## Controles
- Rate limit por IP.
- Rate limit por RUT normalizado.
- Límite global de concurrencia.
- Pool pequeño de conexiones.
- Usuario de base de datos solo lectura.

## Variables de entorno
- `RATE_LIMIT_ENABLED=true|false`
- `RATE_LIMIT_PER_MINUTE=30`
- `RATE_LIMIT_PER_IP=20`
- `RATE_LIMIT_PER_RUT=5`
- `RATE_LIMIT_BURST=5`
- `RATE_LIMIT_WINDOW_SECONDS=60`

## Reglas
- Rechazar consultas excesivas con `429`.
- Evitar SQL dinámico.
- Registrar eventos de abuso.
- Timeouts estrictos en consultas.
