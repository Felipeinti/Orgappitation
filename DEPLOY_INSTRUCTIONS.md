# 🚀 Instrucciones de Deploy - Finanzas con LLM

Guía rápida para deployar todo el sistema.

## 📦 Requisitos

```bash
pip install -r requirements.txt
```

Necesitarás:
- ✅ Cuenta de Modal
- ✅ Bot de Telegram (vía @BotFather)
- ✅ Ollama (opcional, solo para text-to-SQL)

---

## 1️⃣ Deployar API de Base de Datos

La API de finanzas maneja toda la persistencia de datos.

### Deploy

```bash
cd /Users/felipemaldonado/Documents/repositories/Orgappitation

# Deploy de la API
modal deploy api/modal_app.py
```

Esto te dará una URL como:
```
https://felipeintimaldonado--finanzas-api-fastapi-app.modal.run
```

### Inicializar Base de Datos

```bash
modal run api/modal_app.py::init_db
```

Deberías ver:
```
✅ Base de datos inicializada exitosamente!
```

---

## 2️⃣ Deployar Servicio LLM

El LLM convierte texto natural a YAML.

### Configurar Secrets

Necesitas un secret de HuggingFace (para descargar el modelo):

```bash
# Crear secret en Modal dashboard
# https://modal.com/secrets

# Nombre: huggingface-secret
# Variable: HUGGINGFACE_TOKEN=tu_token_aqui
```

Para obtener token de HuggingFace:
1. Ve a https://huggingface.co/settings/tokens
2. Crea un token nuevo (Read access es suficiente)
3. Copia el token

### Deploy

```bash
modal deploy llm_service_modal.py
```

**IMPORTANTE:** El primer deploy tarda ~5-10 minutos porque descarga el modelo (3GB).

Esto te dará una URL como:
```
https://felipeintimaldonado--finanzas-llm-text-to-yaml-endpoint.modal.run
```

### Probar el LLM

```bash
modal run llm_service_modal.py --text "Gasté 5000 en café"
```

Deberías ver:
```
🧠 Procesando: Gasté 5000 en café

✅ YAML generado:
──────────────────────────────────────────────────
monto: 5000
descripcion: café
categoria: food
──────────────────────────────────────────────────
```

---

## 3️⃣ Configurar Variables de Entorno

Crea/actualiza tu `.env`:

```bash
cd /Users/felipemaldonado/Documents/repositories/Orgappitation

cat > .env << 'EOF'
# API de finanzas
MODAL_API_URL=https://felipeintimaldonado--finanzas-api-fastapi-app.modal.run
FINANZAS_API_KEY=tu_api_key_secreta_aqui

# LLM service
LLM_API_URL=https://felipeintimaldonado--finanzas-llm-text-to-yaml-endpoint.modal.run

# Bot de Telegram
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
EOF
```

**Reemplaza:**
- `MODAL_API_URL` con la URL del paso 1
- `LLM_API_URL` con la URL del paso 2
- `FINANZAS_API_KEY` genera una contraseña segura (usa: `openssl rand -hex 32`)
- `TELEGRAM_BOT_TOKEN` obtén de @BotFather en Telegram

---

## 4️⃣ Iniciar Bot de Telegram

```bash
python telegram/bot.py
```

Deberías ver:
```
🤖 Iniciando bot de Telegram...
   Token: 123456789:...
   🧠 LLM: https://felipeintimaldonado--finanzas...
✅ Bot iniciado!
   Busca tu bot en Telegram y envía /start
```

### Probar

1. Abre Telegram
2. Busca tu bot (el username que le pusiste)
3. Envía: `/start`
4. Prueba lenguaje natural: "Gasté 5000 en café"
5. Prueba comandos: `/balance`

---

## 🔍 Verificar que todo funciona

### Test API de finanzas

```bash
curl https://tu-url--finanzas-api-fastapi-app.modal.run/health
```

Respuesta esperada:
```json
{"status":"healthy","database":"connected"}
```

### Test LLM

```bash
curl -X POST https://tu-url--finanzas-llm-text-to-yaml-endpoint.modal.run \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Gasté 5000 en café",
    "api_key": "tu_api_key"
  }'
```

