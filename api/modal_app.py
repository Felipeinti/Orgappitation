"""
Modal API para aplicación de finanzas personales
FastAPI + SQLite en Modal Volume
"""
import os
import sqlite3
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import modal
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

# Configuración de Modal
app = modal.App("finanzas-api")

# Volume persistente para SQLite
volume = modal.Volume.from_name("finanzas-data", create_if_missing=True)

# Path de la base de datos en el volume
DB_PATH = "/data/finanzas.db"

# Imagen con dependencias
image = modal.Image.debian_slim().pip_install(
    "fastapi",
    "pydantic",
    "python-multipart"
)


# ============================================================================
# Modelos Pydantic (en inglés para compatibilidad con SQL)
# ============================================================================

class TransactionCreate(BaseModel):
    """Modelo para crear una transacción"""
    amount: float = Field(..., gt=0, description="Monto de la transacción (debe ser mayor a 0)")
    currency: str = Field(default="ARS", description="Moneda (ARS, USD, CAD, ETH)")
    
    # Campos opcionales
    expense_type: Optional[str] = Field(None, description="Tipo de gasto: fixed o variable")
    category: Optional[str] = Field(None, description="Categoría del gasto")
    is_income: bool = Field(default=False, description="Si es un ingreso (True) o egreso (False)")
    
    payment_method: Optional[str] = Field(None, description="Método de pago")
    money_source: Optional[str] = Field(None, description="Fuente del dinero (texto libre)")
    
    description: Optional[str] = Field(None, description="Descripción de la transacción")
    notes: Optional[str] = Field(None, description="Notas adicionales")
    
    # Conversión de moneda (opcional)
    exchange_rate: Optional[float] = Field(None, gt=0, description="Tasa de cambio")
    converted_amount: Optional[float] = Field(None, gt=0, description="Monto convertido")
    converted_currency: Optional[str] = Field(None, description="Moneda convertida")
    
    # Fecha opcional (si no se provee, se usa la actual)
    date: Optional[str] = Field(None, description="Fecha en formato ISO (YYYY-MM-DD HH:MM:SS)")
    
    @field_validator('currency', 'converted_currency')
    @classmethod
    def validate_currency(cls, v):
        """Validar que la moneda sea válida"""
        if v and v not in ['ARS', 'USD', 'CAD', 'ETH', 'BTC']:
            raise ValueError(f"Moneda no válida: {v}. Debe ser ARS, USD, CAD, ETH o BTC")
        return v


class TransactionResponse(BaseModel):
    """Respuesta al crear una transacción"""
    id: str
    success: bool
    message: str


class QueryRequest(BaseModel):
    """Request para ejecutar una query SQL"""
    sql: str = Field(..., description="Query SQL a ejecutar (solo SELECT)")
    
    @field_validator('sql')
    @classmethod
    def validate_sql(cls, v):
        """Validar que solo sea un SELECT y no contenga operaciones peligrosas"""
        v_upper = v.upper().strip()
        
        # Debe empezar con SELECT
        if not v_upper.startswith('SELECT'):
            raise ValueError("Solo se permiten queries SELECT")
        
        # No debe contener operaciones peligrosas
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'PRAGMA', 'ATTACH', 'DETACH'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in v_upper:
                raise ValueError(f"Operación no permitida: {keyword}")
        
        return v


class QueryResponse(BaseModel):
    """Respuesta a una query"""
    success: bool
    columns: List[str]
    rows: List[List[Any]]
    row_count: int


class StatsResponse(BaseModel):
    """Respuesta de estadísticas"""
    total_income: float
    total_expenses: float
    balance: float
    total_transactions: int
    expense_count: int
    income_count: int


# ============================================================================
# Funciones de base de datos
# ============================================================================

def init_database():
    """Inicializar la base de datos con el schema"""
    with get_db_connection() as conn:
        # Leer y ejecutar el schema SQL
        schema_path = "/root/sql_schema.sql"
        
        # Si existe el archivo de schema, ejecutarlo
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
                conn.executescript(schema)
        else:
            # Schema básico si no existe el archivo
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
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
                
                CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
                CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
                CREATE INDEX IF NOT EXISTS idx_transactions_is_income ON transactions(is_income);
            """)
        
        conn.commit()


@contextmanager
def get_db_connection():
    """Context manager para conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def generate_id() -> str:
    """Generar ID único para transacción"""
    from uuid import uuid4
    return str(uuid4())


# ============================================================================
# Autenticación
# ============================================================================

def verify_api_key(x_api_key: str = Header(...)):
    """Verificar API key"""
    expected_key = os.environ.get("FINANZAS_API_KEY", "")
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key no configurada en el servidor")
    
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    return x_api_key


# ============================================================================
# FastAPI app
# ============================================================================

web_app = FastAPI(
    title="Finanzas API",
    description="API para gestión de finanzas personales",
    version="1.0.0"
)


@web_app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "app": "Finanzas API",
        "version": "1.0.0",
        "status": "running"
    }


