# Fase 07 — Bootstrap declarativo de Postgres con SQL inicial en primer arranque

- `fase_id`: `F07`
- `titulo`: `Bootstrap declarativo de Postgres con SQL inicial en primer arranque`
- `objetivo`: `Cargar automáticamente SQL/deudores_morosos.sql solo cuando el volumen de Postgres esté vacío, usando /docker-entrypoint-initdb.d/, sin tocar la lógica de consultas de la API.`
- `tipo`: `extender_plan`
- `dependencias`: `["F01", "F02"]`
- `riesgos`:
  - `Montar el seed en una ruta incorrecta impediría el bootstrap automático.`
  - `Cambiar el volumen persistente podría provocar recargas no deseadas.`
  - `Tocar la lógica de la API mezclaría infraestructura con dominio.`
- `criterios_de_validacion`:
  - `El compose monta el SQL en /docker-entrypoint-initdb.d/ en modo solo lectura.`
  - `La carga ocurre solo en el primer arranque con data directory vacío.`
  - `Los tests de configuración cubren el contrato de bootstrap.`

## Tareas

### 1) Montar el SQL como init script oficial de Postgres
- `tarea_id`: `F07-T01`
- `titulo`: `Declarar seed inicial en docker-compose`
- `que_hacer_a_nivel_de_codigo`: `Editar docker-compose.yml para montar ./SQL/deudores_morosos.sql en /docker-entrypoint-initdb.d/01-deudores_morosos.sql:ro dentro del servicio postgres, manteniendo postgres_data como volumen persistente.`
- `archivos_o_modulos_impactados`:
  - `docker-compose.yml`
  - `tests/deploy/test_compose_config.py`
- `dependencias`: `[]`
- `pruebas_unitarias`: `Validar por parseo YAML que el servicio postgres conserva el volumen persistente y agrega el mount read-only al directorio oficial de init.`
- `respuesta_esperada`: `Postgres ejecuta el SQL automáticamente solo cuando el volumen está vacío.`
- `criterio_de_listo`: `El bootstrap queda declarativo, reproducible y sin código adicional.`

### 2) Proteger el contrato de primer arranque
- `tarea_id`: `F07-T02`
- `titulo`: `Agregar prueba de contrato para bootstrap one-shot`
- `que_hacer_a_nivel_de_codigo`: `Crear un test de infraestructura que verifique la coexistencia de postgres_data con el mount en /docker-entrypoint-initdb.d/ y deje explícito que el patrón corresponde a inicialización de primer arranque, no a recarga continua.`
- `archivos_o_modulos_impactados`:
  - `tests/deploy/test_compose_init_seed_contract.py`
- `dependencias`: `["F07-T01"]`
- `pruebas_unitarias`: `Afirmar que el seed existe, se monta en la ruta oficial y se mantiene la persistencia del volumen.`
- `respuesta_esperada`: `El repositorio detecta regresiones que rompan el bootstrap inicial.`
- `criterio_de_listo`: `El comportamiento de carga inicial queda cubierto por tests.`

## Cierre de fase

- `estado`: completada
- `fecha`: 2026-04-21
- `resumen`: Se agregó el mount declarativo del seed SQL en /docker-entrypoint-initdb.d/01-deudores_morosos.sql:ro y se cubrió con tests de contrato que validan mount read-only, coexistencia con postgres_data y patrón one-shot de primer arranque.
- `pruebas_ejecutadas`:
  - tests/deploy/test_compose_config.py::TestDockerComposeConfig::test_postgres_init_script_mount_readonly
  - tests/deploy/test_compose_config.py::TestDockerComposeConfig::test_postgres_persistent_volume_preserved
  - tests/deploy/test_compose_init_seed_contract.py::TestInitSeedContract::test_seed_file_exists
  - tests/deploy/test_compose_init_seed_contract.py::TestInitSeedContract::test_seed_file_not_empty
  - tests/deploy/test_compose_init_seed_contract.py::TestInitSeedContract::test_compose_declares_init_mount
  - tests/deploy/test_compose_init_seed_contract.py::TestInitSeedContract::test_init_mount_is_readonly
  - tests/deploy/test_compose_init_seed_contract.py::TestInitSeedContract::test_persistent_volume_coexists_with_init_mount
  - tests/deploy/test_compose_init_seed_contract.py::TestInitSeedContract::test_init_script_naming_convention
- `resultado`: exitoso
- `pendientes`: ninguna
