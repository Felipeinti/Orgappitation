#!/usr/bin/env python3
"""
Script para generar SQL desde lenguaje natural usando Llama local
y ejecutar queries en la API de Modal
"""
import os
import sys
import json
import requests
from typing import Optional, Dict, Any


def load_env():
    """Cargar variables de entorno desde .env si existe"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


# Sistema prompt optimizado para modelos pequeños
SYSTEM_PROMPT = """You are a SQL query generator for a personal finance database.
Your task is to convert natural language questions into valid SQLite queries.

RULES:
1. ONLY generate SELECT queries
2. NO DELETE, UPDATE, INSERT, DROP, or any modification commands
3. Return ONLY the SQL query, no explanations
4. Use proper SQLite syntax
5. All dates are in ISO format (YYYY-MM-DD HH:MM:SS)

DATABASE SCHEMA:
- transactions table:
  * id, date, amount, currency
  * expense_type (fixed/variable), category, is_income (0=expense, 1=income)
  * payment_method, money_source, description, notes

COMMON QUERIES:
- "total expenses": SELECT SUM(amount) FROM transactions WHERE is_income=0
- "this month": strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
- "by category": GROUP BY category

Output ONLY the SQL, nothing else."""


def generate_sql_with_llama(question: str, model: str = "llama3.2") -> str:
    """
    Generar SQL usando Llama local via Ollama
    
    Args:
        question: Pregunta en lenguaje natural
        model: Modelo de Ollama a usar
        
    Returns:
        SQL query generado
    
    Nota: Requiere Ollama instalado y corriendo
    """
    try:
        # Intentar usar Ollama API (local)
        import ollama
        
        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': SYSTEM_PROMPT
                },
                {
                    'role': 'user',
                    'content': question
                }
            ]
        )
        
        sql = response['message']['content'].strip()
        
        # Limpiar respuesta (remover markdown code blocks si existen)
        if sql.startswith('```'):
            sql = sql.split('```')[1]
            if sql.startswith('sql'):
                sql = sql[3:]
            sql = sql.strip()
        
        return sql
    
    except ImportError:
        print("⚠️  Ollama no instalado. Usa: pip install ollama", file=sys.stderr)
        print("⚠️  O instala Ollama desde: https://ollama.ai", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al generar SQL con Llama: {e}", file=sys.stderr)
        sys.exit(1)


def is_safe_query(sql: str) -> bool:
    """
    Validar que el query sea seguro (solo SELECT)
    
    Args:
        sql: Query SQL a validar
        
    Returns:
        True si es seguro, False si es peligroso
    """
    dangerous_keywords = [
        'DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER',
        'CREATE', 'TRUNCATE', 'REPLACE', 'PRAGMA', 'ATTACH', 'DETACH'
    ]
    
    sql_upper = sql.upper().strip()
    
    # Debe empezar con SELECT
    if not sql_upper.startswith('SELECT'):
        return False
    
    # No debe contener keywords peligrosos
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    return True


def execute_query(sql: str, api_url: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Ejecutar query en Modal API
    
    Args:
        sql: Query SQL a ejecutar
        api_url: URL de la API (default: desde env)
        api_key: API key (default: desde env)
        
    Returns:
        Resultados de la query
    """
    # Validar query
    if not is_safe_query(sql):
        raise ValueError("Query no seguro detectado. Solo se permiten SELECT queries.")
    
    # Cargar configuración
    if api_url is None:
        api_url = os.environ.get('MODAL_API_URL')
        if not api_url:
            raise ValueError("MODAL_API_URL no configurada")
    
    if api_key is None:
        api_key = os.environ.get('FINANZAS_API_KEY')
        if not api_key:
            raise ValueError("FINANZAS_API_KEY no configurada")
    
    # Ejecutar query
    query_url = api_url.rstrip('/') + '/query'
    
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            query_url,
            headers=headers,
            json={'sql': sql}
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error al ejecutar query en Modal: {e}")


def format_results(results: Dict[str, Any], format: str = 'table') -> str:
    """
    Formatear resultados para display
    
    Args:
        results: Resultados de la query
        format: 'table', 'json', or 'csv'
        
    Returns:
        String formateado
    """
    if not results.get('success'):
        return "Error en la query"
    
    columns = results.get('columns', [])
    rows = results.get('rows', [])
    
    if not rows:
        return "No hay resultados"
    
    if format == 'json':
        return json.dumps(results, indent=2)
    
    elif format == 'csv':
        output = ','.join(columns) + '\n'
        for row in rows:
            output += ','.join(str(v) for v in row) + '\n'
        return output
    
    else:  # table
        # Calcular anchos de columnas
        col_widths = [len(col) for col in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        
        # Header
        output = '  '.join(col.ljust(col_widths[i]) for i, col in enumerate(columns)) + '\n'
        output += '  '.join('-' * col_widths[i] for i in range(len(columns))) + '\n'
        
        # Rows
        for row in rows:
            output += '  '.join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + '\n'
        
        output += f"\n{len(rows)} row(s) returned"
        
        return output


def ask_question(question: str, verbose: bool = False, format: str = 'table') -> str:
    """
    Pipeline completo: pregunta → SQL → resultados
    
    Args:
        question: Pregunta en lenguaje natural
        verbose: Mostrar información detallada
        format: Formato de salida ('table', 'json', 'csv')
        
    Returns:
        Resultados formateados
    """
    # 1. Generar SQL con Llama
    if verbose:
        print(f"🤔 Pregunta: {question}\n")
    
    sql = generate_sql_with_llama(question)
    
    if verbose:
        print(f"🔍 SQL generado:\n{sql}\n")
    
    # 2. Validar seguridad
    if not is_safe_query(sql):
        return "❌ Error: Query no seguro generado por el modelo"
    
    # 3. Ejecutar
    if verbose:
        print("📡 Ejecutando query en Modal...\n")
    
    results = execute_query(sql)
    
    # 4. Formatear
    return format_results(results, format)


def main():
    """CLI principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generar SQL desde lenguaje natural y ejecutar en Modal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:

  # Pregunta simple
  python text_to_sql.py "¿Cuánto gasté este mes?"

  # Mostrar SQL generado
  python text_to_sql.py "Gastos por categoría" --verbose

  # Output en JSON
  python text_to_sql.py "Últimas 10 transacciones" --format json

  # Solo generar SQL (no ejecutar)
  python text_to_sql.py "Balance actual" --sql-only

Requiere:
- Ollama instalado: https://ollama.ai
- Modelo llama3.2 descargado: ollama pull llama3.2
- Variables de entorno: MODAL_API_URL, FINANZAS_API_KEY
        """
    )
    
    parser.add_argument('question', type=str, help='Pregunta en lenguaje natural')
    parser.add_argument('--model', type=str, default='llama3.2', help='Modelo de Ollama (default: llama3.2)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table', help='Formato de salida')
    parser.add_argument('--sql-only', action='store_true', help='Solo generar SQL, no ejecutar')
    
    args = parser.parse_args()
    
    # Cargar .env
    load_env()
    
    try:
        if args.sql_only:
            # Solo generar SQL
            sql = generate_sql_with_llama(args.question, model=args.model)
            print(sql)
        else:
            # Pipeline completo
            result = ask_question(args.question, verbose=args.verbose, format=args.format)
            print(result)
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
