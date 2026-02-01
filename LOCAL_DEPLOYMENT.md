# 🏠 Deployment Local - Sin Modal

Guía para correr todo el sistema localmente sin usar Modal.

## 🎯 Por qué deployar local?

- ✅ **Gratis** - Sin costos de Modal
- ✅ **Privado** - Tus datos nunca salen de tu compu
- ✅ **Rápido** - Sin latencia de red (si tienes buena GPU)
- ✅ **Offline** - Funciona sin internet (después de descargar el modelo)
- ⚠️ Requiere GPU/CPU potente para el LLM

## 📦 Requisitos

- Python 3.11+
- ~4GB RAM mínimo (8GB recomendado)
- GPU NVIDIA (opcional pero recomendado)
- ~3GB espacio en disco para el modelo

## 🚀 Setup Rápido

### 1. Instalar dependencias

```bash
cd /Users/felipemaldonado/Documents/repositories/Orgappitation

# Dependencias básicas
pip install -r requirements.txt

# Para GPU NVIDIA (opcional, pero MUCHO más rápido)
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir
```

### 2. Configurar .env

```bash
# Editar .env
nano .env

# Configurar para modo local:
FINANZAS_API_KEY=tu_api_key_secreta
TELEGRAM_BOT_TOKEN=tu_token_de_botfather

# URL local del LLM (importante!)
LLM_API_URL=http://127.0.0.1:8001/text_to_yaml

# Modal API URL (si quieres usar la API en Modal)
# O déjalo vacío si también la quieres local
MODAL_API_URL=
```

## 🎮 Opción 1: Todo Local (LLM + API + Bot)

### 1. Iniciar Servicio LLM Local

Terminal 1:

```bash
python llm_service_local.py
```

Primera vez tarda ~5-10 minutos descargando el modelo (2GB).

Deberías ver:

```
🧠 Cargando modelo Qwen-2.5-3b-Text_to_SQL...
   Repo: mradermacher/Qwen-2.5-3b-Text_to_SQL-GGUF
   File: Qwen-2.5-3b-Text_to_SQL.Q4_K_M.gguf
✅ Modelo cargado exitosamente!

🚀 Iniciando Finanzas LLM Service (Local)
   Host: 127.0.0.1
   Puerto: 8001
   URL: http://127.0.0.1:8001
```

### 2. Iniciar API Local (SQLite)

Terminal 2:

```bash
# Crear directorio para DB
mkdir -p data

# Inicializar DB local
python -c "
import sqlite3
with open('api/sql_schema.sql', 'r') as f:
    schema = f.read()
conn = sqlite3.connect('data/finanzas.db')
conn.executescript(schema)
conn.close()
print('✅ DB local inicializada')
"

# Iniciar API local
python api/local_api.py
```

**Nota**: Si no existe `api/local_api.py`, puedes usar Modal localmente con:

```bash
modal serve api/modal_app.py
```

### 3. Iniciar Bot de Telegram

Terminal 3:

```bash
python telegram/bot.py
```

### 4. Probar

Abre Telegram y escribe:

```
Gasté 5000 en café
```

## 🎮 Opción 2: Híbrido (LLM Local + API Modal)

Si quieres el LLM local pero la API en Modal (para acceso desde múltiples dispositivos):

### 1. Deploy API en Modal

```bash
modal deploy api/modal_app.py
modal run api/modal_app.py::init_db
```

### 2. Configurar .env

```bash
# URL de Modal para la API
MODAL_API_URL=https://tu-url--finanzas-api-fastapi-app.modal.run

# URL local para el LLM
LLM_API_URL=http://127.0.0.1:8001/text_to_yaml
```

### 3. Iniciar servicios

```bash
# Terminal 1: LLM local
python llm_service_local.py

# Terminal 2: Bot
python telegram/bot.py
```

## 🧪 Testing

### Test del LLM local

```bash
# Modo test directo (sin servidor)
python llm_service_local.py --test "Gasté 5000 en café"

# Salida esperada:
🧪 Modo test: Gasté 5000 en café

🧠 Cargando modelo Qwen-2.5-3b-Text_to_SQL...
✅ Modelo cargado exitosamente!

✅ YAML generado:
──────────────────────────────────────────────────
monto: 5000
descripcion: café
categoria: food
──────────────────────────────────────────────────
```

### Test del endpoint HTTP

```bash
# En otra terminal (con el servidor corriendo)
curl -X POST http://127.0.0.1:8001/text_to_yaml \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Gasté 5000 en café",
    "api_key": "tu_api_key"
  }'

# Respuesta esperada:
{
  "yaml_output": "monto: 5000\ndescripcion: café\ncategoria: food",
  "success": true,
  "error": null
}
```

### Health check

