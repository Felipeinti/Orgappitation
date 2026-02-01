# 🚀 Guía de Deployment en Modal

Esta guía explica cómo desplegar la API de finanzas en Modal paso a paso.

## Prerequisitos

1. **Cuenta en Modal**: Regístrate en [modal.com](https://modal.com)
2. **Python 3.9+**: Verifica con `python --version`
3. **Modal CLI instalado**: `pip install modal`

## Paso 1: Configurar Modal

### 1.1 Instalar Modal CLI

```bash
pip install modal
```

### 1.2 Autenticarte en Modal

```bash
modal token new
```

Esto abrirá tu navegador y te pedirá que inicies sesión. Una vez completado, tu token quedará guardado localmente.

### 1.3 Verificar autenticación

```bash
modal profile current
```

Deberías ver tu username de Modal.

## Paso 2: Crear el Secret en Modal

La API necesita una API key para autenticación. Debes crear un "Secret" en Modal con esta key.

### 2.1 Generar una API key segura

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Guarda esta key, la necesitarás.

### 2.2 Crear el Secret en Modal

```bash
modal secret create finanzas-api-secret FINANZAS_API_KEY=tu_api_key_aqui
```

Reemplaza `tu_api_key_aqui` con la key que generaste.

**Importante**: Guarda esta API key en tu archivo `.env` local también:

```bash
echo "FINANZAS_API_KEY=tu_api_key_aqui" >> .env
```

## Paso 3: Desplegar la API

### 3.1 Desplegar

```bash
modal deploy modal_app.py
```

Este comando:
1. Construye la imagen Docker con todas las dependencias
2. Crea el Volume para SQLite si no existe
3. Despliega la aplicación en Modal
4. Te muestra la URL de la API

### 3.2 Guardar la URL

Después del deploy, verás algo como:

```
✓ Created web function fastapi-app => https://yourusername--finanzas-api-fastapi-app.modal.run
```

**Copia esta URL** y agrégala a tu `.env`:

```bash
echo "MODAL_API_URL=https://yourusername--finanzas-api-fastapi-app.modal.run" >> .env
```

## Paso 4: Inicializar la base de datos

La primera vez que despliegas, necesitas inicializar la base de datos con el schema:

```bash
modal run modal_app.py::init_db
```

Esto ejecuta el script de inicialización que crea todas las tablas.

## Paso 5: Verificar que funciona

### 5.1 Health check

```bash
curl https://yourusername--finanzas-api-fastapi-app.modal.run/health
```

Deberías ver:

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-01-31T..."
}
```

### 5.2 Probar inserción de transacción

```bash
curl -X POST https://yourusername--finanzas-api-fastapi-app.modal.run/ingest \
  -H "X-API-Key: tu_api_key_aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100,
    "description": "Test transaction",
    "category": "test"
  }'
```

### 5.3 Ver estadísticas

```bash
curl https://yourusername--finanzas-api-fastapi-app.modal.run/stats \
  -H "X-API-Key: tu_api_key_aqui"
```

## Paso 6: Migrar datos existentes (opcional)

Si ya tienes transacciones en CSV, mígralas:

```bash
python migrate_csv_to_sql.py --csv data/transacciones.csv --upload
```

## Gestión de la aplicación

### Ver logs

```bash
modal app logs finanzas-api
```

### Pausar el servicio (para no consumir créditos)

```bash
modal app stop finanzas-api
```

### Reanudar el servicio

```bash
modal app start finanzas-api
```

### Ver volúmenes (datos persistentes)

```bash
modal volume list
```

### Ver detalles de un volumen

```bash
modal volume get finanzas-data
```

### Descargar backup de la base de datos

```bash
modal volume get finanzas-data finanzas.db --output backup.db
```

## Actualizar la aplicación

Cuando hagas cambios en `modal_app.py`:

```bash
modal deploy modal_app.py
```

Modal automáticamente:
1. Construye una nueva versión
2. La despliega sin downtime
3. Mantiene los datos en el Volume

## Costos y límites

### Tier Gratuito de Modal

- **30 créditos/mes gratis**
- 1 crédito ≈ 1 GPU-hora o ~10 CPU-horas
- La API usa CPU, muy económico

### Optimizaciones

- `keep_warm=1`: Mantiene 1 contenedor activo para respuestas rápidas
  - Consume ~0.1 créditos/día
  - Vale la pena para buena UX
- Si necesitas ahorrar más: `keep_warm=0`
  - Primera request tarda ~3-5 segundos (cold start)
  - Luego es rápido por ~5 minutos

### Pausar cuando no uses

```bash
# Antes de dormir o si no usarás por días
modal app stop finanzas-api

# Cuando vuelvas
modal app start finanzas-api
```

El Volume (datos) persiste incluso cuando la app está pausada.

## Troubleshooting

### Error: "Secret not found"

```bash
# Verificar secrets
modal secret list

# Recrear secret
modal secret create finanzas-api-secret FINANZAS_API_KEY=nueva_key
```

### Error: "Volume not found"

```bash
# Listar volumes
modal volume list

# Crear manualmente
modal volume create finanzas-data
```

### Error de autenticación en requests

Verifica que:
1. La API key en el header `X-API-Key` sea correcta
2. La API key en Modal Secret sea la misma que usas localmente

### La base de datos está vacía

```bash
# Reinicializar
modal run modal_app.py::init_db

# Migrar datos
python migrate_csv_to_sql.py --csv data/transacciones.csv --upload
```

## Integración con OpenClaw

Una vez desplegada la API, puedes usarla desde OpenClaw:

```bash
# Agregar transacción desde YAML
echo "monto: 5000
descripcion: Cena
categoria: food" | python yaml_to_modal.py --stdin
```

Para integración completa con OpenClaw/Telegram, consulta la sección de OpenClaw en el README.

## Monitoreo

### Dashboard de Modal

Visita [modal.com/apps](https://modal.com/apps) para ver:
- Requests por segundo
- Latencia
- Errores
- Uso de créditos

### Logs en tiempo real

```bash
modal app logs finanzas-api --follow
```

### Alertas (opcional)

Puedes configurar alertas en el dashboard de Modal para:
- Alto uso de créditos
- Errores frecuentes
- Latencia alta

## Siguiente paso

Una vez que la API esté funcionando:

1. ✅ Probar ingesta con `yaml_to_modal.py`
2. ✅ Configurar text-to-SQL con Llama local
3. ✅ Integrar con OpenClaw
4. ✅ Configurar APIs de precios (ETH, USD)

¡Tu API de finanzas ya está en la nube! 🎉
