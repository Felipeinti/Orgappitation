#!/usr/bin/env python3
"""
Script para convertir YAML a JSON y enviar a Modal API
Optimizado para uso con OpenClaw/LLMs pequeños
"""
import sys
import os
import json
import yaml
import argparse
from typing import Dict, Any, Optional
import requests
from decimal import Decimal


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


def convert_yaml_to_json(yaml_string: str) -> Dict[str, Any]:
    """
    Convierte YAML a JSON/dict válido para la API
    
    Mapeo de campos:
    - monto → amount
    - moneda → currency
    - tipo_gasto → expense_type
    - metodo_pago → payment_method
    - fuente_dinero → money_source
    - descripcion → description
    - categoria → category
    - notas → notes
    - es_ingreso → is_income
    - tasa_cambio → exchange_rate
    - monto_convertido → converted_amount
    - moneda_convertida → converted_currency
    - fecha → date
    """
    try:
        # Parsear YAML
        data = yaml.safe_load(yaml_string)
        
        if not data:
            raise ValueError("YAML vacío")
        
        # Mapeo de campos español → inglés
        field_mapping = {
            'monto': 'amount',
            'moneda': 'currency',
            'tipo_gasto': 'expense_type',
            'metodo_pago': 'payment_method',
            'fuente_dinero': 'money_source',
            'descripcion': 'description',
            'categoria': 'category',
            'notas': 'notes',
            'es_ingreso': 'is_income',
            'tasa_cambio': 'exchange_rate',
            'monto_convertido': 'converted_amount',
            'moneda_convertida': 'converted_currency',
            'fecha': 'date'
        }
        
        # Convertir campos
        json_data = {}
        
        for spanish_key, english_key in field_mapping.items():
            if spanish_key in data:
                value = data[spanish_key]
                
                # Convertir tipos especiales
                if english_key in ['amount', 'exchange_rate', 'converted_amount']:
                    if value is not None:
                        json_data[english_key] = float(value)
                elif english_key == 'is_income':
                    json_data[english_key] = bool(value)
                else:
                    json_data[english_key] = value
        
        # También aceptar campos en inglés directamente
        for english_key in field_mapping.values():
            if english_key in data and english_key not in json_data:
                value = data[english_key]
                
                if english_key in ['amount', 'exchange_rate', 'converted_amount']:
                    if value is not None:
                        json_data[english_key] = float(value)
                elif english_key == 'is_income':
                    json_data[english_key] = bool(value)
                else:
                    json_data[english_key] = value
        
        # Validar que al menos tenga amount
        if 'amount' not in json_data:
            raise ValueError("Debe especificar al menos 'monto' o 'amount'")
        
        # Defaults
        if 'currency' not in json_data:
            json_data['currency'] = 'ARS'
        
        if 'is_income' not in json_data:
            json_data['is_income'] = False
        
        return json_data
    
    except yaml.YAMLError as e:
        raise ValueError(f"Error al parsear YAML: {e}")
    except Exception as e:
        raise ValueError(f"Error al convertir YAML: {e}")