Respuesta esperada:
```json
{
  "yaml_output": "monto: 5000\ndescripcion: café\ncategoria: food",
  "success": true,
  "error": null
}
```

### Test ingesta manual

```bash
python cli/yaml_to_modal.py --yaml "monto: 5000
descripcion: Test desde CLI
categoria: other"
```

### Ver estadísticas

```bash
./cli/finanzas_cli.sh stats
```

---

## 🐛 Troubleshooting

### "modal-http: app for invoked web endpoint is stopped"

Usaste `modal run` en vez de `modal deploy`. Usa:
```bash
modal deploy api/modal_app.py
```

### "Invalid API key"

Verifica que el `FINANZAS_API_KEY` en `.env` sea el mismo que configuraste en Modal:
```bash
# Ver secrets en Modal
modal secret list
```

### "ModuleNotFoundError"

Reinstala dependencias:
```bash
pip install -r requirements.txt
```

### Bot no responde

1. Verifica que el bot esté corriendo: `ps aux | grep bot.py`
2. Revisa logs en la terminal donde corre
3. Verifica `.env` con: `cat .env`
4. Prueba comandos manuales primero: `/gastar 5000 Test`

### LLM tarda mucho / timeout

Es normal la primera vez (cold start). Modal tarda ~30-60s en levantar el contenedor con GPU.

Para evitarlo, puedes configurar `min_containers=1` en `llm_service_modal.py`:

```python
@app.cls(
    ...
    min_containers=1,  # Mantener siempre 1 contenedor caliente
)
```

**⚠️ CUIDADO:** Esto consume créditos de Modal constantemente (~$0.40/hora con GPU T4).

---

## 💰 Costos estimados (Modal)

- **API de finanzas**: ~$0.01/día (prácticamente gratis)
- **LLM (sin contenedor caliente)**: ~$0.10/día (solo cuando usas)
- **LLM (con contenedor caliente)**: ~$9.60/día ($0.40/hora × 24h)

**Recomendación**: Deja LLM sin contenedor caliente (`min_containers=0`). El cold start de 30s es tolerable para uso personal.

---

## 📂 Estructura del Proyecto

```
/
├── api/                    # API de base de datos (Modal)
│   ├── modal_app.py        # Deploy: modal deploy api/modal_app.py
│   └── sql_schema.sql
│
├── llm_service_modal.py    # LLM service (Modal)
│                           # Deploy: modal deploy llm_service_modal.py
│
├── telegram/               # Bot de Telegram
│   └── bot.py              # Run: python telegram/bot.py
│
├── cli/                    # Herramientas CLI
│   ├── yaml_to_modal.py    # Ingesta manual
│   └── finanzas_cli.sh     # Wrapper para stats/balance
│
├── models/                 # Modelos Pydantic
├── scripts/                # Scripts auxiliares (migración, text-to-SQL)
├── tests/                  # Tests
├── docs/                   # Documentación
├── examples/               # Ejemplos YAML
└── .env                    # Variables de entorno
```

---

## 🎯 Flujo completo

```
Usuario escribe en Telegram: "Gasté 5000 en café"
           ↓
telegram/bot.py (Python local)
           ↓
llm_service_modal.py (Modal con GPU)
  - Qwen-2.5-3b genera YAML
           ↓
telegram/bot.py recibe YAML
           ↓
cli/yaml_to_modal.py (Python local)
           ↓
api/modal_app.py (Modal FastAPI)
  - Valida con Pydantic
  - Guarda en SQLite (Modal Volume)
           ↓
Respuesta al usuario: "✅ Gasto registrado: $5,000 ARS"
```

---

## 🚦 Próximos pasos

Una vez que todo funcione:

1. ✅ Usa el bot diariamente desde Telegram
2. ✅ Monitorea costos en Modal dashboard
3. ✅ Ajusta `min_containers` según necesites
4. ⏭️ Implementa text-to-SQL para análisis (futuro)
5. ⏭️ Agrega más categorías y validaciones (futuro)

---

## 📞 Comandos útiles

```bash
# Ver apps deployadas
modal app list

# Ver logs de API
modal app logs finanzas-api

# Ver logs de LLM
modal app logs finanzas-llm

# Detener apps
modal app stop finanzas-api
modal app stop finanzas-llm

# Ver consumo
modal account usage
```
