"""
Servicio LLM en Modal - Convierte texto natural a YAML de finanzas
Usa Qwen-2.5-3b-Text_to_SQL para generar YAML
"""
import modal
import os
from typing import Dict, Any

# Crear app de Modal
app = modal.App("finanzas-llm")

# Definir imagen con dependencias
llm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "llama-cpp-python==0.2.90",
        "huggingface-hub>=0.20.0",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
    })
)

# Volume para caché del modelo
model_cache = modal.Volume.from_name("llm-models-cache", create_if_missing=True)

MODEL_CACHE_PATH = "/cache"

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


@app.cls(
    image=llm_image,
    gpu="T4",  # GPU barata para modelo pequeño
    secrets=[modal.Secret.from_name("huggingface-secret")],
    volumes={MODEL_CACHE_PATH: model_cache},
    timeout=300,
    container_idle_timeout=120,
    min_containers=0,  # No mantener contenedor caliente (para ahorrar)
    max_containers=2,
)
class LLMService:
    """Servicio de LLM para convertir texto a YAML"""
    
    @modal.build()
    def download_model(self):
        """Descargar modelo al hacer build"""
        from llama_cpp import Llama
        import os
        
        os.makedirs(MODEL_CACHE_PATH, exist_ok=True)
        
        print("Descargando modelo Qwen-2.5-3b-Text_to_SQL...")
        
        # Inicializar (descarga automáticamente si no existe)
        Llama.from_pretrained(
            repo_id="mradermacher/Qwen-2.5-3b-Text_to_SQL-GGUF",
            filename="Qwen-2.5-3b-Text_to_SQL.Q4_K_M.gguf",
            n_ctx=4096,
            n_threads=4,
            n_gpu_layers=-1,
            verbose=True,
            model_path=MODEL_CACHE_PATH,
        )
        
        print("Modelo descargado exitosamente!")
    
    @modal.enter()
    def load_model(self):
        """Cargar modelo al iniciar contenedor"""
        from llama_cpp import Llama
        
        print("Cargando modelo en memoria...")
        
        self.llm = Llama.from_pretrained(
            repo_id="mradermacher/Qwen-2.5-3b-Text_to_SQL-GGUF",
            filename="Qwen-2.5-3b-Text_to_SQL.Q4_K_M.gguf",
            n_ctx=4096,
            n_threads=32,
            n_gpu_layers=-1,
            verbose=False,
            model_path=MODEL_CACHE_PATH,
        )
        
        print("✅ Modelo cargado!")
    
    @modal.method()
    def text_to_yaml(self, text: str) -> Dict[str, Any]:
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
        try:
            # Crear prompt
            prompt = f"""<|im_start|>system
{SYSTEM_PROMPT}<|im_end|>
<|im_start|>user
{text}<|im_end|>
<|im_start|>assistant
"""
            
            # Generar
            response = self.llm(
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


# Endpoint web para testing
@app.function(
    image=llm_image,
    secrets=[modal.Secret.from_name("finanzas-api-secret")],
)
@modal.web_endpoint(method="POST")
def text_to_yaml_endpoint(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Endpoint HTTP para convertir texto a YAML
    
    POST /text_to_yaml
    Body: {"text": "Gasté 5000 en café"}
    
    Response: {"yaml_output": "monto: 5000\n...", "success": true}
    """
    # Validar API key
    import os
    expected_key = os.environ.get("FINANZAS_API_KEY", "")
    provided_key = data.get("api_key", "")
    
    if not expected_key or provided_key != expected_key:
        return {
            "yaml_output": None,
            "success": False,
            "error": "Invalid API key",
        }
    
    text = data.get("text", "")
    
    if not text:
        return {
            "yaml_output": None,
            "success": False,
            "error": "No text provided",
        }
    
    # Llamar al servicio
    service = LLMService()
    result = service.text_to_yaml.remote(text)
    
    return result


# Health check
@app.function()
@modal.web_endpoint(method="GET")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "finanzas-llm"}


# CLI para testing local
@app.local_entrypoint()
def test_llm(text: str = "Gasté 5000 en café"):
    """
    Test del LLM localmente
    
    Usage:
        modal run llm_service_modal.py --text "Gasté 5000 en café"
    """
    print(f"🧠 Procesando: {text}")
    
    service = LLMService()
    result = service.text_to_yaml.remote(text)
    
    if result["success"]:
        print("\n✅ YAML generado:")
        print("─" * 50)
        print(result["yaml_output"])
        print("─" * 50)
    else:
        print(f"\n❌ Error: {result['error']}")
