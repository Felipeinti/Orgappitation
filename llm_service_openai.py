#!/usr/bin/env python3
"""
Servicio LLM con OpenAI API - Convierte texto natural a YAML de finanzas
Usa OpenAI GPT-4 con reasoning para generar YAML estructurado
Incluye logging de tokens consumidos
"""
import os
import sys
import csv
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
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

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
FINANZAS_API_KEY = os.environ.get('FINANZAS_API_KEY', '')

if not OPENAI_API_KEY:
    print("⚠️  OPENAI_API_KEY no configurado en .env")
    print("   El servicio funcionará pero las peticiones fallarán")

if not FINANZAS_API_KEY:
    print("⚠️  FINANZAS_API_KEY no configurado en .env")
    print("   El servicio funcionará sin autenticación")

# Archivo de log de tokens
TOKENS_LOG_FILE = "logs/openai_tokens.csv"

# Prompt del sistema para finanzas (con reasoning y soporte múltiple)
SYSTEM_PROMPT_FINANZAS = """Eres un asistente experto en finanzas personales que convierte mensajes de texto a YAML estructurado.

**IMPORTANTE: El usuario puede enviar MÚLTIPLES TRANSACCIONES en un solo mensaje.**

**PROCESO DE RAZONAMIENTO:**
Antes de generar el YAML, piensa paso a paso:
1. Detecta cuántas transacciones hay en el mensaje (puede ser 1 o más)
2. Para cada transacción:
   - Identifica si es un gasto o ingreso
   - Extrae el monto exacto
   - Extrae la descripción
   - Infiere la categoría más apropiada

**CAMPOS A EXTRAER (por cada transacción):**

1. **monto** (obligatorio) - número sin símbolos
2. **descripcion** (opcional) - texto descriptivo corto
3. **categoria** (opcional) - una de estas:
   - food: comida, café, restaurantes, supermercado, bebidas
   - housing: alquiler, servicios (luz, gas, agua), reparaciones, muebles
   - transport: taxi, Uber, gasolina, transporte público, peajes
   - entertainment: cine, streaming, juegos, salidas, eventos
   - health: médicos, farmacia, gimnasio, terapia
   - shopping: ropa, tecnología, compras generales
   - income: ingresos, salario, freelance (si es ingreso)
   - other: si no encaja en ninguna categoría
4. **es_ingreso** (opcional) - true si es ingreso, false o no incluir si es gasto

**REGLAS:**
- Si dice "gasté", "compré", "pagué" → es gasto
- Si dice "ingreso", "cobré", "me pagaron", "sueldo" → es_ingreso: true
- Usa el contexto para inferir la categoría más específica
- Monto SIEMPRE en números (sin $, ARS, pesos, etc)
- Descripción corta y clara
- SOLO genera YAML, nada más
- NO uses markdown code blocks
- NO agregues explicaciones

**FORMATO DE SALIDA:**
- Si hay UNA transacción: genera un solo bloque YAML
- Si hay MÚLTIPLES transacciones: separa cada una con "---" (separador YAML estándar)

**EJEMPLOS:**

Input: "Gasté 5000 en café"
Output:
monto: 5000
descripcion: café
categoria: food

Input: "Café 200 y almuerzo 1500"
Output:
monto: 200
descripcion: café
categoria: food
---
monto: 1500
descripcion: almuerzo
categoria: food

Input: "Gasté 5000 en café, pagué 45000 de alquiler y me llegó el sueldo de 200000"
Output:
monto: 5000
descripcion: café
categoria: food
---
monto: 45000
descripcion: alquiler
categoria: housing
---
monto: 200000
descripcion: sueldo
categoria: income
es_ingreso: true

Input: "Taxi 3500
Cena 8000
Cobré 50000"
Output:
monto: 3500
descripcion: taxi
categoria: transport
---
monto: 8000
descripcion: cena
categoria: food
---
monto: 50000
descripcion: ingreso
categoria: income
es_ingreso: true
"""

# Cliente OpenAI global
openai_client = None


def init_openai():
    """Inicializa cliente de OpenAI"""
    global openai_client
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY no configurado")
        return False
    
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ Cliente OpenAI inicializado")
        return True
    except Exception as e:
        print(f"❌ Error al inicializar OpenAI: {e}")
        return False


