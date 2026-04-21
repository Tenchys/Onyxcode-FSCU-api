# Fase 02 — Dominio RUT y endpoint de consulta exacta

- `fase_id`: `F02`
- `titulo`: `Dominio RUT y endpoint de consulta exacta`
- `objetivo`: `Implementar validación/normalización estricta de RUT y exponer GET /v1/rut/{rut} sin búsquedas parciales.`
- `tipo`: `plan_base`
- `dependencias`: `["F01"]`
- `riesgos`:
  - `Validación incompleta permite entradas ambiguas o inválidas.`
  - `Diseño de endpoint podría habilitar variantes de búsqueda no permitidas.`
- `criterios_de_validacion`:
  - `Solo se acepta formato de RUT válido; inválidos retornan 400.`
  - `No existen parámetros para listado, paginación ni búsqueda parcial.`

## Tareas

### 1) Implementar validador y normalizador de RUT
- `tarea_id`: `F02-T01`
- `titulo`: `Crear módulo de validación de RUT chileno`
- `que_hacer_a_nivel_de_codigo`: `Crear app/domain/rut.py con parse_rut(), normalizar y validar dígito verificador. Exponer resultado normalizado (rut_numérico + dv).`
- `archivos_o_modulos_impactados`:
  - `app/domain/rut.py`
  - `tests/domain/test_rut.py`
- `dependencias`: `["F01-T02"]`
- `pruebas_unitarias`: `Casos válidos/inválidos, DV en mayúscula/minúscula, formatos con y sin puntos/guion.`
- `respuesta_esperada`: `Entradas válidas se normalizan; inválidas levantan error de dominio.`
- `criterio_de_listo`: `Cobertura de reglas de formato y DV completa.`

### 2) Definir schema de salida del endpoint principal
- `tarea_id`: `F02-T02`
- `titulo`: `Modelar respuesta de consulta RUT`
- `que_hacer_a_nivel_de_codigo`: `Crear modelo response con campos: found, rut, dv, nombre, universidad, monto_utm, monto_clp, utm_fecha; restringir campos extra.`
- `archivos_o_modulos_impactados`:
  - `app/api/v1/schemas_rut.py`
  - `tests/api/test_rut_response_schema.py`
- `dependencias`: `["F01-T03"]`
- `pruebas_unitarias`: `Validar presencia/ausencia exacta de campos y tipos esperados.`
- `respuesta_esperada`: `Respuesta mínima sin sobreexposición de datos.`
- `criterio_de_listo`: `Contrato de salida alineado al contexto del proyecto.`

### 3) Implementar router GET /v1/rut/{rut}
- `tarea_id`: `F02-T03`
- `titulo`: `Crear endpoint principal con validación temprana`
- `que_hacer_a_nivel_de_codigo`: `Agregar app/api/v1/rut.py con endpoint GET /v1/rut/{rut}; validar RUT antes de acceder a servicios; mapear errores de validación a 400.`
- `archivos_o_modulos_impactados`:
  - `app/api/v1/rut.py`
  - `app/main.py`
  - `tests/api/test_rut_endpoint_validation.py`
- `dependencias`: `["F02-T01", "F02-T02"]`
- `pruebas_unitarias`: `400 por formato inválido; no invocar repositorio cuando falla validación.`
- `respuesta_esperada`: `Endpoint rechaza entradas inválidas y mantiene flujo exacto.`
- `criterio_de_listo`: `Endpoint funcional sin lógica de búsqueda parcial.`

### 4) Blindar contrato para impedir listados masivos
- `tarea_id`: `F02-T04`
- `titulo`: `Agregar pruebas negativas de no-listado/no-búsqueda-libre`
- `que_hacer_a_nivel_de_codigo`: `Crear tests de rutas inexistentes o parámetros no soportados para confirmar que no existen endpoints masivos ni filtros libres.`
- `archivos_o_modulos_impactados`:
  - `tests/api/test_no_massive_or_partial_search.py`
- `dependencias`: `["F02-T03"]`
- `pruebas_unitarias`: `404/405 para intentos de listado y ausencia de query params de búsqueda parcial.`
- `respuesta_esperada`: `La API mantiene únicamente consulta exacta por path param.`
- `criterio_de_listo`: `No hay superficie accidental para scraping por listados.`
