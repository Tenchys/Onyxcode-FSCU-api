# Fase 03 — Postgres, repositorio y consulta segura

- `fase_id`: `F03`
- `titulo`: `Postgres, repositorio y consulta segura`
- `objetivo`: `Conectar la API con Postgres usando consulta exacta parametrizada por rut+dv, con solo lectura y timeout estricto.`
- `tipo`: `plan_base`
- `dependencias`: `["F02"]`
- `riesgos`:
  - `Conexión sin límites puede saturar la base.`
  - `Consulta no parametrizada abre riesgo de inyección.`
  - `Ausencia de índice degrada latencia bajo carga.`
- `criterios_de_validacion`:
  - `Toda consulta usa parámetros y nunca SQL dinámico.`
  - `statement_timeout y pool reducido están activos.`
  - `404 cuando no existe rut+dv exacto.`

## Tareas

### 1) Crear capa de conexión a Postgres con pool pequeño
- `tarea_id`: `F03-T01`
- `titulo`: `Implementar cliente DB y límites de pool`
- `que_hacer_a_nivel_de_codigo`: `Crear app/db/postgres.py con engine/pool configurables (mínimo, máximo y timeout de conexión). Aplicar credenciales de solo lectura por entorno.`
- `archivos_o_modulos_impactados`:
  - `app/db/postgres.py`
  - `app/core/settings.py`
  - `tests/db/test_pool_config.py`
- `dependencias`: `["F01-T02", "F01-T04"]`
- `pruebas_unitarias`: `Verificar carga de límites de pool y valores por defecto seguros.`
- `respuesta_esperada`: `Conexión inicializa con límites controlados y sin privilegios de escritura en prod.`
- `criterio_de_listo`: `Pool pequeño parametrizable y validado por tests.`

### 2) Implementar consulta exacta parametrizada rut+dv
- `tarea_id`: `F03-T02`
- `titulo`: `Crear repositorio de deudores con SELECT exacto`
- `que_hacer_a_nivel_de_codigo`: `Crear app/repositories/deudores_repo.py con query fija parametrizada por rut y dv; mapear solo columnas necesarias del dominio.`
- `archivos_o_modulos_impactados`:
  - `app/repositories/deudores_repo.py`
  - `tests/repositories/test_deudores_repo_exact_query.py`
- `dependencias`: `["F03-T01", "F02-T01"]`
- `pruebas_unitarias`: `Validar uso de parámetros, consulta única exacta y mapeo de campos permitidos.`
- `respuesta_esperada`: `El repositorio retorna registro exacto o None.`
- `criterio_de_listo`: `Sin SQL dinámico y sin campos extra expuestos.`

### 3) Integrar statement_timeout en sesión/consulta
- `tarea_id`: `F03-T03`
- `titulo`: `Aplicar timeout estricto a consultas SQL`
- `que_hacer_a_nivel_de_codigo`: `Agregar configuración de statement_timeout en conexión o por sesión antes de ejecutar SELECT.`
- `archivos_o_modulos_impactados`:
  - `app/db/postgres.py`
  - `app/repositories/deudores_repo.py`
  - `tests/db/test_statement_timeout.py`
- `dependencias`: `["F03-T01", "F03-T02"]`
- `pruebas_unitarias`: `Simular consulta lenta y verificar error controlado sin bloquear worker.`
- `respuesta_esperada`: `Consultas fuera de tiempo finalizan con control de error.`
- `criterio_de_listo`: `Timeout SQL efectivo y cubierto por tests.`

### 4) Conectar endpoint con servicio de consulta y errores 404/500
- `tarea_id`: `F03-T04`
- `titulo`: `Orquestar servicio de búsqueda exacta`
- `que_hacer_a_nivel_de_codigo`: `Crear app/services/rut_lookup.py para usar repositorio; devolver 404 cuando no hay coincidencia exacta y 500 controlado en fallas internas.`
- `archivos_o_modulos_impactados`:
  - `app/services/rut_lookup.py`
  - `app/api/v1/rut.py`
  - `tests/services/test_rut_lookup_service.py`
  - `tests/api/test_rut_endpoint_404_500.py`
- `dependencias`: `["F03-T02", "F03-T03", "F02-T03"]`
- `pruebas_unitarias`: `404 no encontrado, 500 controlado ante excepción de infraestructura.`
- `respuesta_esperada`: `Endpoint entrega resultado exacto o error según contrato.`
- `criterio_de_listo`: `Flujo end-to-end exacto operativo con errores mapeados.`

## Cierre de fase

- `estado`: completada
- `fecha`: 2026-04-20
- `resumen`: Se implementó la conexión a Postgres con pool reducido y timeouts estrictos, el repositorio de deudores con consulta parametrizada exacta (rut+dv), el timeout a nivel de sesión SQL, y la orquestación completa endpoint→servicio→repositorio con manejo de 404 y 500 controlado. Se agregaron 23 pruebas unitarias nuevas y se actualizaron los tests existentes que dependían del comportamiento placeholder del endpoint.
- `pruebas_ejecutadas`:
  - tests/db/test_pool_config.py (4 tests)
  - tests/db/test_statement_timeout.py (2 tests)
  - tests/repositories/test_deudores_repo_exact_query.py (9 tests)
  - tests/services/test_rut_lookup_service.py (3 tests)
  - tests/api/test_rut_endpoint_404_500.py (5 tests)
  - tests/api/test_rut_endpoint_validation.py (actualizados con mocks)
- `resultado`: exitoso
- `pendientes`: ninguna