@web_app.get("/health")
async def health_check():
    """Health check - verifica que la DB esté accesible"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


@web_app.post("/ingest", response_model=TransactionResponse)
async def ingest_transaction(
    transaction: TransactionCreate,
    api_key: str = Depends(verify_api_key)
):
    """
    Insertar una nueva transacción
    
    Requiere header: X-API-Key
    """
    try:
        # Generar ID
        transaction_id = generate_id()
        
        # Usar fecha actual si no se provee
        date = transaction.date if transaction.date else datetime.now().isoformat()
        
        # Insertar en la base de datos
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO transactions (
                    id, date, amount, currency, expense_type, category,
                    is_income, payment_method, money_source, description,
                    notes, exchange_rate, converted_amount, converted_currency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                date,
                transaction.amount,
                transaction.currency,
                transaction.expense_type,
                transaction.category,
                1 if transaction.is_income else 0,
                transaction.payment_method,
                transaction.money_source,
                transaction.description,
                transaction.notes,
                transaction.exchange_rate,
                transaction.converted_amount,
                transaction.converted_currency
            ))
            conn.commit()
        
        return TransactionResponse(
            id=transaction_id,
            success=True,
            message=f"Transacción creada exitosamente"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al insertar transacción: {str(e)}")


@web_app.post("/query", response_model=QueryResponse)
async def execute_query(
    query: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Ejecutar una query SQL (solo SELECT)
    
    Requiere header: X-API-Key
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(query.sql)
            rows = cursor.fetchall()
            
            # Obtener nombres de columnas
            columns = [description[0] for description in cursor.description] if cursor.description else []
            
            # Convertir rows a lista de listas
            rows_list = [list(row) for row in rows]
            
            return QueryResponse(
                success=True,
                columns=columns,
                rows=rows_list,
                row_count=len(rows_list)
            )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al ejecutar query: {str(e)}")


@web_app.get("/stats", response_model=StatsResponse)
async def get_stats(api_key: str = Depends(verify_api_key)):
    """
    Obtener estadísticas generales
    
    Requiere header: X-API-Key
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    SUM(CASE WHEN is_income = 1 THEN amount ELSE 0 END) as total_income,
                    SUM(CASE WHEN is_income = 0 THEN amount ELSE 0 END) as total_expenses,
                    SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END) as balance,
                    COUNT(*) as total_transactions,
                    COUNT(CASE WHEN is_income = 0 THEN 1 END) as expense_count,
                    COUNT(CASE WHEN is_income = 1 THEN 1 END) as income_count
                FROM transactions
            """)
            
            row = cursor.fetchone()
            
            return StatsResponse(
                total_income=float(row['total_income'] or 0),
                total_expenses=float(row['total_expenses'] or 0),
                balance=float(row['balance'] or 0),
                total_transactions=int(row['total_transactions'] or 0),
                expense_count=int(row['expense_count'] or 0),
                income_count=int(row['income_count'] or 0)
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")


@web_app.get("/transactions/recent")
async def get_recent_transactions(
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """
    Obtener últimas N transacciones
    
    Requiere header: X-API-Key
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    id, date, amount, currency, expense_type, category,
                    is_income, payment_method, money_source, description
                FROM transactions
                ORDER BY date DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            transactions = []
            for row in rows:
                transactions.append({
                    "id": row['id'],
                    "date": row['date'],
                    "amount": row['amount'],
                    "currency": row['currency'],
                    "expense_type": row['expense_type'],
                    "category": row['category'],
                    "is_income": bool(row['is_income']),
                    "payment_method": row['payment_method'],
                    "money_source": row['money_source'],
                    "description": row['description']
                })
            
            return {
                "success": True,
                "count": len(transactions),
                "transactions": transactions
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener transacciones: {str(e)}")


@web_app.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Eliminar una transacción por ID
    
    Requiere header: X-API-Key
    """
    try:
        with get_db_connection() as conn:
            # Verificar que existe
            cursor = conn.execute("SELECT id FROM transactions WHERE id = ?", (transaction_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Transacción no encontrada")
            
            # Eliminar
            conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
            
            return {
                "success": True,
                "message": f"Transacción {transaction_id} eliminada exitosamente"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar transacción: {str(e)}")


@web_app.delete("/transactions")
async def delete_all_transactions(
    confirm: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Eliminar TODAS las transacciones
    
    Requiere:
    - Header: X-API-Key
    - Query param: confirm=DELETE_ALL
    
    Ejemplo: DELETE /transactions?confirm=DELETE_ALL
    """
    if confirm != "DELETE_ALL":
        raise HTTPException(
            status_code=400, 
            detail="Para eliminar todas las transacciones, debes pasar ?confirm=DELETE_ALL"
        )
    
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as count FROM transactions")
            count = cursor.fetchone()['count']
            
            conn.execute("DELETE FROM transactions")
            conn.commit()
            
            return {
                "success": True,
                "message": f"{count} transacciones eliminadas exitosamente"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar transacciones: {str(e)}")


# ============================================================================
# Modal function
# ============================================================================

@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("finanzas-api-secret")],
    min_containers=1,  # Mantener 1 contenedor caliente para respuestas rápidas
    timeout=300  # 5 minutos de timeout
)
@modal.asgi_app()
def fastapi_app():
    """Modal function que sirve la FastAPI app"""
    # Inicializar la base de datos si no existe
    if not os.path.exists(DB_PATH):
        print(f"Inicializando base de datos en {DB_PATH}")
        init_database()
        volume.commit()
    
    return web_app


# ============================================================================
# Función para inicializar DB manualmente
# ============================================================================

@app.function(
    image=image,
    volumes={"/data": volume},
)
def init_db():
    """Función para inicializar la base de datos manualmente"""
    print(f"Inicializando base de datos en {DB_PATH}...")
    init_database()
    volume.commit()
    print("Base de datos inicializada exitosamente!")
