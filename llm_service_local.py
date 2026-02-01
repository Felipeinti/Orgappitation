#!/usr/bin/env python3
"""
Servicio LLM Local - Convierte texto natural a YAML de finanzas
Versión local (sin Modal) para correr en tu computadora
Usa Qwen-2.5-3b-Text_to_SQL con llama-cpp-python
"""
import os
import sys
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
from llama_cpp import Llama

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

FINANZAS_API_KEY = os.environ.get('FINANZAS_API_KEY', '')

if not FINANZAS_API_KEY:
    print("⚠️  FINANZAS_API_KEY no configurado en .env")
    print("   El servicio funcionará sin autenticación")

# Configuración del modelo
MODEL_REPO = "mradermacher/Qwen-2.5-3b-Text_to_SQL-GGUF"
MODEL_FILE = "Qwen-2.5-3b-Text_to_SQL.Q4_K_M.gguf"
MODEL_CACHE_PATH = os.path.expanduser("~/.cache/huggingface/hub")

# Prompt del sistema
SYSTEM_PROMPT = """Eres un asistente que convierte mensajes de finanzas en YAML.

El usuario dirá cosas como:
- "Gasté 5000 en café"
- "Compré comida por 12000 pesos"
- "Pagué 45000 de alquiler"
- "Me llegó el sueldo de 200000"
- "Ingreso de 50000"

Tu trabajo es extraer:
1. monto (obligatorio) - número
2. descripcion (opcional) - texto descriptivo
3. categoria (opcional) - una de: food, housing, transport, entertainment, health, shopping, income, other
4. es_ingreso (opcional) - true si es ingreso, false o no incluir si es gasto

Formato de salida YAML:
```yaml
monto: <número>
descripcion: <texto>
categoria: <categoría>
es_ingreso: <true/false>
```

Reglas:
- Si no mencionan categoría, intenta inferirla del contexto
- Si dice "gasté", "compré", "pagué" → es gasto (es_ingreso: false o no incluir)
- Si dice "ingreso", "cobré", "me pagaron", "sueldo" → es_ingreso: true
- SOLO responde con YAML, nada más
- NO agregues explicaciones
- NO uses markdown code blocks (```)
- Monto SIEMPRE en números (sin símbolos $, ARS, etc)

Ejemplos:

Input: "Gasté 5000 en café"
Output:
monto: 5000
descripcion: café
categoria: food

Input: "Pagué 45000 de alquiler"
Output:
monto: 45000
descripcion: alquiler
categoria: housing

Input: "Me llegó el sueldo de 200000"
Output:
monto: 200000
descripcion: sueldo
categoria: income
es_ingreso: true

Input: "Compré ropa por 15000"
Output:
monto: 15000
descripcion: ropa
categoria: shopping
"""

