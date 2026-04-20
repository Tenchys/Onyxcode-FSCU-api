# Conversión UTM a CLP

## Fuente externa
- `https://api.boostr.cl/economy/indicator/utm.json`

## Lógica
- Obtener el valor vigente de UTM.
- Convertir `monto_utm` a pesos chilenos.
- Redondear de forma consistente.

## Reglas
- Cachear el valor UTM con TTL.
- Usar último valor válido si la API externa falla.
- Si no hay cache, fallar de forma controlada.
