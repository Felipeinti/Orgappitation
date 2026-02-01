"""
Webhook para recibir audio directamente desde iOS Shortcuts
Sin pasar por la API de Telegram
"""
import os
import tempfile
import requests
import yaml
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Audio Webhook para iOS")

# Configuración
MODAL_API_URL = os.getenv("MODAL_API_URL")
MODAL_API_KEY = os.getenv("MODAL_API_KEY")
LLM_API_URL = os.getenv("LLM_API_URL", "http://127.0.0.1:8002")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mi_secreto_super_seguro_123")

# Cliente OpenAI para Whisper
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("✅ Cliente OpenAI (Whisper) inicializado")
else:
    print("⚠️  OPENAI_API_KEY no configurada - Whisper no disponible")


@app.post("/audio")
async def process_audio(
    audio: UploadFile = File(...),
    authorization: str = Header(None)
):
    """
    Endpoint para recibir audio desde iOS Shortcuts
    
    Requiere header: Authorization: Bearer {WEBHOOK_SECRET}
    """
    # Validar autenticación
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header requerido")
    
    token = authorization.replace("Bearer ", "")
    if token != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Token inválido")
    
    if not openai_client:
        raise HTTPException(status_code=503, detail="Whisper no configurado")
    
    try:
        # 1. Guardar audio temporalmente
        content = await audio.read()
        
        # Detectar formato del archivo
        content_type = audio.content_type
        filename = audio.filename
        
        print(f"🎤 Audio recibido:")
        print(f"   - Bytes: {len(content)}")
        print(f"   - Content-Type: {content_type}")
        print(f"   - Filename: {filename}")
        print(f"   - Primeros bytes (hex): {content[:16].hex()}")
        
        # Determinar extensión correcta
        ext_map = {
            "audio/mp4": ".m4a",
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/x-m4a": ".m4a",
            "audio/wav": ".wav",
            "audio/ogg": ".ogg",
        }
        
        suffix = ext_map.get(content_type, ".m4a")  # Default a .m4a
        print(f"   - Extensión detectada: {suffix}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
        
        # 2. Transcribir con Whisper
        print("📝 Transcribiendo con Whisper...")
        with open(temp_audio_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es"
            )
        
        text = transcript.text
        print(f"✅ Transcripción: {text}")
        
        # 3. Enviar al LLM para convertir a YAML
        print("🧠 Procesando con LLM...")
        llm_response = requests.post(
            f"{LLM_API_URL}/text_to_yaml",
            json={
                "text": text,
                "api_key": MODAL_API_KEY  # Enviar API key
            },
            timeout=30
        )
        llm_response.raise_for_status()
        llm_data = llm_response.json()
        
        print(f"🔍 Respuesta del LLM: {llm_data}")
        
        # Intentar diferentes nombres de campos
        yaml_output = llm_data.get("yaml") or llm_data.get("yaml_output")
        if not yaml_output:
            print(f"❌ Campo 'yaml' no encontrado. Keys disponibles: {list(llm_data.keys())}")
            raise HTTPException(status_code=500, detail=f"LLM no generó YAML. Keys: {list(llm_data.keys())}")
        
        print(f"📋 YAML generado:\n{yaml_output}")
        
        # 4. Parsear múltiples documentos YAML y convertir al formato de la API
        try:
            # Usar safe_load_all para manejar múltiples documentos separados por ---
            yaml_documents = list(yaml.safe_load_all(yaml_output))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parseando YAML: {e}")
        
        if not yaml_documents:
            raise HTTPException(status_code=500, detail="No se encontraron transacciones en el YAML")
        
        print(f"📊 {len(yaml_documents)} transacción(es) detectada(s)")
        
        # 5. Procesar cada transacción
        results = []
        for idx, yaml_data in enumerate(yaml_documents, 1):
            if not yaml_data:  # Saltar documentos vacíos
                continue
                
            # Mapear campos del YAML al formato de la API
            es_ingreso = yaml_data.get("es_ingreso", False) or yaml_data.get("tipo", "gasto").lower() == "ingreso"
            
            transaction_data = {
                "amount": float(yaml_data.get("monto", 0)),
                "currency": yaml_data.get("moneda", "ARS").upper(),
                "description": yaml_data.get("descripcion"),
                "category": yaml_data.get("categoria"),
                "is_income": es_ingreso,
                "payment_method": yaml_data.get("metodo_pago"),
                "money_source": yaml_data.get("fuente_dinero"),
                "expense_type": yaml_data.get("tipo_gasto"),
                "notes": yaml_data.get("notas"),
            }
            
            # Remover campos None
            transaction_data = {k: v for k, v in transaction_data.items() if v is not None}
            
            print(f"📦 Transacción {idx}: {transaction_data}")
            
            # Enviar a Modal API
            try:
                modal_response = requests.post(
                    f"{MODAL_API_URL}/ingest",
                    json=transaction_data,
                    headers={"X-API-Key": MODAL_API_KEY},
                    timeout=30
                )
                modal_response.raise_for_status()
                result = modal_response.json()
                results.append({
                    "success": True,
                    "data": transaction_data,
                    "result": result
                })
                print(f"✅ Transacción {idx} guardada")
            except Exception as e:
                print(f"❌ Error en transacción {idx}: {e}")
                results.append({
                    "success": False,
                    "data": transaction_data,
                    "error": str(e)
                })
        
        # Limpiar archivo temporal
        os.unlink(temp_audio_path)
        
        # 6. Responder al iPhone con resumen
        summary_lines = []
        for r in results:
            if r["success"]:
                data = r["data"]
                tipo = "💰" if data.get("is_income") else "💸"
                monto = data.get("amount", 0)
                desc = data.get("description", "?")
                summary_lines.append(f"{tipo} ${monto:,.0f} - {desc}")
        
        if len(results) == 1:
            response_text = f"✅ Transacción registrada:\n{summary_lines[0]}"
        else:
            response_text = f"✅ {len(results)} transacciones registradas:\n" + "\n".join(summary_lines)
        
        print(f"\n✅ {response_text}")
        
        return JSONResponse({
            "success": True,
            "message": response_text,
            "transcription": text,
            "transactions_count": len(results),
            "transactions": results
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if 'temp_audio_path' in locals():
            try:
                os.unlink(temp_audio_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error procesando audio: {str(e)}")


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "whisper": openai_client is not None,
        "llm_url": LLM_API_URL,
        "modal_url": MODAL_API_URL
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*50)
    print("🎤 Audio Webhook Server")
    print("="*50)
    print(f"   Host: 0.0.0.0")
    print(f"   Puerto: 8003")
    print(f"   URL: http://localhost:8003")
    print(f"   Endpoint: POST /audio")
    print(f"   Auth: Bearer {WEBHOOK_SECRET}")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)
