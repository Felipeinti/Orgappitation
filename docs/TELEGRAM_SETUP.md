# 📱 Setup para Telegram con OpenClaw

Guía completa para usar tu app de finanzas desde Telegram.

## Opción 1: Sin OpenClaw (Más simple, solo para probar)

Si solo quieres probar rápido sin instalar OpenClaw, puedes usar un bot simple:

### 1.1 Crear bot de Telegram

1. Abre Telegram y busca: **@BotFather**
2. Envía: `/newbot`
3. Sigue las instrucciones
4. Te dará un **token** como: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
5. Guarda ese token

### 1.2 Script simple de Telegram

Crea `telegram_bot.py`:

```python
#!/usr/bin/env python3
"""
Bot simple de Telegram para finanzas
"""
import os
import sys
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN no configurado en .env")
    sys.exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "💰 Bot de Finanzas\n\n"
        "Comandos disponibles:\n"
        "/gastar <monto> <descripcion> - Registrar gasto\n"
        "/balance - Ver balance\n"
        "/stats - Ver estadísticas\n\n"
        "Ejemplo: /gastar 5000 Supermercado"
    )

async def gastar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /gastar"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Uso: /gastar <monto> <descripcion>\nEjemplo: /gastar 5000 Café")
        return
    
    try:
        monto = float(context.args[0])
        descripcion = ' '.join(context.args[1:])
        
        # Crear YAML
        yaml_content = f"monto: {monto}\ndescripcion: {descripcion}"
        
        # Ejecutar script
        result = subprocess.run(
            ['python', 'yaml_to_modal.py', '--yaml', yaml_content],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            await update.message.reply_text(f"✅ Gasto registrado: ${monto} ARS - {descripcion}")
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Debe ser un número.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /balance"""
    try:
        result = subprocess.run(
            ['python', 'text_to_sql.py', '¿Cuál es mi balance actual?'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            await update.message.reply_text(f"💰 Balance:\n\n{result.stdout}")
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats"""
    try:
        result = subprocess.run(
            ['bash', './finanzas_cli.sh', 'stats'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            msg = "📊 Estadísticas:\n\n"
            msg += f"💵 Ingresos: ${data['total_income']:.0f} ARS\n"
            msg += f"💸 Gastos: ${data['total_expenses']:.0f} ARS\n"
            msg += f"💰 Balance: ${data['balance']:.0f} ARS\n"
            msg += f"📝 Transacciones: {data['total_transactions']}"
            
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    """Iniciar bot"""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gastar", gastar))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    
    print("🤖 Bot iniciado...")
    app.run_polling()

if __name__ == '__main__':
    main()
```

### 1.3 Instalar dependencias

```bash
pip install python-telegram-bot python-dotenv
```

### 1.4 Configurar token

Agrega a tu `.env`:

```bash
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

### 1.5 Ejecutar bot

```bash
python telegram_bot.py
```

### 1.6 Usar en Telegram

1. Busca tu bot en Telegram (el nombre que le pusiste)
2. Envía: `/start`
3. Prueba: `/gastar 5000 Café en Starbucks`
4. Prueba: `/balance`
5. Prueba: `/stats`

---

## Opción 2: Con OpenClaw (Completo, con IA)

OpenClaw es más poderoso porque:
- ✅ Entiende lenguaje natural ("gasté 5000 en café")
- ✅ Soporta audio (grabas y transcribe)
- ✅ Multi-canal (Telegram, WhatsApp, Discord, etc)
- ✅ Más inteligente (usa Claude/GPT)

### 2.1 Instalar OpenClaw

```bash
# Instalar
npm install -g openclaw@latest

# Configurar
openclaw onboard --install-daemon
```

Esto abrirá un wizard interactivo. Selecciona:
- ✅ Telegram como canal
- ✅ Anthropic o OpenAI como modelo
- Sigue las instrucciones

### 2.2 Configurar Telegram en OpenClaw

Durante el `onboard`, OpenClaw te pedirá un token de Telegram. Usa el mismo que creaste con BotFather.

O edita manualmente:

```bash
nano ~/.openclaw/openclaw.json
```

Agrega:

```json
{
  "channels": {
    "telegram": {
      "botToken": "tu_token_aqui"
    }
  }
}
```

### 2.3 Copiar scripts de finanzas al workspace de OpenClaw

```bash
# Crear directorio
mkdir -p ~/.openclaw/workspace/tools/finanzas

# Copiar archivos
cp finanzas_cli.sh ~/.openclaw/workspace/tools/finanzas/
cp yaml_to_modal.py ~/.openclaw/workspace/tools/finanzas/
cp text_to_sql.py ~/.openclaw/workspace/tools/finanzas/
cp .env ~/.openclaw/workspace/tools/finanzas/

# Dar permisos
chmod +x ~/.openclaw/workspace/tools/finanzas/finanzas_cli.sh
```

### 2.4 Crear Skill de Finanzas

```bash
mkdir -p ~/.openclaw/workspace/skills/finanzas
nano ~/.openclaw/workspace/skills/finanzas/SKILL.md
```

Contenido:

```markdown
# 💰 Finanzas Skill

Gestiona finanzas personales.

## Descripción

Este skill permite registrar gastos e ingresos, y hacer consultas sobre finanzas personales.

