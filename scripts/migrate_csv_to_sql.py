#!/usr/bin/env python3
"""
Script de migración: CSV → SQLite → Modal API
Migra datos existentes del sistema CSV al nuevo sistema SQL en Modal
"""
import os
import csv
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import requests


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


def read_csv_transactions(csv_path: str) -> List[Dict[str, Any]]:
    """
    Leer transacciones desde CSV
    """
    transactions = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                transactions.append(row)
        
        return transactions
    except FileNotFoundError:
        print(f"⚠️  Archivo no encontrado: {csv_path}")
        return []
    except Exception as e:
        print(f"❌ Error al leer CSV: {e}")
        return []


def convert_csv_to_sql_format(csv_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convertir una fila de CSV al formato SQL (en inglés)
    
    Mapeo:
    - id → id (mantener)
    - fecha → date
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
    """
    sql_row = {}
    
    # Mapeo directo
    mapping = {
        'id': 'id',
        'fecha': 'date',
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
        'moneda_convertida': 'converted_currency'
    }
    
    for csv_key, sql_key in mapping.items():
        if csv_key in csv_row and csv_row[csv_key]:
            value = csv_row[csv_key]
            
            # Convertir tipos
            if sql_key in ['amount', 'exchange_rate', 'converted_amount']:
                try:
                    sql_row[sql_key] = float(value)
                except (ValueError, TypeError):
                    sql_row[sql_key] = None
            elif sql_key == 'is_income':
                # Convertir string 'True'/'False' a booleano
                sql_row[sql_key] = value.lower() in ['true', '1', 'yes']
            else:
                # String, mantener como está (pero convertir vacíos a None)
                sql_row[sql_key] = value if value else None
    
    # Validaciones
    if 'amount' not in sql_row or not sql_row['amount']:
        raise ValueError(f"Transacción sin monto válido: {csv_row.get('id', 'unknown')}")
    
    # Defaults
    if 'currency' not in sql_row or not sql_row['currency']:
        sql_row['currency'] = 'ARS'
    
    if 'is_income' not in sql_row:
        sql_row['is_income'] = False
    
    return sql_row


def create_local_sqlite_from_csv(csv_path: str, db_path: str, schema_path: str) -> int:
    """
    Crear base de datos SQLite local desde CSV
    
    Returns:
        Número de transacciones insertadas
    """
    print(f"\n📊 Creando base de datos SQLite local...")
    print(f"   CSV: {csv_path}")
    print(f"   DB: {db_path}")
    
    # Leer transacciones del CSV
    csv_transactions = read_csv_transactions(csv_path)
    
    if not csv_transactions:
        print(f"⚠️  No se encontraron transacciones en {csv_path}")
        return 0
    
    print(f"   Encontradas {len(csv_transactions)} transacciones en CSV")
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
    
    # Crear base de datos
    conn = sqlite3.connect(db_path)
    
    try:
        # Ejecutar schema
        if os.path.exists(schema_path):
            print(f"   Ejecutando schema desde {schema_path}...")
            with open(schema_path, 'r') as f:
                schema = f.read()
                conn.executescript(schema)
        else:
            print(f"   ⚠️  Schema no encontrado en {schema_path}, usando schema básico...")
            # Schema mínimo
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'ARS',
                    expense_type TEXT,
                    category TEXT,
                    is_income INTEGER NOT NULL DEFAULT 0,
                    payment_method TEXT,
                    money_source TEXT,
                    description TEXT,
                    notes TEXT,
                    exchange_rate REAL,
                    converted_amount REAL,
                    converted_currency TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        # Insertar transacciones
        inserted = 0
        errors = 0
        
        for i, csv_row in enumerate(csv_transactions, 1):
            try:
                sql_row = convert_csv_to_sql_format(csv_row)
                
                # Insertar
                conn.execute("""
                    INSERT INTO transactions (
                        id, date, amount, currency, expense_type, category,
                        is_income, payment_method, money_source, description,
                        notes, exchange_rate, converted_amount, converted_currency
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sql_row.get('id'),
                    sql_row.get('date'),
                    sql_row.get('amount'),
                    sql_row.get('currency', 'ARS'),
                    sql_row.get('expense_type'),
                    sql_row.get('category'),
                    1 if sql_row.get('is_income') else 0,
                    sql_row.get('payment_method'),
                    sql_row.get('money_source'),
                    sql_row.get('description'),
                    sql_row.get('notes'),
                    sql_row.get('exchange_rate'),
                    sql_row.get('converted_amount'),
                    sql_row.get('converted_currency')
                ))
                
                inserted += 1
                
            except Exception as e:
                print(f"   ⚠️  Error en fila {i}: {e}")
                errors += 1
        
        conn.commit()
        
        print(f"   ✅ Insertadas {inserted} transacciones")
        if errors > 0:
            print(f"   ⚠️  {errors} errores")
        
        return inserted
    
    finally:
        conn.close()


