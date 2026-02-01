# 🏗️ Arquitectura del Sistema

Diagrama y explicación de cómo funciona el sistema de finanzas.

## 📊 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                    USUARIO (Telegram)                            │
│                                                                   │
│  Escribe: "Gasté 5000 en café"                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             telegram/bot.py (Python Local)                       │
│                                                                   │
│  - Recibe mensaje de Telegram                                    │
│  - Detecta que no es comando (sin /)                            │
│  - Llama al servicio LLM                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP POST
                            │ {"text": "Gasté 5000 en café", "api_key": "..."}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│         llm_service_modal.py (Modal + GPU T4)                    │
│                                                                   │
│  - Recibe texto natural                                          │
│  - Carga modelo: Qwen-2.5-3b-Text_to_SQL (2GB)                 │
│  - Prompt engineering para finanzas                             │
│  - Genera YAML estructurado                                      │
│                                                                   │
│  Output:                                                         │
│  monto: 5000                                                     │
│  descripcion: café                                               │
│  categoria: food                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Returns JSON
                            │ {"yaml_output": "monto: 5000\n...", "success": true}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             telegram/bot.py (Python Local)                       │
│                                                                   │
│  - Recibe YAML del LLM                                          │
│  - Muestra al usuario el YAML generado                          │
│  - Llama a yaml_to_modal.py                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ subprocess
                            │ python cli/yaml_to_modal.py --yaml "..."
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│            cli/yaml_to_modal.py (Python Local)                   │
│                                                                   │
│  - Parsea YAML                                                   │
│  - Valida con Pydantic                                          │
│  - Convierte a JSON                                             │
│  - Agrega defaults (fecha, ID, etc)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP POST
                            │ /ingest
                            │ {"transactions": [...]}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│            api/modal_app.py (Modal FastAPI)                      │
│                                                                   │
│  - Valida API key                                                │
│  - Valida datos con Pydantic                                    │
│  - Inserta en SQLite                                            │
│  - Guarda en Modal Volume (/data/finanzas.db)                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Returns
                            │ {"inserted": 1, "errors": []}
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SQLite (Modal Volume)                         │
│                                                                   │
│  - Persistencia permanente                                       │
│  - Schema optimizado para text-to-SQL                           │
│  - Backups automáticos de Modal                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USUARIO (Telegram)                            │
│                                                                   │
│  Recibe: "✅ Gasto registrado: $5,000 ARS - café"              │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Flujo Alternativo: Comandos Manuales

```
Usuario: "/gastar 5000 Café"
    ↓
telegram/bot.py
    ↓ (Saltea LLM, crea YAML directamente)
cli/yaml_to_modal.py
    ↓
api/modal_app.py
    ↓
SQLite
```

## 🔍 Flujo de Consultas

```
Usuario: "/balance"
    ↓
telegram/bot.py
    ↓ subprocess
cli/finanzas_cli.sh stats
    ↓ HTTP GET /stats
api/modal_app.py
    ↓ SQL Query
SQLite
    ↓ Results
Usuario: "💰 Balance: $X ARS"
```

## 🧩 Componentes

### 1. telegram/bot.py (Local)
**Responsabilidad**: Interfaz de usuario

- Framework: python-telegram-bot
- Ejecuta: Local en tu computadora
- Funciones:
  - Recibe mensajes de Telegram
  - Detecta comandos vs texto libre
  - Llama a LLM para texto libre
  - Llama a CLI para comandos
  - Formatea respuestas al usuario

### 2. llm_service_modal.py (Modal GPU)
**Responsabilidad**: Conversión texto → YAML

- Framework: Modal + llama-cpp-python
- Ejecuta: Modal con GPU T4
- Modelo: Qwen-2.5-3b-Text_to_SQL (Q4_K_M, ~2GB)
- Funciones:
  - Recibe texto natural
  - Aplica prompt engineering
  - Genera YAML estructurado
  - Infiere categorías automáticamente
  - Detecta si es ingreso o gasto

### 3. cli/yaml_to_modal.py (Local)
**Responsabilidad**: Ingesta de datos

- Ejecuta: Local
- Funciones:
  - Parsea YAML
  - Valida con Pydantic
  - Agrega metadata (ID, fecha, etc)
  - Envía a API de Modal
  - Maneja errores

