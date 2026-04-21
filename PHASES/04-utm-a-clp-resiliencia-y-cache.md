# Fase 04 — Conversión UTM a CLP con resiliencia y caché

- `fase_id`: `F04`
- `titulo`: `Conversión UTM a CLP con resiliencia y caché`
- `objetivo`: `Incorporar consumo de API externa de UTM con caché TTL, fallback al último valor válido y fallo controlado cuando no exista caché.`
- `tipo`: `plan_base`
- `dependencias`: `["F03"]`
- `riesgos`:
  - `Dependencia externa inestable afecta disponibilidad.`
  - `Cacheo incorrecto puede retornar valores desactualizados o inconsistentes.`
- `criterios_de_validacion`:
  - `monto_clp se calcula con redondeo consistente.`
  - `Si API externa falla y hay caché, se usa último valor válido.`
  - `Si falla API y no hay caché, respuesta controlada según contrato de error.`

## Tareas

### 1) Implementar cliente HTTP de UTM con timeout dedicado
- `tarea_id`: `F04-T01`
- `titulo`: `Crear adapter para API de UTM`
- `que_hacer_a_nivel_de_codigo`: `Crear app/integrations/utm_client.py con solicitud a fuente oficial, timeout corto y parseo robusto del valor vigente y fecha.`
- `archivos_o_modulos_impactados`:
  - `app/integrations/utm_client.py`
  - `app/core/settings.py`
  - `tests/integrations/test_utm_client.py`
- `dependencias`: `["F01-T02"]`
- `pruebas_unitarias`: `Caso éxito, timeout, payload inválido de proveedor.`
- `respuesta_esperada`: `Cliente entrega valor+fecha o error controlado de integración.`
- `criterio_de_listo`: `Timeout y parseo defensivo implementados.`

### 2) Agregar caché TTL y fallback de último valor válido
- `tarea_id`: `F04-T02`
- `titulo`: `Persistir valor UTM en caché de proceso`
- `que_hacer_a_nivel_de_codigo`: `Crear app/services/utm_cache.py con get/set, expiración TTL y retención del último valor válido para fallback.`
- `archivos_o_modulos_impactados`:
  - `app/services/utm_cache.py`
  - `tests/services/test_utm_cache.py`
- `dependencias`: `["F04-T01"]`
- `pruebas_unitarias`: `Hit/miss de caché, expiración, fallback tras error remoto.`
- `respuesta_esperada`: `Cache reduce llamadas externas y protege ante fallas transitorias.`
- `criterio_de_listo`: `Política TTL/fallback cubierta por tests.`

### 3) Implementar conversor UTM→CLP en servicio de dominio
- `tarea_id`: `F04-T03`
- `titulo`: `Calcular monto_clp con redondeo consistente`
- `que_hacer_a_nivel_de_codigo`: `Crear app/services/money.py para convertir monto_utm a CLP usando Decimal y regla de redondeo definida.`
- `archivos_o_modulos_impactados`:
  - `app/services/money.py`
  - `tests/services/test_money_conversion.py`
- `dependencias`: `["F04-T02"]`
- `pruebas_unitarias`: `Casos de precisión y redondeo para montos representativos.`
- `respuesta_esperada`: `monto_clp determinístico y sin errores de precisión binaria.`
- `criterio_de_listo`: `Conversión estable y reproducible.`

### 4) Integrar conversión y fallback al flujo del endpoint
- `tarea_id`: `F04-T04`
- `titulo`: `Completar respuesta con monto_clp y utm_fecha`
- `que_hacer_a_nivel_de_codigo`: `Actualizar app/services/rut_lookup.py para anexar monto_clp y utm_fecha usando caché+cliente UTM; mapear fallo sin caché a error controlado.`
- `archivos_o_modulos_impactados`:
  - `app/services/rut_lookup.py`
  - `app/api/v1/schemas_rut.py`
  - `tests/services/test_rut_lookup_with_utm.py`
  - `tests/api/test_rut_endpoint_utm_failover.py`
- `dependencias`: `["F04-T03", "F03-T04"]`
- `pruebas_unitarias`: `Éxito completo, fallback con caché, error cuando no hay caché disponible.`
- `respuesta_esperada`: `Endpoint siempre responde campos esperados o error controlado según reglas.`
- `criterio_de_listo`: `Integración UTM operativa con degradación segura.`
