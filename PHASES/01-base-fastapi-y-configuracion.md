# Fase 01 — Base FastAPI y configuración segura

- `fase_id`: `F01`
- `titulo`: `Base FastAPI y configuración segura`
- `objetivo`: `Levantar una base de aplicación FastAPI con configuración por entorno y estructura modular mínima para habilitar desarrollo seguro.`
- `tipo`: `plan_base`
- `dependencias`: `[]`
- `riesgos`:
  - `Variables de entorno incompletas provocan arranque inconsistente.`
  - `Estructura inicial débil dificulta aplicar controles de seguridad posteriores.`
- `criterios_de_validacion`:
  - `La app inicia con configuración válida y falla explícitamente con configuración faltante.`
  - `Existe separación clara entre capa API, servicios, infraestructura y configuración.`

## Tareas

### 1) Crear esqueleto de aplicación y punto de entrada
- `tarea_id`: `F01-T01`
- `titulo`: `Inicializar estructura app y main FastAPI`
- `que_hacer_a_nivel_de_codigo`: `Crear app/main.py con factory create_app(), registrar router v1 y endpoint base /health. Crear paquetes app/api, app/core, app/services, app/db, tests.`
- `archivos_o_modulos_impactados`:
  - `app/main.py`
  - `app/api/__init__.py`
  - `app/api/v1/__init__.py`
  - `app/api/v1/health.py`
  - `tests/test_health.py`
- `dependencias`: `[]`
- `pruebas_unitarias`: `test_health_ok devuelve 200 y payload mínimo de estado.`
- `respuesta_esperada`: `GET /health responde 200 con estado "ok".`
- `criterio_de_listo`: `Servidor ejecuta sin errores y test de salud pasa.`

### 2) Implementar configuración tipada por entorno
- `tarea_id`: `F01-T02`
- `titulo`: `Agregar settings centralizados y validación estricta`
- `que_hacer_a_nivel_de_codigo`: `Crear app/core/settings.py con BaseSettings para DB, rate limit, timeouts y flags obligatorias. Forzar valores por defecto seguros y validaciones de rango.`
- `archivos_o_modulos_impactados`:
  - `app/core/settings.py`
  - `app/main.py`
  - `.env.example`
  - `tests/core/test_settings.py`
- `dependencias`: `["F01-T01"]`
- `pruebas_unitarias`: `test_settings_requires_db_url, test_settings_reject_invalid_rate_limits.`
- `respuesta_esperada`: `La app no inicia si faltan variables críticas o si límites son inválidos.`
- `criterio_de_listo`: `Settings quedan centralizados, tipados y con tests de validación.`

### 3) Definir contratos de respuesta y errores API
- `tarea_id`: `F01-T03`
- `titulo`: `Crear modelos de respuesta mínimos y esquema de error`
- `que_hacer_a_nivel_de_codigo`: `Definir modelos Pydantic para respuesta estándar y errores 400/404/429/500 en app/api/schemas.py; integrar handlers globales de error.`
- `archivos_o_modulos_impactados`:
  - `app/api/schemas.py`
  - `app/core/errors.py`
  - `app/main.py`
  - `tests/api/test_error_contracts.py`
- `dependencias`: `["F01-T01"]`
- `pruebas_unitarias`: `test_error_contract_400_404_429_500 con payload consistente.`
- `respuesta_esperada`: `Los errores expuestos siguen un contrato único y mínimo.`
- `criterio_de_listo`: `No hay respuestas de error ad-hoc fuera del contrato.`

### 4) Configurar timeouts base de request y app lifespan
- `tarea_id`: `F01-T04`
- `titulo`: `Aplicar timeout de request y cierre limpio`
- `que_hacer_a_nivel_de_codigo`: `Agregar middleware de timeout global de request y hooks startup/shutdown para inicializar/terminar recursos.`
- `archivos_o_modulos_impactados`:
  - `app/core/middleware.py`
  - `app/main.py`
  - `tests/core/test_request_timeout.py`
- `dependencias`: `["F01-T02"]`
- `pruebas_unitarias`: `test_request_timeout_returns_controlled_error cuando se supera tiempo límite.`
- `respuesta_esperada`: `Peticiones lentas se cancelan con respuesta controlada sin colgar workers.`
- `criterio_de_listo`: `Timeout de request activo y probado.`