### 4. api/modal_app.py (Modal)
**Responsabilidad**: Persistencia y API

- Framework: FastAPI + SQLite
- Ejecuta: Modal (serverless)
- Funciones:
  - API REST con autenticación
  - CRUD de transacciones
  - Estadísticas y balance
  - Health checks
  - Persistencia en Modal Volume

### 5. SQLite en Modal Volume
**Responsabilidad**: Almacenamiento

- Tipo: SQLite file-based
- Ubicación: `/data/finanzas.db` en Modal Volume
- Schema: Optimizado para text-to-SQL (futuro)
- Backup: Automático por Modal

## 🔐 Seguridad

### Autenticación
```
┌─────────────┐      API Key       ┌──────────────┐
│   Cliente   │ ──────────────────> │  API Modal   │
│ (bot/cli)   │ <────────────────── │              │
└─────────────┘    Auth Success     └──────────────┘
```

- API key compartida entre todos los servicios
- Configurada en `.env` localmente
- Configurada en Modal Secrets para servicios
- Validación en cada request

### Validación de Datos

1. **Pydantic en cliente** (yaml_to_modal.py):
   - Valida formato YAML
   - Valida tipos de datos
   - Aplica defaults

2. **Pydantic en servidor** (modal_app.py):
   - Doble validación
   - Sanitización SQL
   - Previene inyecciones

## 📦 Deployment

### Servicios en Modal

| Servicio | Comando | Costo/día | Latencia |
|----------|---------|-----------|----------|
| API de finanzas | `modal deploy api/modal_app.py` | ~$0.01 | <100ms |
| LLM service | `modal deploy llm_service_modal.py` | ~$0.10 | 2-3s (1era vez: 30-60s) |

### Servicios Locales

| Servicio | Comando | Costo | Requisitos |
|----------|---------|-------|------------|
| Bot Telegram | `python telegram/bot.py` | $0 | Python 3.11+ |
| CLI tools | `python cli/...` | $0 | Python 3.11+ |

## 🔌 Integraciones

### Actual
- ✅ Telegram (bot oficial)
- ✅ Modal (API + LLM)
- ✅ HuggingFace (descarga de modelo)

### Futuro
- ⏭️ OpenClaw (interfaz LLM avanzada)
- ⏭️ Text-to-SQL (Llama local para análisis)
- ⏭️ Dashboard web (FastAPI + React)
- ⏭️ WhatsApp (via OpenClaw)

## 🎯 Ventajas de esta Arquitectura

1. **Desacoplamiento**:
   - Bot puede cambiar sin afectar API
   - LLM es opcional (modo manual funciona sin él)
   - Fácil agregar más interfaces (web, CLI, etc)

2. **Escalabilidad**:
   - Modal escala automáticamente
   - LLM solo se activa cuando se usa
   - Sin servidor que mantener

3. **Costo-eficiencia**:
   - Pay-per-use en Modal
   - Bot local gratis
   - LLM pequeño en GPU barata

4. **Flexibilidad**:
   - Funciona con/sin LLM
   - Comandos + lenguaje natural
   - Fácil agregar nuevas features

## 🔮 Evolución Futura

### Fase 1 (Actual)
```
Telegram → LLM → YAML → API → SQLite
```

### Fase 2 (Próxima)
```
                    ┌─> Text-to-SQL (Llama) ─> Análisis
                    │
Telegram → LLM ─────┼─> YAML ─> API ─> SQLite
                    │
WhatsApp ───────────┘
```

### Fase 3 (Futuro)
```
                    ┌─> Text-to-SQL ─> Análisis
                    │
Telegram ───────────┤
WhatsApp ─> OpenClaw ─> LLM ─> YAML ─> API ─> SQLite
Web Dashboard ──────┤                           │
Siri Shortcuts ─────┘                           │
                                                 ├─> Reportes
                                                 └─> Gráficos
```

## 📊 Métricas

### Latencias típicas
- Comando manual: ~500ms
- Con LLM (warm): ~3s
- Con LLM (cold start): ~45s
- Consultas: ~200ms

### Costos mensuales
- Modal API: ~$0.30
- Modal LLM: ~$3.00
- Total: **~$3.30/mes**

---

Para más detalles técnicos, ver:
- [README.md](README.md) - Overview general
- [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) - Deploy paso a paso
- Código fuente en cada directorio
