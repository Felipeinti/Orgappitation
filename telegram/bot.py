#!/usr/bin/env python3
"""
Bot de Telegram para finanzas con LLM
Usa LLM en Modal para convertir texto natural a YAML
"""
import os
import sys
import subprocess
import json
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Cargar variables de entorno
def load_env():
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env()

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
LLM_API_URL = os.environ.get('LLM_API_URL', '')
FINANZAS_API_KEY = os.environ.get('FINANZAS_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN no configurado en .env")
    print("   Agrega: TELEGRAM_BOT_TOKEN=tu_token_aqui")
    sys.exit(1)

if not LLM_API_URL:
    print("⚠️  LLM_API_URL no configurado - modo sin LLM")
    print("   Para usar LLM: Despliega llm_service_modal.py y agrega LLM_API_URL en .env")

if not OPENAI_API_KEY:
    print("⚠️  OPENAI_API_KEY no configurado - audio no funcionará")
    print("   Agrega tu OpenAI API key para usar Whisper")

# Inicializar cliente OpenAI para Whisper
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    llm_status = "✅ Conectado" if LLM_API_URL else "❌ Sin configurar"
    
    voice_status = "✅ Whisper habilitado" if openai_client else "❌ Sin configurar"
    
    # Mostrar chat_id para configurar shortcuts
    chat_id = update.effective_chat.id
    print(f"📱 Chat ID del usuario: {chat_id}")
    
    await update.message.reply_text(
        "💰 *Bot de Finanzas Personales*\n\n"
        "Comandos disponibles:\n\n"
        "🤖 Modo inteligente (con LLM):\n"
        "   Simplemente escribe en lenguaje natural:\n"
        "   • \"Gasté 5000 en café\"\n"
        "   • \"Pagué 45000 de alquiler\"\n"
        "   • \"Me llegó el sueldo de 200000\"\n\n"
        "🎤 Mensajes de voz:\n"
        "   ¡Ahora puedes enviar audios!\n"
        "   El bot transcribe y procesa automáticamente\n"
        "   Perfecto para usar con Action Button del iPhone\n\n"
        "📝 Comandos manuales:\n"
        "   `/gastar <monto> <descripcion>` - Registrar gasto\n"
        "   `/ingreso <monto> <descripcion>` - Registrar ingreso\n\n"
        "📊 Consultas:\n"
        "   `/balance` - Ver balance actual\n"
        "   `/stats` - Ver estadísticas completas\n\n"
        "🗑️ Otros:\n"
        "   `/limpiar` - Borrar todas las transacciones\n"
        "   `/help` - Ver esta ayuda\n\n"
        f"🧠 LLM: {llm_status}\n"
        f"🎤 Audio: {voice_status}\n\n"
        f"🆔 Tu Chat ID: `{chat_id}`\n"
        f"_(Úsalo en Shortcuts de iOS)_",
        parse_mode='Markdown'
    )


async def gastar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /gastar"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Uso: `/gastar <monto> [descripcion]`\n"
            "Ejemplo: `/gastar 5000 Café`",
            parse_mode='Markdown'
        )
        return
    
    try:
        monto = float(context.args[0])
        descripcion = ' '.join(context.args[1:]) if len(context.args) > 1 else "Gasto"
        
        # Crear YAML
        yaml_content = f"monto: {monto}\ndescripcion: {descripcion}"
        
        # Ejecutar script
        result = subprocess.run(
            ['python', 'yaml_to_modal.py', '--yaml', yaml_content],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            await update.message.reply_text(
                f"✅ *Gasto registrado*\n\n"
                f"💸 Monto: ${monto:,.0f} ARS\n"
                f"📝 Descripción: {descripcion}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Debe ser un número.")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout - intenta de nuevo")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ingreso"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Uso: `/ingreso <monto> [descripcion]`\n"
            "Ejemplo: `/ingreso 50000 Sueldo`",
            parse_mode='Markdown'
        )
        return
    
    try:
        monto = float(context.args[0])
        descripcion = ' '.join(context.args[1:]) if len(context.args) > 1 else "Ingreso"
        
        # Crear YAML
        yaml_content = f"monto: {monto}\ndescripcion: {descripcion}\nes_ingreso: true"
        
        # Ejecutar script
        result = subprocess.run(
            ['python', 'cli/yaml_to_modal.py', '--yaml', yaml_content],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            await update.message.reply_text(
                f"✅ *Ingreso registrado*\n\n"
                f"💵 Monto: ${monto:,.0f} ARS\n"
                f"📝 Descripción: {descripcion}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except ValueError:
        await update.message.reply_text("❌ Monto inválido. Debe ser un número.")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout - intenta de nuevo")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /balance"""
    await update.message.reply_text("⏳ Consultando balance...")
    
    try:
        result = subprocess.run(
            ['bash', './cli/finanzas_cli.sh', 'stats'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            msg = "💰 *Balance Actual*\n\n"
            msg += f"💵 Ingresos: ${data['total_income']:,.0f} ARS\n"
            msg += f"💸 Gastos: ${data['total_expenses']:,.0f} ARS\n"
            msg += f"━━━━━━━━━━━━━━━━━\n"
            msg += f"💰 *Balance: ${data['balance']:,.0f} ARS*\n\n"
            msg += f"📝 Total transacciones: {data['total_transactions']}"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout - intenta de nuevo")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats"""
    await update.message.reply_text("⏳ Obteniendo estadísticas...")
    
    try:
        result = subprocess.run(
            ['bash', './finanzas_cli.sh', 'stats'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            msg = "📊 *Estadísticas Completas*\n\n"
            msg += f"💵 Ingresos totales: ${data['total_income']:,.0f} ARS\n"
            msg += f"💸 Gastos totales: ${data['total_expenses']:,.0f} ARS\n"
            msg += f"💰 Balance: ${data['balance']:,.0f} ARS\n\n"
            msg += f"📝 Total transacciones: {data['total_transactions']}\n"
            msg += f"   • Gastos: {data['expense_count']}\n"
            msg += f"   • Ingresos: {data['income_count']}"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout - intenta de nuevo")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /consulta - Pregunta en lenguaje natural"""
    if not context.args:
        await update.message.reply_text(
            "❌ Uso: `/consulta <pregunta>`\n"
            "Ejemplo: `/consulta ¿Cuánto gasté en comida este mes?`",
            parse_mode='Markdown'
        )
        return
    
    pregunta = ' '.join(context.args)
    await update.message.reply_text(f"🤔 Analizando: _{pregunta}_", parse_mode='Markdown')
    
    try:
        result = subprocess.run(
            ['python', 'scripts/text_to_sql.py', pregunta],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            await update.message.reply_text(
                f"📊 *Resultado:*\n\n```\n{result.stdout}\n```",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"⚠️ Necesitas Ollama con llama3.2 para usar esta función.\n\n"
                f"Instala con:\n"
                f"`ollama pull llama3.2`",
                parse_mode='Markdown'
            )
    
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout - la consulta tomó demasiado tiempo")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /limpiar - Borrar todas las transacciones"""
    await update.message.reply_text(
        "⚠️ *¿Estás seguro?*\n\n"
        "Esto borrará *TODAS* las transacciones.\n"
        "Envía `/confirmar_limpiar` para confirmar.",
        parse_mode='Markdown'
    )


async def confirmar_limpiar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirmación para borrar todo"""
    await update.message.reply_text("🗑️ Borrando todas las transacciones...")
    
    try:
        result = subprocess.run(
            ['bash', '-c', 'echo "SI" | python cli/yaml_to_modal.py --delete-all --verbose'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            await update.message.reply_text(
                "✅ *Todas las transacciones fueron eliminadas*\n\n"
                "Puedes empezar de nuevo con `/gastar`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout - intenta de nuevo")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await start(update, context)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes de voz
    Transcribe con Whisper y procesa como texto
    """
    if not openai_client:
        await update.message.reply_text(
            "⚠️ Whisper no configurado. Agrega OPENAI_API_KEY en .env"
        )
        return
    
    if not LLM_API_URL:
        await update.message.reply_text(
            "⚠️ LLM no configurado. Configura LLM_API_URL en .env"
        )
        return
    
    try:
        # Indicar que está procesando
        await update.message.reply_text("🎤 Transcribiendo audio...")
        
        # Obtener archivo de voz
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        
        # Descargar audio temporalmente
        audio_path = f"/tmp/voice_{voice.file_id}.ogg"
        await file.download_to_drive(audio_path)
        
        # Transcribir con Whisper
        with open(audio_path, 'rb') as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es"  # Español
            )
        
        # Limpiar archivo temporal
        os.remove(audio_path)
        
        texto_transcrito = transcript.text
        
        # Mostrar transcripción
        await update.message.reply_text(
            f"📝 *Transcripción:*\n_{texto_transcrito}_",
            parse_mode='Markdown'
        )
        
        # Procesar el texto transcrito con el LLM (igual que texto normal)
        await update.message.reply_text("🧠 Procesando con LLM...")
        
        # Llamar al LLM service
        response = requests.post(
            LLM_API_URL,
            json={
                "text": texto_transcrito,
                "api_key": FINANZAS_API_KEY,
            },
            timeout=30
        )
        
        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Error del LLM: HTTP {response.status_code}"
            )
            return
        
        result = response.json()
        
        if not result.get("success"):
            await update.message.reply_text(
                f"❌ LLM falló: {result.get('error', 'Unknown error')}"
            )
            return
        
        yaml_output = result.get("yaml_output", "")
        tokens_info = result.get("tokens", {})
        
        if not yaml_output:
            await update.message.reply_text("❌ LLM no generó YAML válido")
            return
        
        # Detectar múltiples transacciones
        yaml_docs = yaml_output.split('\n---\n')
        num_transactions = len(yaml_docs)
        
        # Mostrar YAML generado COMPLETO para validación
        await update.message.reply_text(
            f"📝 *{num_transactions} transacción(es) detectada(s)*\n\n"
            f"🔍 *YAML generado por el LLM:*",
            parse_mode='Markdown'
        )
        
        # Enviar el YAML completo
        if len(yaml_output) <= 4000:
            await update.message.reply_text(
                f"```yaml\n{yaml_output}\n```",
                parse_mode='Markdown'
            )
        else:
            # Dividir por transacciones si es muy largo
            for i, yaml_doc in enumerate(yaml_docs, 1):
                yaml_doc_stripped = yaml_doc.strip()
                if yaml_doc_stripped:
                    await update.message.reply_text(
                        f"```yaml\n# Transacción {i}\n{yaml_doc_stripped}\n```",
                        parse_mode='Markdown'
                    )
        
        # Procesar transacciones
        import yaml
        successful = []
        failed = []
        
        for i, yaml_doc in enumerate(yaml_docs, 1):
            yaml_doc = yaml_doc.strip()
            if not yaml_doc:
                continue
            
            try:
                data = yaml.safe_load(yaml_doc)
                if not data or 'monto' not in data:
                    failed.append(f"Transacción {i}: falta campo 'monto'")
                    continue
                
                # Enviar a Modal API
                ingest_result = subprocess.run(
                    ['python', 'cli/yaml_to_modal.py', '--yaml', yaml_doc],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if ingest_result.returncode == 0:
                    monto = data.get('monto', 0)
                    descripcion = data.get('descripcion', 'Sin descripción')
                    es_ingreso = data.get('es_ingreso', False)
                    categoria = data.get('categoria', '')
                    
                    successful.append({
                        'monto': monto,
                        'descripcion': descripcion,
                        'es_ingreso': es_ingreso,
                        'categoria': categoria
                    })
                else:
                    failed.append(f"Transacción {i}: {ingest_result.stderr[:100]}")
            
            except Exception as e:
                failed.append(f"Transacción {i}: {str(e)[:100]}")
        
        # Generar resumen
        if successful:
            msg = f"🎤 *{len(successful)} transacción(es) desde audio:*\n\n"
            
            total_gastos = 0
            total_ingresos = 0
            
            for tx in successful:
                tipo_emoji = "💵" if tx['es_ingreso'] else "💸"
                cat_text = f" ({tx['categoria']})" if tx['categoria'] else ""
                msg += f"{tipo_emoji} ${tx['monto']:,.0f} - {tx['descripcion']}{cat_text}\n"
                
                if tx['es_ingreso']:
                    total_ingresos += tx['monto']
                else:
                    total_gastos += tx['monto']
            
            balance_neto = total_ingresos - total_gastos
            balance_emoji = "📈" if balance_neto > 0 else "📉" if balance_neto < 0 else "➖"
            
            msg += f"\n{balance_emoji} *Balance neto: "
            if balance_neto > 0:
                msg += f"+${balance_neto:,.0f}*"
            elif balance_neto < 0:
                msg += f"${balance_neto:,.0f}*"
            else:
                msg += f"${balance_neto:,.0f}*"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        
        if failed:
            error_msg = "⚠️ *Errores:*\n\n" + "\n".join(failed)
            await update.message.reply_text(error_msg, parse_mode='Markdown')
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error procesando audio: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes de texto libres (sin comando)
    Usa LLM para convertir a YAML y registrar
    """
    if not LLM_API_URL:
        await update.message.reply_text(
            "⚠️ LLM no configurado. Usa comandos como `/gastar` o `/ingreso`",
            parse_mode='Markdown'
        )
        return
    
    text = update.message.text.strip()
    
    if not text:
        return
    
    # Indicar que está procesando
    await update.message.reply_text("🧠 Analizando con LLM...")
    
    try:
        # Llamar al LLM service
        response = requests.post(
            LLM_API_URL,
            json={
                "text": text,
                "api_key": FINANZAS_API_KEY,
            },
            timeout=30
        )
        
        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Error del LLM: HTTP {response.status_code}\n{response.text}"
            )
            return
        
        result = response.json()
        
        if not result.get("success"):
            await update.message.reply_text(
                f"❌ LLM falló: {result.get('error', 'Unknown error')}"
            )
            return
        
        yaml_output = result.get("yaml_output", "")
        tokens_info = result.get("tokens", {})
        
        if not yaml_output:
            await update.message.reply_text("❌ LLM no generó YAML válido")
            return
        
        # Detectar múltiples transacciones (separadas por ---)
        yaml_docs = yaml_output.split('\n---\n')
        num_transactions = len(yaml_docs)
        
        # Mostrar YAML generado COMPLETO para validación
        await update.message.reply_text(
            f"📝 *{num_transactions} transacción(es) detectada(s)*\n\n"
            f"🔍 *YAML generado por el LLM:*",
            parse_mode='Markdown'
        )
        
        # Enviar el YAML completo en un mensaje separado
        # Si es muy largo, dividir en múltiples mensajes
        if len(yaml_output) <= 4000:
            await update.message.reply_text(
                f"```yaml\n{yaml_output}\n```",
                parse_mode='Markdown'
            )
        else:
            # Dividir por transacciones si es muy largo
            for i, yaml_doc in enumerate(yaml_docs, 1):
                yaml_doc = yaml_doc.strip()
                if yaml_doc:
                    await update.message.reply_text(
                        f"```yaml\n# Transacción {i}\n{yaml_doc}\n```",
                        parse_mode='Markdown'
                    )
        
        # Procesar cada transacción
        import yaml
        successful = []
        failed = []
        
        for i, yaml_doc in enumerate(yaml_docs, 1):
            yaml_doc = yaml_doc.strip()
            if not yaml_doc:
                continue
            
            try:
                # Validar que sea YAML válido
                data = yaml.safe_load(yaml_doc)
                if not data or 'monto' not in data:
                    failed.append(f"Transacción {i}: falta campo 'monto'")
                    continue
                
                # Enviar a Modal API
                ingest_result = subprocess.run(
                    ['python', 'cli/yaml_to_modal.py', '--yaml', yaml_doc],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if ingest_result.returncode == 0:
                    monto = data.get('monto', 0)
                    descripcion = data.get('descripcion', 'Sin descripción')
                    es_ingreso = data.get('es_ingreso', False)
                    categoria = data.get('categoria', '')
                    
                    successful.append({
                        'monto': monto,
                        'descripcion': descripcion,
                        'es_ingreso': es_ingreso,
                        'categoria': categoria
                    })
                else:
                    failed.append(f"Transacción {i}: {ingest_result.stderr[:100]}")
            
            except Exception as e:
                failed.append(f"Transacción {i}: {str(e)[:100]}")
        
        # Generar resumen
        if successful:
            msg = f"✅ *{len(successful)} transacción(es) registrada(s):*\n\n"
            
            total_gastos = 0
            total_ingresos = 0
            
            for tx in successful:
                tipo_emoji = "💵" if tx['es_ingreso'] else "💸"
                cat_text = f" ({tx['categoria']})" if tx['categoria'] else ""
                msg += f"{tipo_emoji} ${tx['monto']:,.0f} - {tx['descripcion']}{cat_text}\n"
                
                if tx['es_ingreso']:
                    total_ingresos += tx['monto']
                else:
                    total_gastos += tx['monto']
            
            # Calcular balance neto de estas transacciones
            balance_neto = total_ingresos - total_gastos
            balance_emoji = "📈" if balance_neto > 0 else "📉" if balance_neto < 0 else "➖"
            
            msg += f"\n{balance_emoji} *Balance neto: "
            if balance_neto > 0:
                msg += f"+${balance_neto:,.0f}*"
            elif balance_neto < 0:
                msg += f"${balance_neto:,.0f}*"
            else:
                msg += f"${balance_neto:,.0f}*"
            
            # Agregar info de tokens si está disponible
            if tokens_info and tokens_info.get('total_tokens'):
                msg += f"\n\n🔢 Tokens: {tokens_info['total_tokens']}"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        
        if failed:
            error_msg = "⚠️ *Errores:*\n\n" + "\n".join(failed)
            await update.message.reply_text(error_msg, parse_mode='Markdown')
    
    except requests.Timeout:
        await update.message.reply_text("❌ Timeout - el LLM tardó demasiado")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("❌ Timeout - guardado tardó demasiado")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


def main():
    """Iniciar bot"""
    print(f"🤖 Iniciando bot de Telegram...")
    print(f"   Token: {TELEGRAM_TOKEN[:10]}...")
    
    if LLM_API_URL:
        print(f"   🧠 LLM: {LLM_API_URL[:50]}...")
    else:
        print(f"   ⚠️  LLM: No configurado (solo comandos manuales)")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("gastar", gastar))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("consulta", consulta))
    app.add_handler(CommandHandler("limpiar", limpiar))
    app.add_handler(CommandHandler("confirmar_limpiar", confirmar_limpiar))
    
    # Handler para texto libre (usa LLM)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Handler para mensajes de voz (usa Whisper + LLM)
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    print("✅ Bot iniciado!")
    print("   Busca tu bot en Telegram y envía /start")
    print("   Escribe en lenguaje natural para usar el LLM")
    print("   🎤 También puedes enviar mensajes de voz!")
    print("   Presiona Ctrl+C para detener\n")
    
    app.run_polling()


if __name__ == '__main__':
    main()
