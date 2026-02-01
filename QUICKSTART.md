# ⚡ Quick Start - 5 minutos

Guía ultra-rápida para tener todo funcionando en 5 minutos.

## Pre-requisitos

- Python 3.11+
- Cuenta de Modal (https://modal.com)
- Bot de Telegram

## 1. Instalar

```bash
cd /Users/felipemaldonado/Documents/repositories/Orgappitation
pip install -r requirements.txt
```

## 2. Crear bot de Telegram

1. Abre Telegram
2. Busca: **@BotFather**
3. Envía: `/newbot`
4. Dale un nombre y username
5. **Copia el token** que te da

## 3. Configurar

```bash
# Copiar template
cp .env.example .env

# Editar
nano .env
```

Agrega:
```bash
# Genera API key
FINANZAS_API_KEY=$(openssl rand -hex 32)

# Pega token de Telegram
TELEGRAM_BOT_TOKEN=tu_token_aqui

# Déjalos vacíos por ahora (los llenaremos después del deploy)
MODAL_API_URL=
LLM_API_URL=
```

## 4. Deploy en Modal

```bash
# Login a Modal (primera vez)
modal token new

# Deploy API
modal deploy api/modal_app.py
# Copia la URL que aparece y agrégala a .env como MODAL_API_URL

# Inicializar DB
modal run api/modal_app.py::init_db

# Configurar secret en Modal Dashboard
# Ve a: https://modal.com/secrets
# Crea: "finanzas-api-secret"
# Agrega: FINANZAS_API_KEY=<el valor de tu .env>

# Deploy LLM (tarda 5-10 min la primera vez)
modal deploy llm_service_modal.py
# Copia la URL y agrégala a .env como LLM_API_URL

# Configurar HuggingFace secret
# Ve a: https://huggingface.co/settings/tokens
# Crea token (Read access)
# En Modal: https://modal.com/secrets
# Crea: "huggingface-secret"
# Agrega: HUGGINGFACE_TOKEN=<tu token>
```

## 5. Iniciar bot

```bash
python telegram/bot.py
```

Deberías ver:
```
🤖 Iniciando bot de Telegram...
   🧠 LLM: https://...
✅ Bot iniciado!
```

## 6. Usar

Abre Telegram, busca tu bot y prueba:

```
Gasté 5000 en café
```

El bot debería responder con:
```
🧠 Analizando con LLM...

📝 YAML generado:
monto: 5000
descripcion: café
categoria: food

✅ Registrado exitosamente

💸 Gasto
💰 Monto: $5,000 ARS
📝 Descripción: café
🏷️ Categoría: food
```

## 7. Ver balance

```
/balance
```

Respuesta:
```
💰 Balance Actual

💵 Ingresos: $0 ARS
💸 Gastos: $5,000 ARS
━━━━━━━━━━━━━━━━━
💰 Balance: -$5,000 ARS

📝 Total transacciones: 1
```

## ✅ ¡Listo!

Ya puedes:
- ✅ Registrar gastos en lenguaje natural
- ✅ Ver balance y estadísticas
- ✅ Usar desde tu celular 24/7

## 🔍 Verificar que todo funciona

```bash
# Test API
curl $(grep MODAL_API_URL .env | cut -d'=' -f2)/health

# Test LLM
modal run llm_service_modal.py --text "Gasté 5000 en café"

# Test ingesta manual
python cli/yaml_to_modal.py --yaml "monto: 5000\ndescripcion: Test"

# Ver stats
./cli/finanzas_cli.sh stats
```

## 🐛 Si algo falla

### Bot no responde

1. Verifica que esté corriendo: `ps aux | grep bot.py`
2. Revisa logs en la terminal
3. Verifica `.env`: `cat .env`

### "Invalid API key"

Verifica que el secret en Modal tenga el mismo valor que tu `.env`:

```bash
# Ver tu API key local
grep FINANZAS_API_KEY .env

# Verifica en: https://modal.com/secrets
```

### LLM tarda mucho

Es normal la primera vez (cold start ~30-60s). Después será más rápido.

## 📖 Siguiente paso

Lee la documentación completa:
- [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) - Deploy detallado
- [README.md](README.md) - Documentación completa
- [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md) - Setup avanzado de Telegram

---

Tiempo total: ~5-10 minutos (la mayoría esperando que descargue el LLM)
