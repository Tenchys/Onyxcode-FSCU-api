# Fase 06 — Observabilidad, Docker y despliegue en Dokploy

- `fase_id`: `F06`
- `titulo`: `Observabilidad, Docker y despliegue en Dokploy`
- `objetivo`: `Cerrar operación productiva con logs/metricas, healthchecks, composición Docker reproducible y checklist de despliegue seguro.`
- `tipo`: `plan_base`
- `dependencias`: `["F05"]`
- `riesgos`:
  - `Despliegue sin healthchecks impide detectar degradación temprana.`
  - `Falta de métricas dificulta controlar 429/5xx y latencia.`
  - `Variables sensibles mal gestionadas exponen riesgo operacional.`
- `criterios_de_validacion`:
  - `Healthchecks activos en API y Postgres.`
  - `Logs JSON incluyen timestamp, IP, RUT consultado, latencia y resultado.`
  - `Se exponen variables necesarias para Dokploy sin secretos en repositorio.`

## Tareas

### 1) Implementar logging estructurado JSON en toda la API
- `tarea_id`: `F06-T01`
- `titulo`: `Estandarizar logs operativos`
- `que_hacer_a_nivel_de_codigo`: `Configurar app/core/logging.py con formatter JSON y middleware de request para capturar timestamp, IP, rut, latencia, status y resultado.`
- `archivos_o_modulos_impactados`:
  - `app/core/logging.py`
  - `app/core/middleware.py`
  - `app/main.py`
  - `tests/observability/test_structured_logging.py`
- `dependencias`: `["F05-T04"]`
- `pruebas_unitarias`: `Verificar esquema JSON y campos mínimos obligatorios.`
- `respuesta_esperada`: `Logs consistentes y parseables para monitoreo.`
- `criterio_de_listo`: `Todos los requests relevantes producen logs estructurados.`

### 2) Exponer métricas técnicas y de negocio mínimas
- `tarea_id`: `F06-T02`
- `titulo`: `Agregar contadores y latencias`
- `que_hacer_a_nivel_de_codigo`: `Crear app/observability/metrics.py con métricas de latencia, 4xx, 5xx, 429 y latencia de API UTM; exponer endpoint interno /metrics si aplica.`
- `archivos_o_modulos_impactados`:
  - `app/observability/metrics.py`
  - `app/main.py`
  - `tests/observability/test_metrics_collection.py`
- `dependencias`: `["F06-T01", "F04-T04", "F05-T01"]`
- `pruebas_unitarias`: `Incremento correcto de contadores por código y registro de latencias.`
- `respuesta_esperada`: `Operación puede observar desempeño y rechazo por abuso.`
- `criterio_de_listo`: `Métricas clave publicadas y verificadas.`

### 3) Preparar docker-compose productivo con healthchecks
- `tarea_id`: `F06-T03`
- `titulo`: `Definir runtime reproducible api+postgres`
- `que_hacer_a_nivel_de_codigo`: `Crear/ajustar Dockerfile y docker-compose.yml con servicios api/postgres, healthchecks, volumen persistente y variables RATE_LIMIT_* requeridas.`
- `archivos_o_modulos_impactados`:
  - `Dockerfile`
  - `docker-compose.yml`
  - `.env.example`
  - `tests/deploy/test_compose_config.py`
- `dependencias`: `["F01-T02", "F03-T01", "F06-T01"]`
- `pruebas_unitarias`: `Validación de configuración declarativa (servicios, healthchecks, variables obligatorias).`
- `respuesta_esperada`: `Entorno ejecutable consistente para despliegue.`
- `criterio_de_listo`: `Compose levanta servicios con chequeos de salud activos.`

### 4) Consolidar checklist pre-publicación y pruebas de humo
- `tarea_id`: `F06-T04`
- `titulo`: `Formalizar validación final operativa`
- `que_hacer_a_nivel_de_codigo`: `Crear tests de humo e2e mínimos (400/404/429/500, conversión UTM, healthchecks) y documento de operación alineado a CONTEXT/08-checklist.md.`
- `archivos_o_modulos_impactados`:
  - `tests/smoke/test_pre_release_checklist.py`
  - `docs/operacion.md`
  - `README.md`
- `dependencias`: `["F06-T02", "F06-T03"]`
- `pruebas_unitarias`: `Suite smoke cubre checklist de publicación y estados esperados.`
- `respuesta_esperada`: `Existe puerta de calidad objetiva previa a producción.`
- `criterio_de_listo`: `Checklist automatizable y documentación de operación vigente.`

## Cierre de fase

- `estado`: completada
- `fecha`: 2026-04-21
- `resumen`: Se implementó logging estructurado JSON (`app/core/logging.py`, `app/core/middleware.py`), métricas de latencia y status code (`app/observability/metrics.py`), Dockerfile y docker-compose.yml con healthchecks, documentación operativa (`README.md`, `docs/operacion.md`) y suite smoke covering pre-release checklist. Todas las pruebas unitarias pasan (206 passed).
- `pruebas_ejecutadas`:
  - `tests/observability/test_structured_logging.py` — 11 passed
  - `tests/observability/test_metrics_collection.py` — 9 passed
  - `tests/deploy/test_compose_config.py` — 21 passed
  - `tests/smoke/test_pre_release_checklist.py` — 18 passed
  - `tests/security/test_abuse_logging.py` — 4 passed (corregido para nuevo esquema JSON)
  - `tests/` — 206 passed en suite completa
- `resultado`: exitoso
- `pendientes`: ninguna