def send_to_modal(json_data: Dict[str, Any], api_url: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Envía JSON a Modal API
    
    Args:
        json_data: Datos en formato JSON
        api_url: URL de la API (default: desde env MODAL_API_URL)
        api_key: API key (default: desde env FINANZAS_API_KEY)
    
    Returns:
        Respuesta de la API
    """
    # Cargar configuración
    if api_url is None:
        api_url = os.environ.get('MODAL_API_URL')
        if not api_url:
            raise ValueError("MODAL_API_URL no configurada. Set en .env o pasa como argumento")
    
    if api_key is None:
        api_key = os.environ.get('FINANZAS_API_KEY')
        if not api_key:
            raise ValueError("FINANZAS_API_KEY no configurada. Set en .env o pasa como argumento")
    
    # URL completa del endpoint
    ingest_url = api_url.rstrip('/') + '/ingest'
    
    # Headers
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        # Hacer request
        response = requests.post(ingest_url, json=json_data, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error al enviar a Modal API: {e}")


def delete_transaction(transaction_id: str, api_url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Eliminar una transacción por ID
    
    Args:
        transaction_id: ID de la transacción a eliminar
        api_url: URL de la API
        api_key: API key
        verbose: Mostrar información detallada
    
    Returns:
        Respuesta de la API
    """
    # Cargar configuración
    if api_url is None:
        api_url = os.environ.get('MODAL_API_URL')
        if not api_url:
            raise ValueError("MODAL_API_URL no configurada")
    
    if api_key is None:
        api_key = os.environ.get('FINANZAS_API_KEY')
        if not api_key:
            raise ValueError("FINANZAS_API_KEY no configurada")
    
    delete_url = api_url.rstrip('/') + f'/transactions/{transaction_id}'
    
    headers = {
        'X-API-Key': api_key
    }
    
    try:
        if verbose:
            print(f"🗑️  Eliminando transacción {transaction_id}...")
        
        response = requests.delete(delete_url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if verbose:
            print(f"✅ {result['message']}")
        
        return result
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error al eliminar transacción: {e}")


def delete_all_transactions(api_url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Eliminar TODAS las transacciones
    
    Args:
        api_url: URL de la API
        api_key: API key
        verbose: Mostrar información detallada
    
    Returns:
        Respuesta de la API
    """
    # Cargar configuración
    if api_url is None:
        api_url = os.environ.get('MODAL_API_URL')
        if not api_url:
            raise ValueError("MODAL_API_URL no configurada")
    
    if api_key is None:
        api_key = os.environ.get('FINANZAS_API_KEY')
        if not api_key:
            raise ValueError("FINANZAS_API_KEY no configurada")
    
    delete_url = api_url.rstrip('/') + '/transactions?confirm=DELETE_ALL'
    
    headers = {
        'X-API-Key': api_key
    }
    
    try:
        if verbose:
            print("⚠️  Eliminando TODAS las transacciones...")
        
        response = requests.delete(delete_url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if verbose:
            print(f"✅ {result['message']}")
        
        return result
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error al eliminar transacciones: {e}")


def ingest_from_yaml(yaml_string: str, api_url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Pipeline completo: YAML → JSON → Modal API
    
    Args:
        yaml_string: String en formato YAML
        api_url: URL de la API
        api_key: API key
        verbose: Mostrar información detallada
    
    Returns:
        Respuesta de la API
    """
    try:
        # 1. Convertir YAML a JSON
        if verbose:
            print("🔄 Convirtiendo YAML a JSON...")
        
        json_data = convert_yaml_to_json(yaml_string)
        
        if verbose:
            print(f"✅ JSON generado:")
            print(json.dumps(json_data, indent=2))
        
        # 2. Enviar a Modal
        if verbose:
            print("\n📤 Enviando a Modal API...")
        
        response = send_to_modal(json_data, api_url, api_key)
        
        if verbose:
            print(f"✅ Respuesta de Modal:")
            print(json.dumps(response, indent=2))
        
        return response
    
    except Exception as e:
        if verbose:
            print(f"❌ Error: {e}")
        raise


def ingest_batch_from_yaml(yaml_string: str, api_url: Optional[str] = None, api_key: Optional[str] = None, verbose: bool = False) -> list:
    """
    Procesar múltiples transacciones desde un YAML
    
    Formatos aceptados:
    1. Lista directa:
       - monto: 100
         descripcion: Café
       - monto: 200
         descripcion: Almuerzo
    
    2. Con clave 'transacciones':
       transacciones:
         - monto: 100
           descripcion: Café
    """
    try:
        data = yaml.safe_load(yaml_string)
        
        if not data:
            raise ValueError("YAML vacío")
        
        # Determinar formato
        transactions = []
        
        if isinstance(data, list):
            # Lista directa
            transactions = data
        elif isinstance(data, dict):
            if 'transacciones' in data:
                transactions = data['transacciones']
            elif 'transactions' in data:
                transactions = data['transactions']
            elif 'monto' in data or 'amount' in data:
                # Una sola transacción
                transactions = [data]
            else:
                raise ValueError("Formato de YAML no reconocido")
        else:
            raise ValueError("Formato de YAML no reconocido")
        
        # Procesar cada transacción
        results = []
        
        for i, trans_data in enumerate(transactions, 1):
            try:
                # Convertir a YAML string individual
                trans_yaml = yaml.dump(trans_data)
                
                if verbose:
                    print(f"\n📝 Transacción {i}/{len(transactions)}:")
                
                result = ingest_from_yaml(trans_yaml, api_url, api_key, verbose=False)
                
                if verbose:
                    print(f"   ✅ {result.get('id', 'unknown')}: {trans_data.get('descripcion', trans_data.get('description', 'Sin descripción'))}")
                
                results.append({
                    'success': True,
                    'index': i,
                    'result': result
                })
            
            except Exception as e:
                if verbose:
                    print(f"   ❌ Error: {e}")
                
                results.append({
                    'success': False,
                    'index': i,
                    'error': str(e)
                })
        
        # Resumen
        success_count = sum(1 for r in results if r['success'])
        error_count = len(results) - success_count
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"📊 Resumen:")
            print(f"   ✅ Exitosas: {success_count}")
            print(f"   ❌ Errores: {error_count}")
            print(f"   📝 Total: {len(results)}")
            print(f"{'='*60}")
        
        return results
    
    except Exception as e:
        if verbose:
            print(f"❌ Error: {e}")
        raise


def main():
    """CLI principal"""
    parser = argparse.ArgumentParser(
        description='Convertir YAML a JSON y enviar a Modal API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Desde argumento directo
  python yaml_to_modal.py --yaml "monto: 5000\\ndescripcion: Café"

  # Desde archivo
  python yaml_to_modal.py --file mis_gastos.yaml

  # Desde stdin (para OpenClaw)
  echo "monto: 100" | python yaml_to_modal.py --stdin

  # Batch (múltiples transacciones)
  python yaml_to_modal.py --file transacciones.yaml --batch

Variables de entorno necesarias:
  MODAL_API_URL: URL de la API en Modal
  FINANZAS_API_KEY: API key para autenticación
  
Puedes configurarlas en un archivo .env en el mismo directorio.
        """
    )
    
    # Input sources (mutuamente exclusivos)
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--yaml', type=str, help='YAML como string')
    input_group.add_argument('--file', type=str, help='Archivo YAML')
    input_group.add_argument('--stdin', action='store_true', help='Leer desde stdin')
    
    # Opciones
    parser.add_argument('--api-url', type=str, help='URL de la API (override env)')
    parser.add_argument('--api-key', type=str, help='API key (override env)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    parser.add_argument('--batch', action='store_true', help='Procesar múltiples transacciones')
    parser.add_argument('--dry-run', action='store_true', help='Solo convertir, no enviar')
    parser.add_argument('--delete', type=str, help='Eliminar transacción por ID')
    parser.add_argument('--delete-all', action='store_true', help='Eliminar TODAS las transacciones (requiere confirmación)')
    
    args = parser.parse_args()
    
    # Cargar .env
    load_env()
    
    # Manejar delete antes que nada
    if args.delete:
        try:
            result = delete_transaction(
                args.delete,
                api_url=args.api_url,
                api_key=args.api_key,
                verbose=args.verbose
            )
            if not args.verbose:
                print(json.dumps(result, indent=2))
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    if args.delete_all:
        try:
            print("⚠️  ¿Estás seguro que quieres eliminar TODAS las transacciones?")
            print("   Escribe 'SI' para confirmar:")
            confirm = input().strip()
            
            if confirm != 'SI':
                print("❌ Cancelado")
                sys.exit(1)
            
            result = delete_all_transactions(
                api_url=args.api_url,
                api_key=args.api_key,
                verbose=args.verbose
            )
            if not args.verbose:
                print(json.dumps(result, indent=2))
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Obtener YAML input
    yaml_string = None
    
    if args.yaml:
        yaml_string = args.yaml
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                yaml_string = f.read()
        except Exception as e:
            print(f"❌ Error al leer archivo: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.stdin:
        yaml_string = sys.stdin.read()
    
    # Si no hay YAML input y no es delete, error
    if not yaml_string or not yaml_string.strip():
        if not args.dry_run:
            print("❌ YAML vacío", file=sys.stderr)
            sys.exit(1)
    
    # Dry run (solo convertir)
    if args.dry_run:
        try:
            json_data = convert_yaml_to_json(yaml_string)
            print(json.dumps(json_data, indent=2))
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Procesar
    try:
        if args.batch:
            results = ingest_batch_from_yaml(
                yaml_string,
                api_url=args.api_url,
                api_key=args.api_key,
                verbose=args.verbose
            )
            
            # Exit code basado en resultados
            success_count = sum(1 for r in results if r['success'])
            if success_count == len(results):
                sys.exit(0)
            elif success_count > 0:
                sys.exit(2)  # Partial success
            else:
                sys.exit(1)  # All failed
        else:
            result = ingest_from_yaml(
                yaml_string,
                api_url=args.api_url,
                api_key=args.api_key,
                verbose=args.verbose
            )
            
            if not args.verbose:
                print(json.dumps(result, indent=2))
            
            sys.exit(0)
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
