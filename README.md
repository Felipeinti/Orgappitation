# 💰 Finanzas Personales con LLM

Sistema de finanzas personales con ingesta inteligente mediante LLM y bot de Telegram.

## ✨ Características

- 🤖 **Ingesta con LLM**: Escribe "Gasté 5000 en café" y el LLM extrae los datos automáticamente
- 📱 **Bot de Telegram**: Registra gastos desde tu celular en lenguaje natural
- 🗄️ **Base de datos SQL**: Almacenamiento persistente optimizado para consultas
- ☁️ **100% Serverless**: Deployado en Modal (API + LLM con GPU)
- 🔒 **Seguro**: Autenticación con API keys
- 📊 **Análisis**: Balance, estadísticas y métricas en tiempo real

## 🚀 Quick Start

Tienes 2 opciones: **Modal (en la nube)** o **Local (en tu compu)**.

### Opción A: Deploy en Modal (Recomendado)

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Configurar .env
cp .env.example .env
nano .env  # Agregar tokens

# 3. Deploy
modal deploy api/modal_app.py
modal deploy llm_service_modal.py

# 4. Iniciar bot
python telegram/bot.py
```

Ver: [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) para guía completa.

### Opción B: Deploy Local (Gratis, privado)

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Configurar .env
cp .env.example .env
# Cambiar LLM_API_URL=http://127.0.0.1:8001/text_to_yaml
nano .env

# 3. Iniciar LLM local
python llm_service_local.py

# 4. Iniciar bot (otra terminal)
python telegram/bot.py
```

Ver: [LOCAL_DEPLOYMENT.md](LOCAL_DEPLOYMENT.md) para guía completa.

### Usar desde Telegram

Abre Telegram, busca tu bot y escribe:

```
Gasté 5000 en café
```

El LLM procesará el mensaje y lo guardará automáticamente.

## 📖 Documentación Completa

### Deployment
- ☁️ **[DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)** - Deploy en Modal (cloud)
- 🏠 **[LOCAL_DEPLOYMENT.md](LOCAL_DEPLOYMENT.md)** - Deploy local (gratis)
- 🚀 **[QUICKSTART.md](QUICKSTART.md)** - Inicio rápido (5 min)

### Uso
- 📱 **[docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md)** - Setup del bot
- 🗑️ **[docs/DELETE_GUIDE.md](docs/DELETE_GUIDE.md)** - Borrar datos
- 🦞 **[docs/OPENCLAW_INTEGRATION.md](docs/OPENCLAW_INTEGRATION.md)** - OpenClaw

### Arquitectura
- 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Diagramas y explicación técnica

## 📂 Estructura del Proyecto

```
/
├── api/                    # API de base de datos (Modal)
│   ├── modal_app.py        # FastAPI app con SQLite
│   └── sql_schema.sql      # Schema optimizado
│
├── llm_service_modal.py    # Servicio LLM (Qwen-2.5-3b)
│
├── telegram/               # Bot de Telegram
│   └── bot.py              # Bot con soporte LLM
│
├── cli/                    # Herramientas CLI
│   ├── yaml_to_modal.py    # Ingesta manual YAML→API
│   └── finanzas_cli.sh     # Wrapper para comandos
│
├── models/                 # Modelos Pydantic
│   └── models.py
│
├── scripts/                # Scripts auxiliares
│   ├── migrate_csv_to_sql.py    # Migración CSV→SQL
│   └── text_to_sql.py           # Text-to-SQL (futuro)
│
├── tests/                  # Tests
├── docs/                   # Documentación
├── examples/               # Ejemplos YAML
└── legacy/                 # Código antiguo (CSV)
```

## 🎯 Flujo de Datos

```
Usuario (Telegram): "Gasté 5000 en café"
          ↓
Bot de Telegram (Python local)
          ↓
LLM Service (Modal GPU - Qwen-2.5-3b)
          ↓ YAML
yaml_to_modal.py (Python local)
          ↓ JSON
API de Finanzas (Modal FastAPI)
          ↓
SQLite (Modal Volume)
```

## 📱 Uso del Bot

### Lenguaje Natural (con LLM)

Simplemente escribe:

```
Gasté 5000 en café
Pagué 45000 de alquiler
Me llegó el sueldo de 200000
Compré comida por 12000
```

El LLM entiende y extrae:
- **Monto** (obligatorio)
- **Descripción** (opcional)
- **Categoría** (inferida): food, housing, transport, etc
- **Tipo** (inferido): gasto vs ingreso

### Comandos Manuales

```
/gastar 5000 Café          - Registrar gasto
/ingreso 50000 Sueldo      - Registrar ingreso
/balance                   - Ver balance
/stats                     - Ver estadísticas
/limpiar                   - Borrar todo
/help                      - Ayuda
```

## 🔧 Desarrollo Local

### Ejecutar tests

```bash
pytest tests/
```

### Probar LLM localmente

```bash
modal run llm_service_modal.py --text "Gasté 5000 en café"
```

### Ingesta manual

```bash
# Desde YAML
python cli/yaml_to_modal.py --file examples/ejemplo_transacciones.yaml

# Desde string
python cli/yaml_to_modal.py --yaml "monto: 5000
descripcion: Test"

# Desde stdin
echo "monto: 5000" | python cli/yaml_to_modal.py --stdin
```

### Ver estadísticas

```bash
./cli/finanzas_cli.sh stats
./cli/finanzas_cli.sh balance
```

## 🧠 Sobre el LLM

Usamos **Qwen-2.5-3b-Text_to_SQL** (quantizado Q4_K_M):

- ✅ Pequeño (~2GB)
- ✅ Rápido (~2-3s en GPU T4)
- ✅ Bueno para extraer datos estructurados
- ✅ Corre en Modal con GPU barata

**Prompt engineering**: El prompt está optimizado para finanzas personales y categorización automática.

## 💰 Costos

### Opción 1: Modal (en la nube)
- **API de finanzas**: ~$0.01/día
- **LLM (on-demand)**: ~$0.10/día
- **Total**: ~$3.30/mes

### Opción 2: Local (gratis)
- **Todo**: $0/mes
- Requiere: GPU recomendada (o CPU potente)

## 🛡️ Seguridad

- ✅ API key authentication
- ✅ SQL injection protection (Pydantic validation)
- ✅ Rate limiting (Modal)
- ✅ Environment variables para secrets
- ⚠️ Text-to-SQL en modo read-only (cuando se implemente)

## 🔜 Roadmap

- [ ] Text-to-SQL con Llama para análisis ("¿Cuánto gasté en comida?")
- [ ] Dashboard web con visualizaciones
- [ ] Soporte multi-moneda real (USD, CAD, etc)
- [ ] Reportes mensuales automáticos
- [ ] Integración con OpenClaw completa
- [ ] Exportar a CSV/Excel
- [ ] Recordatorios de gastos recurrentes

## 🤝 Contribuir

1. Fork el repo
2. Crea branch: `git checkout -b feature/nueva-feature`
3. Commit: `git commit -m "Agrega nueva feature"`
4. Push: `git push origin feature/nueva-feature`
5. Pull request

## 📝 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

## 💬 Soporte

- 📖 [Documentación completa](docs/)
- 🐛 [Reportar bug](https://github.com/tu-usuario/finanzas/issues)
- 💡 [Sugerir feature](https://github.com/tu-usuario/finanzas/issues)

---

Hecho con ❤️ y mucho ☕
