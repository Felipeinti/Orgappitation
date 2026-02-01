#!/bin/bash
# Script para iniciar todos los servicios locales

set -e  # Exit on error

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Finanzas (Modo Local)${NC}\n"

# Verificar .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Archivo .env no encontrado${NC}"
    echo -e "${YELLOW}   Copia .env.example a .env y configúralo${NC}"
    exit 1
fi

# Verificar Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python no encontrado${NC}"
    exit 1
fi

# Verificar dependencias
echo -e "${YELLOW}📦 Verificando dependencias...${NC}"
python -c "import llama_cpp" 2>/dev/null || {
    echo -e "${RED}❌ llama-cpp-python no instalado${NC}"
    echo -e "${YELLOW}   Ejecuta: pip install -r requirements.txt${NC}"
    exit 1
}

# Crear directorio de datos si no existe
mkdir -p data

# Preguntar qué servicios iniciar
echo -e "\n${YELLOW}¿Qué servicios quieres iniciar?${NC}"
echo "1) Solo LLM (para usar con API en Modal)"
echo "2) Todo local (LLM + Bot de Telegram)"
echo "3) Test del LLM (sin servidor)"
read -p "Selecciona [1-3]: " choice

case $choice in
    1)
        echo -e "\n${GREEN}🧠 Iniciando solo LLM local...${NC}\n"
        python llm_service_local.py
        ;;
    2)
        echo -e "\n${GREEN}🚀 Iniciando servicios locales...${NC}\n"
        
        # Iniciar LLM en background
        echo -e "${YELLOW}📝 Iniciando LLM service...${NC}"
        python llm_service_local.py > logs/llm.log 2>&1 &
        LLM_PID=$!
        echo -e "${GREEN}   ✅ LLM iniciado (PID: $LLM_PID)${NC}"
        
        # Esperar a que el LLM esté listo
        echo -e "${YELLOW}⏳ Esperando que el LLM cargue (puede tardar ~30s)...${NC}"
        sleep 5
        
        # Verificar que esté funcionando
        for i in {1..30}; do
            if curl -s http://127.0.0.1:8001/health > /dev/null 2>&1; then
                echo -e "${GREEN}   ✅ LLM listo!${NC}\n"
                break
            fi
            sleep 2
            echo -n "."
        done
        
        # Iniciar bot
        echo -e "${YELLOW}🤖 Iniciando bot de Telegram...${NC}"
        python telegram/bot.py
        
        # Cleanup al salir
        trap "echo -e '\n${YELLOW}🛑 Deteniendo servicios...${NC}'; kill $LLM_PID 2>/dev/null; exit" INT TERM
        ;;
    3)
        echo -e "\n${GREEN}🧪 Modo test del LLM${NC}\n"
        read -p "Escribe un mensaje de prueba (ej: 'Gasté 5000 en café'): " test_msg
        python llm_service_local.py --test "$test_msg"
        ;;
    *)
        echo -e "${RED}❌ Opción inválida${NC}"
        exit 1
        ;;
esac
