# Fase 05 — Seguridad, rate limit y anticoncurrencia

- `fase_id`: `F05`
- `titulo`: `Seguridad, rate limit y anticoncurrencia`
- `objetivo`: `Aplicar controles antiabuso (por IP y RUT), límite global de concurrencia y protección por timeouts para mantener estabilidad.`
- `tipo`: `plan_base`
- `dependencias`: `["F03", "F04"]`
- `riesgos`:
  - `Rate limit mal calibrado bloquea tráfico legítimo.`
  - `Sin control de concurrencia aumenta riesgo de saturación de DB.`
  - `Falta de trazabilidad dificulta detectar abuso.`
- `criterios_de_validacion`:
  - `Exceso de solicitudes devuelve 429 según límites configurados.`
  - `Existe límite global de concurrencia activo.`
  - `Eventos de abuso quedan logueados de forma estructurada.`

## Tareas

### 1) Implementar rate limit por IP
- `tarea_id`: `F05-T01`
- `titulo`: `Agregar middleware de límite por IP`
- `que_hacer_a_nivel_de_codigo`: `Crear app/security/rate_limit.py con ventana temporal y contador por IP; habilitar/deshabilitar vía RATE_LIMIT_ENABLED.`
- `archivos_o_modulos_impactados`:
  - `app/security/rate_limit.py`
  - `app/core/settings.py`
  - `app/main.py`
  - `tests/security/test_rate_limit_ip.py`
- `dependencias`: `["F01-T02", "F03-T04"]`
- `pruebas_unitarias`: `Permitir dentro de cuota y bloquear con 429 al exceder límite por IP.`
- `respuesta_esperada`: `Clientes con exceso de frecuencia son rechazados de forma consistente.`
- `criterio_de_listo`: `Límite por IP configurable y probado.`

### 2) Implementar rate limit por RUT normalizado
- `tarea_id`: `F05-T02`
- `titulo`: `Restringir repetición intensiva sobre mismo RUT`
- `que_hacer_a_nivel_de_codigo`: `Extender app/security/rate_limit.py para bucket por RUT normalizado (rut+dv) y burst controlado.`
- `archivos_o_modulos_impactados`:
  - `app/security/rate_limit.py`
  - `app/api/v1/rut.py`
  - `tests/security/test_rate_limit_rut.py`
- `dependencias`: `["F05-T01", "F02-T01"]`
- `pruebas_unitarias`: `Bloqueo 429 por exceso sobre un mismo RUT, sin afectar RUTs distintos.`
- `respuesta_esperada`: `Se reduce scraping focalizado por identidad.`
- `criterio_de_listo`: `Política por RUT normalizado aplicada sin falsos positivos graves.`

### 3) Agregar límite global de concurrencia
- `tarea_id`: `F05-T03`
- `titulo`: `Controlar solicitudes simultáneas`
- `que_hacer_a_nivel_de_codigo`: `Crear app/security/concurrency_guard.py con semáforo asíncrono global y rechazo controlado cuando se supera capacidad.`
- `archivos_o_modulos_impactados`:
  - `app/security/concurrency_guard.py`
  - `app/main.py`
  - `app/core/settings.py`
  - `tests/security/test_concurrency_guard.py`
- `dependencias`: `["F03-T01", "F01-T04"]`
- `pruebas_unitarias`: `Simular N solicitudes simultáneas y validar límite/rechazo esperado.`
- `respuesta_esperada`: `Carga concurrente no sobrepasa umbral definido.`
- `criterio_de_listo`: `Sistema mantiene estabilidad bajo bursts.`

### 4) Auditar y registrar eventos antiabuso
- `tarea_id`: `F05-T04`
- `titulo`: `Emitir logs de seguridad para 429 y rechazos`
- `que_hacer_a_nivel_de_codigo`: `Integrar logging estructurado en middleware de rate limit/concurrencia con campos IP, rut_normalizado (si existe), motivo y latencia.`
- `archivos_o_modulos_impactados`:
  - `app/core/logging.py`
  - `app/security/rate_limit.py`
  - `app/security/concurrency_guard.py`
  - `tests/security/test_abuse_logging.py`
- `dependencias`: `["F05-T01", "F05-T02", "F05-T03"]`
- `pruebas_unitarias`: `Verificar presencia de campos mínimos en logs de bloqueo.`
- `respuesta_esperada`: `Cada rechazo antiabuso queda trazable para operación.`
- `criterio_de_listo`: `Logs listos para observabilidad y auditoría mínima.`