## Comandos

### Registrar gastos

Cuando el usuario mencione un gasto, extrae:
- **monto** (obligatorio)
- **descripción** (opcional)
- **categoría** (opcional): food, housing, transport, entertainment, health, shopping

Ejemplos:
- "Gasté 5000 en el supermercado" → monto: 5000, descripción: Supermercado, categoría: food
- "Pagué 45000 de alquiler" → monto: 45000, descripción: Alquiler, categoría: housing
- "200 pesos de café" → monto: 200, descripción: Café, categoría: food

### Consultas

Para preguntas como:
- "¿Cuánto gasté este mes?"
- "¿Cuál es mi balance?"
- "Gastos por categoría"

Usa el script de text-to-SQL.

## Herramientas

### Para registrar

```bash
cd ~/.openclaw/workspace/tools/finanzas && \
./finanzas_cli.sh add "monto: <monto>\ndescripcion: <descripcion>\ncategoria: <categoria>"
```

### Para consultas

```bash
cd ~/.openclaw/workspace/tools/finanzas && \
./finanzas_cli.sh query "<pregunta>"
```

### Para balance rápido

```bash
cd ~/.openclaw/workspace/tools/finanzas && \
./finanzas_cli.sh balance
```

## Notas

- El campo `monto` es OBLIGATORIO
- Todo lo demás es opcional
- Si no hay categoría, déjala vacía
```

### 2.5 Agregar instrucciones al AGENTS.md

```bash
nano ~/.openclaw/workspace/AGENTS.md
```

Agrega al final:

```markdown
## 💰 Finanzas

Cuando el usuario mencione gastos o finanzas:

1. **Para REGISTRAR un gasto:**
   - Extrae: monto (obligatorio), descripción, categoría
   - Categorías válidas: food, housing, transport, entertainment, health, shopping
   - Genera YAML:
     ```
     monto: <número>
     descripcion: <texto>
     categoria: <categoría>
     ```
   - Ejecuta:
     ```bash
     cd ~/.openclaw/workspace/tools/finanzas && \
     ./finanzas_cli.sh add "monto: X\ndescripcion: Y\ncategoria: Z"
     ```
   - Confirma al usuario

2. **Para CONSULTAS:**
   - Ejecuta:
     ```bash
     cd ~/.openclaw/workspace/tools/finanzas && \
     ./finanzas_cli.sh query "pregunta del usuario"
     ```
   - Muestra resultados de forma clara

3. **Para BALANCE:**
   - Ejecuta:
     ```bash
     cd ~/.openclaw/workspace/tools/finanzas && \
     ./finanzas_cli.sh balance
     ```

Ejemplos de conversación:
- Usuario: "Gasté 5000 en el super"
  → Registras: monto: 5000, descripcion: Supermercado, categoria: food
  → Respondes: "✅ Registrado: $5,000 ARS en Supermercado"

- Usuario: "¿Cuánto gasté este mes?"
  → Ejecutas query
  → Respondes con el resultado
```

### 2.6 Iniciar OpenClaw

```bash
openclaw gateway --port 18789 --verbose
```

O si ya configuraste el daemon:

```bash
modal app start openclaw-gateway
```

### 2.7 Usar desde Telegram

1. Abre Telegram
2. Busca tu bot
3. Envía: "Hola"
4. OpenClaw responderá
5. Prueba: "Gasté 5000 pesos en el supermercado"
6. Prueba: "¿Cuánto gasté este mes?"
7. Prueba: "Dame mi balance"

---

## Diferencias entre Opción 1 y 2

| Característica | Bot Simple | OpenClaw |
|---------------|------------|----------|
| Comandos | `/gastar 5000 Café` | "Gasté 5000 en café" |
| Audio | ❌ No | ✅ Sí |
| Inteligencia | Básica | IA completa |
| Multi-canal | Solo Telegram | Telegram, WhatsApp, Discord, etc |
| Setup | 5 minutos | 15-20 minutos |
| Costo | Gratis | Requiere API de Claude/GPT |

## Recomendación

1. **Empieza con Opción 1** para probar rápido
2. **Luego migra a Opción 2** cuando quieras features avanzadas

## Troubleshooting

### "ModuleNotFoundError: telegram"

```bash
pip install python-telegram-bot
```

### "TELEGRAM_BOT_TOKEN not found"

Verifica tu `.env`:

```bash
cat .env | grep TELEGRAM
```

### "Bot doesn't respond"

1. Verifica que el bot esté corriendo: `ps aux | grep telegram_bot`
2. Verifica logs: mira la terminal donde corre
3. Verifica token: busca tu bot en Telegram y prueba `/start`

### OpenClaw no ejecuta comandos

1. Verifica que los scripts estén en el path correcto
2. Verifica permisos: `ls -la ~/.openclaw/workspace/tools/finanzas/`
3. Prueba manual: `cd ~/.openclaw/workspace/tools/finanzas && ./finanzas_cli.sh stats`

---

## Próximos pasos

Una vez funcionando:
- ✅ Agregar más comandos (/ingresos, /categorias, etc)
- ✅ Configurar audio input (OpenClaw)
- ✅ Multi-canal (WhatsApp, Discord)
- ✅ Recordatorios automáticos
- ✅ Reportes mensuales