def log_tokens(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    input_text: str,
    output_text: str,
    success: bool
):
    """
    Registra el consumo de tokens en un CSV
    
    Format: timestamp, model, prompt_tokens, completion_tokens, total_tokens, 
            input_length, output_length, success
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(TOKENS_LOG_FILE), exist_ok=True)
        
        # Verificar si el archivo existe para agregar header
        file_exists = os.path.exists(TOKENS_LOG_FILE)
        
        with open(TOKENS_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header si es archivo nuevo
            if not file_exists:
                writer.writerow([
                    'timestamp',
                    'model',
                    'prompt_tokens',
                    'completion_tokens',
                    'total_tokens',
                    'input_length',
                    'output_length',
                    'success',
                    'input_preview',
                    'output_preview'
                ])
            
            # Escribir datos
            writer.writerow([
                datetime.now().isoformat(),
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                len(input_text),
                len(output_text) if output_text else 0,
                success,
                input_text[:100],  # Preview de entrada
                output_text[:100] if output_text else ''  # Preview de salida
            ])
        
        print(f"📊 Tokens logged: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})")
    
    except Exception as e:
        print(f"⚠️  Error logging tokens: {e}")


def text_to_yaml_openai(text: str) -> Dict[str, Any]:
    """
    Convierte texto natural a YAML usando OpenAI API
    
    Args:
        text: Texto del usuario (ej: "Gasté 5000 en café")
        
    Returns:
        Dict con:
        - yaml_output: El YAML generado
        - success: True/False
        - error: Mensaje de error si falló
        - tokens: Info de tokens consumidos
    """
    if openai_client is None:
        return {
            "yaml_output": None,
            "success": False,
            "error": "Cliente OpenAI no inicializado",
            "tokens": None,
        }
    
    try:
        # Determinar modelo a usar
        # Prioridad: o1-mini (reasoning) > gpt-4o-mini (más barato) > gpt-4o
        model = "gpt-4o-mini"  # Más barato y rápido
        
        # Llamar a OpenAI
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_FINANZAS},
                {"role": "user", "content": text}
            ],
            temperature=0.1,  # Más determinístico
            max_tokens=256,
        )
        
        # Extraer YAML generado
        yaml_output = response.choices[0].message.content.strip()
        
        # Limpiar si tiene code blocks
        if yaml_output.startswith("```"):
            lines = yaml_output.split("\n")
            yaml_output = "\n".join(lines[1:-1]) if len(lines) > 2 else yaml_output
        
        yaml_output = yaml_output.replace("```yaml", "").replace("```", "").strip()
        
        # Detectar múltiples transacciones
        # Contar cuántos documentos YAML hay (separados por ---)
        num_transactions = yaml_output.count('---') + 1 if yaml_output else 0
        
        # Extraer info de tokens
        tokens_info = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
            "num_transactions": num_transactions,
        }
        
        # Logear tokens
        log_tokens(
            model=model,
            prompt_tokens=tokens_info["prompt_tokens"],
            completion_tokens=tokens_info["completion_tokens"],
            total_tokens=tokens_info["total_tokens"],
            input_text=text,
            output_text=yaml_output,
            success=True
        )
        
        return {
            "yaml_output": yaml_output,
            "success": True,
            "error": None,
            "tokens": tokens_info,
        }
    
    except Exception as e:
        # Logear error
        log_tokens(
            model=model if 'model' in locals() else 'unknown',
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            input_text=text,
            output_text='',
            success=False
        )
        
        return {
            "yaml_output": None,
            "success": False,
            "error": str(e),
            "tokens": None,
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler - inicializa OpenAI al iniciar"""
    # Startup
    init_openai()
    yield
    # Shutdown (si necesitamos cleanup en el futuro)
    pass


# App FastAPI
app = FastAPI(
    title="Finanzas LLM Service (OpenAI)",
    description="Servicio con OpenAI API para convertir texto natural a YAML de finanzas",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/text_to_yaml")
async def text_to_yaml_endpoint(request: Request):
    """
    Endpoint HTTP para convertir texto a YAML usando OpenAI
    
    POST /text_to_yaml
    Body: {"text": "Gasté 5000 en café", "api_key": "..."}
    
    Response: {
        "yaml_output": "monto: 5000\n...", 
        "success": true,
        "tokens": {...}
    }
    """
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    
    # Validar API key (si está configurada)
    if FINANZAS_API_KEY:
        provided_key = data.get("api_key", "")
        if provided_key != FINANZAS_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    text = data.get("text", "")
    
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Generar YAML con OpenAI
    result = text_to_yaml_openai(text)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return JSONResponse(content=result)


@app.get("/health")
async def health():
    """Health check endpoint"""
    openai_status = "connected" if openai_client is not None else "not_initialized"
    return {
        "status": "ok",
        "service": "finanzas-llm-openai",
        "openai": openai_status,
    }


@app.get("/tokens/stats")
async def tokens_stats():
    """Ver estadísticas de tokens consumidos"""
    try:
        if not os.path.exists(TOKENS_LOG_FILE):
            return {"total_requests": 0, "total_tokens": 0}
        
        total_requests = 0
        total_tokens = 0
        successful_requests = 0
        
        with open(TOKENS_LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_requests += 1
                total_tokens += int(row['total_tokens'])
                if row['success'] == 'True':
                    successful_requests += 1
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "total_tokens": total_tokens,
            "avg_tokens_per_request": total_tokens / total_requests if total_requests > 0 else 0,
            "log_file": TOKENS_LOG_FILE,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint con información"""
    return {
        "service": "Finanzas LLM Service (OpenAI)",
        "version": "1.0.0",
        "model": "gpt-4o-mini",
        "endpoints": {
            "POST /text_to_yaml": "Convertir texto a YAML",
            "GET /health": "Health check",
            "GET /tokens/stats": "Estadísticas de tokens",
            "GET /": "Esta información",
        },
        "example": {
            "url": "/text_to_yaml",
            "method": "POST",
            "body": {
                "text": "Gasté 5000 en café",
                "api_key": "tu_api_key",
            },
        },
    }


def main():
    """Iniciar servidor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Servicio LLM con OpenAI para finanzas")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8002, help="Puerto (default: 8002)")
    parser.add_argument("--reload", action="store_true", help="Auto-reload en desarrollo")
    parser.add_argument("--test", help="Probar con texto de ejemplo")
    
    args = parser.parse_args()
    
    # Modo test
    if args.test:
        print(f"🧪 Modo test: {args.test}\n")
        
        # Inicializar OpenAI
        if not init_openai():
            sys.exit(1)
        
        # Generar
        result = text_to_yaml_openai(args.test)
        
        if result["success"]:
            print("✅ YAML generado:")
            print("─" * 50)
            print(result["yaml_output"])
            print("─" * 50)
            print(f"\n📊 Tokens: {result['tokens']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        sys.exit(0)
    
    # Modo servidor
    print("🚀 Iniciando Finanzas LLM Service (OpenAI)")
    print(f"   Host: {args.host}")
    print(f"   Puerto: {args.port}")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs")
    print(f"   Tokens log: {TOKENS_LOG_FILE}")
    print()
    
    uvicorn.run(
        "llm_service_openai:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