# Variable global para el modelo (se carga al iniciar)
llm = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler - carga modelo al iniciar"""
    # Startup
    load_model()
    yield
    # Shutdown (si necesitamos cleanup en el futuro)
    pass


# App FastAPI
app = FastAPI(
    title="Finanzas LLM Service (Local)",
    description="Servicio local para convertir texto natural a YAML de finanzas",
    version="1.0.0",
    lifespan=lifespan,
)


def load_model():
    """Carga el modelo LLM en memoria"""
    global llm
    
    print("🧠 Cargando modelo Qwen-2.5-3b-Text_to_SQL...")
    print(f"   Repo: {MODEL_REPO}")
    print(f"   File: {MODEL_FILE}")
    print(f"   Cache: {MODEL_CACHE_PATH}")
    
    try:
        llm = Llama.from_pretrained(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            n_ctx=4096,
            n_threads=os.cpu_count() or 8,  # Usar todos los cores
            n_gpu_layers=-1,  # Usar GPU si está disponible
            verbose=False,
        )
        print("✅ Modelo cargado exitosamente!")
        return True
    
    except Exception as e:
        print(f"❌ Error al cargar modelo: {e}")
        print("\n💡 Solución:")
        print("   1. Instala llama-cpp-python:")
        print("      pip install llama-cpp-python")
        print("   2. El modelo se descargará automáticamente la primera vez")
        print("      (puede tardar ~5-10 minutos, es un archivo de ~2GB)")
        return False


def text_to_yaml(text: str) -> Dict[str, Any]:
    """
    Convierte texto natural a YAML de finanzas
    
    Args:
        text: Texto del usuario (ej: "Gasté 5000 en café")
        
    Returns:
        Dict con:
        - yaml_output: El YAML generado
        - success: True/False
        - error: Mensaje de error si falló
    """
    if llm is None:
        return {
            "yaml_output": None,
            "success": False,
            "error": "Modelo no cargado. Reinicia el servicio.",
        }
    
    try:
        # Crear prompt
        prompt = f"""<|im_start|>system
{SYSTEM_PROMPT}<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant
"""
        
        # Generar
        response = llm(
            prompt,
            max_tokens=256,
            temperature=0.1,
            top_p=0.9,
            stop=["<|im_end|>", "<|endoftext|>"],
            echo=False,
        )
        
        # Extraer texto generado
        yaml_output = response["choices"][0]["text"].strip()
        
        # Limpiar si tiene code blocks
        if yaml_output.startswith("```"):
            lines = yaml_output.split("\n")
            yaml_output = "\n".join(lines[1:-1]) if len(lines) > 2 else yaml_output
        
        yaml_output = yaml_output.replace("```yaml", "").replace("```", "").strip()
        
        return {
            "yaml_output": yaml_output,
            "success": True,
            "error": None,
        }
    
    except Exception as e:
        return {
            "yaml_output": None,
            "success": False,
            "error": str(e),
        }


@app.post("/text_to_yaml")
async def text_to_yaml_endpoint(request: Request):
    """
    Endpoint HTTP para convertir texto a YAML
    
    POST /text_to_yaml
    Body: {"text": "Gasté 5000 en café", "api_key": "..."}
    
    Response: {"yaml_output": "monto: 5000\n...", "success": true}
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
    
    # Generar YAML
    result = text_to_yaml(text)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return JSONResponse(content=result)


@app.get("/health")
async def health():
    """Health check endpoint"""
    model_status = "loaded" if llm is not None else "not_loaded"
    return {
        "status": "ok",
        "service": "finanzas-llm-local",
        "model": model_status,
    }


@app.get("/")
async def root():
    """Root endpoint con información"""
    return {
        "service": "Finanzas LLM Service (Local)",
        "version": "1.0.0",
        "endpoints": {
            "POST /text_to_yaml": "Convertir texto a YAML",
            "GET /health": "Health check",
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
    
    parser = argparse.ArgumentParser(description="Servicio LLM local para finanzas")
    parser.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="Puerto (default: 8001)")
    parser.add_argument("--reload", action="store_true", help="Auto-reload en desarrollo")
    parser.add_argument("--test", help="Probar con texto de ejemplo")
    
    args = parser.parse_args()
    
    # Modo test
    if args.test:
        print(f"🧪 Modo test: {args.test}\n")
        
        # Cargar modelo
        if not load_model():
            sys.exit(1)
        
        # Generar
        result = text_to_yaml(args.test)
        
        if result["success"]:
            print("✅ YAML generado:")
            print("─" * 50)
            print(result["yaml_output"])
            print("─" * 50)
        else:
            print(f"❌ Error: {result['error']}")
        
        sys.exit(0)
    
    # Modo servidor
    print("🚀 Iniciando Finanzas LLM Service (Local)")
    print(f"   Host: {args.host}")
    print(f"   Puerto: {args.port}")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Docs: http://{args.host}:{args.port}/docs")
    print()
    
    uvicorn.run(
        "llm_service_local:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