def upload_to_modal(db_path: str, api_url: str, api_key: str, batch_size: int = 10) -> Dict[str, int]:
    """
    Subir transacciones de SQLite local a Modal API
    
    Returns:
        Dict con estadísticas: {success: int, errors: int}
    """
    print(f"\n📤 Subiendo transacciones a Modal API...")
    print(f"   API: {api_url}")
    
    # Conectar a SQLite local
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Leer todas las transacciones
        cursor = conn.execute("""
            SELECT 
                id, date, amount, currency, expense_type, category,
                is_income, payment_method, money_source, description,
                notes, exchange_rate, converted_amount, converted_currency
            FROM transactions
            ORDER BY date
        """)
        
        transactions = cursor.fetchall()
        total = len(transactions)
        
        print(f"   Total a subir: {total}")
        
        # Subir en batches
        success = 0
        errors = 0
        
        ingest_url = api_url.rstrip('/') + '/ingest'
        headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        for i, row in enumerate(transactions, 1):
            try:
                # Convertir a dict
                data = {
                    'amount': float(row['amount']),
                    'currency': row['currency'] or 'ARS',
                    'expense_type': row['expense_type'],
                    'category': row['category'],
                    'is_income': bool(row['is_income']),
                    'payment_method': row['payment_method'],
                    'money_source': row['money_source'],
                    'description': row['description'],
                    'notes': row['notes'],
                    'date': row['date']
                }
                
                # Agregar campos opcionales solo si existen
                if row['exchange_rate']:
                    data['exchange_rate'] = float(row['exchange_rate'])
                if row['converted_amount']:
                    data['converted_amount'] = float(row['converted_amount'])
                if row['converted_currency']:
                    data['converted_currency'] = row['converted_currency']
                
                # POST a la API
                response = requests.post(ingest_url, json=data, headers=headers)
                response.raise_for_status()
                
                success += 1
                
                # Mostrar progreso cada 10 transacciones
                if i % 10 == 0 or i == total:
                    print(f"   Progreso: {i}/{total} ({success} exitosas, {errors} errores)")
            
            except Exception as e:
                print(f"   ⚠️  Error en transacción {row['id']}: {e}")
                errors += 1
        
        print(f"\n   ✅ Completado: {success} exitosas, {errors} errores")
        
        return {'success': success, 'errors': errors}
    
    finally:
        conn.close()


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrar transacciones de CSV a Modal API via SQLite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Proceso de migración:
  1. Leer transacciones desde CSV
  2. Convertir formato español → inglés
  3. Crear SQLite local con schema correcto
  4. Subir a Modal API via /ingest endpoint

Ejemplo:
  python migrate_csv_to_sql.py --csv data/transacciones.csv --upload

Variables de entorno:
  MODAL_API_URL: URL de la API en Modal
  FINANZAS_API_KEY: API key para autenticación
        """
    )
    
    parser.add_argument('--csv', type=str, default='data/transacciones.csv',
                       help='Path al CSV de transacciones (default: data/transacciones.csv)')
    parser.add_argument('--db', type=str, default='migrated_data.db',
                       help='Path a la DB SQLite local (default: migrated_data.db)')
    parser.add_argument('--schema', type=str, default='sql_schema.sql',
                       help='Path al archivo de schema SQL (default: sql_schema.sql)')
    parser.add_argument('--upload', action='store_true',
                       help='Subir a Modal API después de crear la DB local')
    parser.add_argument('--api-url', type=str,
                       help='URL de la API (override env MODAL_API_URL)')
    parser.add_argument('--api-key', type=str,
                       help='API key (override env FINANZAS_API_KEY)')
    
    args = parser.parse_args()
    
    # Cargar .env
    load_env()
    
    # Verificar que el CSV exista
    if not os.path.exists(args.csv):
        print(f"❌ Archivo CSV no encontrado: {args.csv}")
        print(f"   Verifica la ruta o crea transacciones primero")
        sys.exit(1)
    
    # Paso 1: Crear SQLite local desde CSV
    print("="*70)
    print("MIGRACIÓN CSV → SQLite → Modal")
    print("="*70)
    
    inserted = create_local_sqlite_from_csv(args.csv, args.db, args.schema)
    
    if inserted == 0:
        print("\n❌ No se insertaron transacciones. Verifica el CSV.")
        sys.exit(1)
    
    print(f"\n✅ Base de datos local creada exitosamente: {args.db}")
    print(f"   {inserted} transacciones insertadas")
    
    # Paso 2: Subir a Modal (opcional)
    if args.upload:
        api_url = args.api_url or os.environ.get('MODAL_API_URL')
        api_key = args.api_key or os.environ.get('FINANZAS_API_KEY')
        
        if not api_url:
            print("\n❌ MODAL_API_URL no configurada")
            print("   Set en .env o usa --api-url")
            sys.exit(1)
        
        if not api_key:
            print("\n❌ FINANZAS_API_KEY no configurada")
            print("   Set en .env o usa --api-key")
            sys.exit(1)
        
        stats = upload_to_modal(args.db, api_url, api_key)
        
        print("\n" + "="*70)
        print("RESUMEN DE MIGRACIÓN")
        print("="*70)
        print(f"CSV leído:           {args.csv}")
        print(f"SQLite local:        {args.db}")
        print(f"Subidas a Modal:     {stats['success']}")
        print(f"Errores:             {stats['errors']}")
        print("="*70)
        
        if stats['errors'] > 0:
            sys.exit(2)  # Partial success
        else:
            print("\n🎉 Migración completada exitosamente!")
            sys.exit(0)
    else:
        print("\n💡 Para subir a Modal, ejecuta:")
        print(f"   python {sys.argv[0]} --csv {args.csv} --db {args.db} --upload")


if __name__ == "__main__":
    main()
