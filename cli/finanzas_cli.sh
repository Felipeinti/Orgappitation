#!/bin/bash
# Script wrapper para que OpenClaw agregue gastos
# OpenClaw ejecuta: ./finanzas_cli.sh add "monto: 5000\ndescripcion: Café"

set -e

# Cambiar al directorio del script
cd "$(dirname "$0")"

COMMAND=$1
shift

case $COMMAND in
  add)
    # Agregar gasto desde YAML string
    # Uso: ./finanzas_cli.sh add "monto: 100\ndescripcion: Test"
    echo -e "$1" | python yaml_to_modal.py --stdin
    ;;
  
  add-file)
    # Agregar desde archivo
    # Uso: ./finanzas_cli.sh add-file /tmp/gasto.yaml
    python yaml_to_modal.py --file "$1"
    ;;
  
  query)
    # Hacer pregunta en lenguaje natural
    # Uso: ./finanzas_cli.sh query "¿Cuánto gasté este mes?"
    python text_to_sql.py "$1"
    ;;
  
  balance)
    # Ver balance rápido
    python text_to_sql.py "¿Cuál es mi balance actual?"
    ;;
  
  stats)
    # Ver estadísticas
    export FINANZAS_API_KEY=$(grep FINANZAS_API_KEY .env | cut -d '=' -f2)
    export MODAL_API_URL=$(grep MODAL_API_URL .env | cut -d '=' -f2)
    curl -s "$MODAL_API_URL/stats" -H "X-API-Key: $FINANZAS_API_KEY" | python -m json.tool
    ;;
  
  delete)
    # Eliminar transacción por ID
    # Uso: ./finanzas_cli.sh delete <transaction_id>
    python yaml_to_modal.py --delete "$1" --verbose
    ;;
  
  delete-all)
    # Eliminar todas las transacciones
    python yaml_to_modal.py --delete-all --verbose
    ;;
  
  help)
    echo "Uso: finanzas_cli.sh <comando> [args]"
    echo ""
    echo "Comandos:"
    echo "  add 'yaml'          Agregar gasto desde YAML"
    echo "  add-file <file>     Agregar desde archivo"
    echo "  query 'pregunta'    Consulta en lenguaje natural"
    echo "  balance             Ver balance"
    echo "  stats               Ver estadísticas"
    echo "  delete <id>         Eliminar transacción por ID"
    echo "  delete-all          Eliminar TODAS las transacciones"
    echo ""
    echo "Ejemplos:"
    echo "  ./finanzas_cli.sh add 'monto: 5000\ndescripcion: Café'"
    echo "  ./finanzas_cli.sh query '¿Cuánto gasté en comida?'"
    echo "  ./finanzas_cli.sh balance"
    echo "  ./finanzas_cli.sh delete abc-123-def"
    echo "  ./finanzas_cli.sh delete-all"
    ;;
  
  *)
    echo "❌ Comando desconocido: $COMMAND"
    echo "Usa: ./finanzas_cli.sh help"
    exit 1
    ;;
esac