```bash
curl http://127.0.0.1:8001/health

# Respuesta:
{
  "status": "ok",
  "service": "finanzas-llm-local",
  "model": "loaded"
}
```

## ⚡ Optimizaciones

### Si tienes GPU NVIDIA

```bash
# Reinstalar llama-cpp-python con soporte CUDA
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir

# Verificar GPU
python -c "from llama_cpp import Llama; print('GPU support:', Llama.supports_gpu_offload())"
```

Con GPU: ~2-3 segundos por request
Sin GPU: ~10-20 segundos por request

### Si solo tienes CPU

El modelo igual funciona, solo será más lento.

Para optimizar:

```bash
# Usar modelo más pequeño
# Edita llm_service_local.py, línea ~23:
MODEL_FILE = "Qwen-2.5-3b-Text_to_SQL.Q2_K.gguf"  # Más pequeño, menos preciso
```

### Cambiar puerto

```bash
# Si el puerto 8001 está ocupado
python llm_service_local.py --port 8002

# Actualizar .env:
LLM_API_URL=http://127.0.0.1:8002/text_to_yaml
```

## 🔧 Configuración Avanzada

### Ajustar threads (CPU)

Edita `llm_service_local.py`, línea ~120:

```python
n_threads=os.cpu_count() or 8,  # Ajusta según tus cores
```

### Ajustar context size

Si tienes suficiente RAM, puedes aumentar el contexto:

```python
n_ctx=8192,  # Default es 4096
```

### Deshabilitar GPU

Si tienes GPU pero quieres usar CPU:

```python
n_gpu_layers=0,  # 0 = solo CPU, -1 = toda la GPU
```

## 📊 Comparación: Local vs Modal

| Característica | Local | Modal |
|---------------|-------|-------|
| **Costo** | $0 | ~$3/mes |
| **Velocidad (GPU)** | 2-3s | 3-5s (30-60s cold start) |
| **Velocidad (CPU)** | 10-20s | N/A (Modal usa GPU) |
| **Setup** | 10 min | 5 min |
| **Privacidad** | 100% local | En la nube |
| **Acceso remoto** | Solo local | Desde cualquier lugar |
| **Mantenimiento** | Tu responsabilidad | Automático |

## 🐛 Troubleshooting

### "ImportError: llama_cpp"

```bash
pip install llama-cpp-python
```

### "Model download failed"

El modelo se descarga desde HuggingFace automáticamente. Si falla:

```bash
# Descargar manualmente
huggingface-cli download mradermacher/Qwen-2.5-3b-Text_to_SQL-GGUF \
  Qwen-2.5-3b-Text_to_SQL.Q4_K_M.gguf

# O usar el script
python -c "
from llama_cpp import Llama
Llama.from_pretrained(
    repo_id='mradermacher/Qwen-2.5-3b-Text_to_SQL-GGUF',
    filename='Qwen-2.5-3b-Text_to_SQL.Q4_K_M.gguf',
)
print('✅ Modelo descargado')
"
```

### "Address already in use"

Puerto 8001 ocupado. Usa otro:

```bash
python llm_service_local.py --port 8002
```

### Muy lento (CPU)

Si solo tienes CPU y es muy lento:

1. Usa modelo más pequeño (Q2_K en vez de Q4_K_M)
2. Reduce threads: `n_threads=4`
3. O usa Modal (tiene GPU)

### "CUDA out of memory"

Tu GPU tiene poca memoria. Reduce layers:

```python
n_gpu_layers=20,  # En vez de -1 (todo)
```

## 🔄 Mantener actualizado

```bash
# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Actualizar modelo (si hay nueva versión)
rm -rf ~/.cache/huggingface/hub/models--mradermacher--*
python llm_service_local.py --test "test"  # Re-descarga
```

## 🚦 Iniciar automáticamente

### macOS/Linux - systemd

Crea `/etc/systemd/system/finanzas-llm.service`:

```ini
[Unit]
Description=Finanzas LLM Service
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/Users/felipemaldonado/Documents/repositories/Orgappitation
ExecStart=/usr/bin/python3 llm_service_local.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable finanzas-llm
sudo systemctl start finanzas-llm
```

### macOS - LaunchAgent

Crea `~/Library/LaunchAgents/com.finanzas.llm.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.finanzas.llm</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/felipemaldonado/Documents/repositories/Orgappitation/llm_service_local.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.finanzas.llm.plist
```

## 📝 Resumen

**Para desarrollo/testing**: Local es perfecto
**Para producción 24/7**: Modal es más confiable
**Para privacidad máxima**: Local + SQLite local
**Para acceso remoto**: Híbrido (LLM local + API Modal)

---

Ver también:
- [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md) - Deploy en Modal
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura del sistema
- [README.md](README.md) - Overview general
