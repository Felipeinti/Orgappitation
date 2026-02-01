# 🚀 Setup Guide - Paso a Paso

Esta guía te lleva de cero a tener tu app de finanzas funcionando completamente.

## Prerrequisitos

- Python 3.9+
- Cuenta en Modal.com (gratis)
- (Opcional) Ollama para text-to-SQL

## Paso 1: Setup Local

### 1.1 Clonar e instalar

```bash
cd /ruta/a/tu/proyecto
pip install -r requirements.txt
```

### 1.2 Configurar entorno

```bash
cp .env.example .env
```

Por ahora `.env` estará incompleto - lo completaremos después del deploy.

## Paso 2: Deploy en Modal

### 2.1 Instalar y autenticar Modal

```bash
pip install modal
modal token new
```

Esto abrirá tu navegador. Inicia sesión y autoriza.

### 2.2 Generar y configurar API Key

```bash
# Generar key segura
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia la key generada. Luego crea el secret en Modal:

```bash
modal secret create finanzas-api-secret FINANZAS_API_KEY=TU_KEY_AQUI
```

**Importante**: Reemplaza `TU_KEY_AQUI` con la key que generaste.

Ahora agrega esta key a tu `.env` local:

```bash
echo "FINANZAS_API_KEY=TU_KEY_AQUI" >> .env
```

### 2.3 Desplegar la API

```bash
modal deploy modal_app.py
```

Esto tomará ~1-2 minutos la primera vez. Al finalizar verás:

```
✓ Created web function fastapi-app => https://yourusername--finanzas-api-fastapi-app.modal.run
```

**Copia esta URL** y agrégala a tu `.env`:

```bash
echo "MODAL_API_URL=https://yourusername--finanzas-api-fastapi-app.modal.run" >> .env
```

### 2.4 Inicializar la base de datos

```bash
modal run modal_app.py::init_db
```

Verás:

```
Inicializando base de datos en /data/finanzas.db...
Base de datos inicializada exitosamente!
```

## Paso 3: Verificar que funciona

### 3.1 Health check

```bash
curl $(grep MODAL_API_URL .env | cut -d '=' -f2)/health
```

Deberías ver:

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "..."
}
```

### 3.2 Agregar tu primera transacción

```bash
echo "monto: 100
descripcion: Primera transacción de test
categoria: test" | python yaml_to_modal.py --stdin --verbose
```

Verás:

```
🔄 Convirtiendo YAML a JSON...
✅ JSON generado:
{
  "amount": 100.0,
  "currency": "ARS",
  "description": "Primera transacción de test",
  "category": "test",
  "is_income": false
}

📤 Enviando a Modal API...
✅ Respuesta de Modal:
{
  "id": "...",
  "success": true,
  "message": "Transacción creada exitosamente"
}
```

### 3.3 Ver estadísticas

Obtén tu API key del `.env`:

```bash
export FINANZAS_API_KEY=$(grep FINANZAS_API_KEY .env | cut -d '=' -f2)
export MODAL_API_URL=$(grep MODAL_API_URL .env | cut -d '=' -f2)

curl "$MODAL_API_URL/stats" \
  -H "X-API-Key: $FINANZAS_API_KEY"
```

Verás:

```json
{
  "total_income": 0.0,
  "total_expenses": 100.0,
  "balance": -100.0,
  "total_transactions": 1,
  "expense_count": 1,
  "income_count": 0
}
```

## Paso 4: Setup Text-to-SQL (Opcional pero recomendado)

### 4.1 Instalar Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows:**
Descarga desde [ollama.ai](https://ollama.ai)

### 4.2 Iniciar Ollama

```bash
ollama serve
```

Deja esto corriendo en una terminal.

### 4.3 Descargar modelo

En otra terminal:

```bash
ollama pull llama3.2
```

Esto descarga ~2GB.

### 4.4 Instalar librería Python

```bash
pip install ollama
```

### 4.5 Probar text-to-SQL

```bash
python text_to_sql.py "¿Cuánto gasté en total?" --verbose
```

Deberías ver:

```
🤔 Pregunta: ¿Cuánto gasté en total?

🔍 SQL generado:
SELECT SUM(amount) as total FROM transactions WHERE is_income = 0

📡 Ejecutando query en Modal...

total
-----
100.0

1 row(s) returned
```

## Paso 5: Migrar datos existentes (Si aplica)

Si ya tienes transacciones en el CSV viejo:

```bash
python migrate_csv_to_sql.py --csv data/transacciones.csv --upload
```

## Paso 6: Testing (Opcional)

```bash
# Instalar pytest si no lo tienes
pip install pytest

# Correr tests
pytest -v
```

## Resumen de archivos importantes

Después del setup, tendrás:

```
.env                    # Configuración local (NO COMMITEAR)
  ├─ MODAL_API_URL      # URL de tu API en Modal
  └─ FINANZAS_API_KEY   # Tu API key

Modal (nube)
  ├─ finanzas-api       # Tu aplicación desplegada
  ├─ finanzas-data      # Volume con SQLite
  └─ finanzas-api-secret # Secret con API key
```

## Próximos pasos

✅ **Setup completado!** Ahora puedes:

1. **Agregar transacciones**:
   ```bash
   python yaml_to_modal.py --file mis_gastos.yaml
   ```

2. **Hacer preguntas**:
   ```bash
   python text_to_sql.py "¿Cuánto gasté este mes en comida?"
   ```

3. **Ver dashboards** (próximamente)

4. **Integrar con OpenClaw** - Ver README.md sección "Integración con OpenClaw"

## Troubleshooting común

### "modal: command not found"

```bash
pip install modal
```

### "Secret not found"

```bash
modal secret list
# Si no ves finanzas-api-secret, créalo:
modal secret create finanzas-api-secret FINANZAS_API_KEY=tu_key
```

### "Connection refused" en text_to_sql.py

Ollama no está corriendo:

```bash
ollama serve
```

### "Model not found: llama3.2"

```bash
ollama pull llama3.2
```

### La API responde 401 Unauthorized

Verifica que:
1. `FINANZAS_API_KEY` en `.env` es correcta
2. La misma key está en Modal Secret
3. Estás pasando la key en el header `X-API-Key`

## ¿Necesitas ayuda?

- Revisa [DEPLOYMENT.md](DEPLOYMENT.md) para más detalles
- Revisa [README.md](README.md) para documentación completa
- Corre `pytest -v` para verificar que todo funciona

---

🎉 **¡Felicitaciones!** Tu app de finanzas está lista para usar.
