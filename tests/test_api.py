"""
Tests de integración para la API de Modal
Requiere que la API esté desplegada y accesible

Para ejecutar estos tests:
1. Desplegar la API: modal deploy modal_app.py
2. Configurar .env con MODAL_API_URL y FINANZAS_API_KEY
3. Ejecutar: pytest test_api.py -v
"""
import os
import pytest
import requests
from datetime import datetime


# Cargar configuración
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

API_URL = os.environ.get('MODAL_API_URL')
API_KEY = os.environ.get('FINANZAS_API_KEY')

# Skip tests si no hay configuración
pytestmark = pytest.mark.skipif(
    not API_URL or not API_KEY,
    reason="MODAL_API_URL y FINANZAS_API_KEY deben estar configurados en .env"
)


@pytest.fixture
def headers():
    """Headers para requests"""
    return {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }


def test_health_check():
    """Test endpoint /health"""
    response = requests.get(f"{API_URL}/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'


def test_root_endpoint():
    """Test endpoint raíz"""
    response = requests.get(API_URL)
    assert response.status_code == 200
    
    data = response.json()
    assert 'app' in data
    assert 'version' in data


def test_ingest_transaction(headers):
    """Test insertar transacción"""
    transaction = {
        'amount': 100,
        'currency': 'ARS',
        'description': 'Test transaction',
        'category': 'test'
    }
    
    response = requests.post(
        f"{API_URL}/ingest",
        headers=headers,
        json=transaction
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data['success'] is True
    assert 'id' in data
    assert len(data['id']) > 0


def test_ingest_without_auth():
    """Test que ingest requiere autenticación"""
    transaction = {
        'amount': 100,
        'description': 'Test'
    }
    
    response = requests.post(
        f"{API_URL}/ingest",
        json=transaction
    )
    
    assert response.status_code == 403  # Forbidden or 401


def test_ingest_invalid_api_key():
    """Test con API key inválida"""
    headers = {
        'X-API-Key': 'invalid_key_123',
        'Content-Type': 'application/json'
    }
    
    transaction = {
        'amount': 100,
        'description': 'Test'
    }
    
    response = requests.post(
        f"{API_URL}/ingest",
        headers=headers,
        json=transaction
    )
    
    assert response.status_code == 401


def test_ingest_missing_amount(headers):
    """Test que falla sin amount"""
    transaction = {
        'description': 'Test without amount'
    }
    
    response = requests.post(
        f"{API_URL}/ingest",
        headers=headers,
        json=transaction
    )
    
    assert response.status_code == 422  # Validation error


def test_query_safe_select(headers):
    """Test ejecutar query SELECT"""
    query = {
        'sql': 'SELECT COUNT(*) as count FROM transactions'
    }
    
    response = requests.post(
        f"{API_URL}/query",
        headers=headers,
        json=query
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data['success'] is True
    assert 'columns' in data
    assert 'rows' in data
    assert data['row_count'] >= 0


def test_query_unsafe_delete(headers):
    """Test que rechaza DELETE"""
    query = {
        'sql': 'DELETE FROM transactions WHERE id = "123"'
    }
    
    response = requests.post(
        f"{API_URL}/query",
        headers=headers,
        json=query
    )
    
    assert response.status_code == 422  # Validation error


def test_query_unsafe_update(headers):
    """Test que rechaza UPDATE"""
    query = {
        'sql': 'UPDATE transactions SET amount = 0'
    }
    
    response = requests.post(
        f"{API_URL}/query",
        headers=headers,
        json=query
    )
    
    assert response.status_code == 422


def test_stats_endpoint(headers):
    """Test endpoint /stats"""
    response = requests.get(
        f"{API_URL}/stats",
        headers=headers
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert 'total_income' in data
    assert 'total_expenses' in data
    assert 'balance' in data
    assert 'total_transactions' in data
    assert 'expense_count' in data
    assert 'income_count' in data


def test_recent_transactions(headers):
    """Test endpoint /transactions/recent"""
    response = requests.get(
        f"{API_URL}/transactions/recent?limit=5",
        headers=headers
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data['success'] is True
    assert 'transactions' in data
    assert 'count' in data
    assert data['count'] <= 5


def test_full_flow(headers):
    """Test flujo completo: insert + query + stats"""
    # 1. Insertar transacción de test
    transaction = {
        'amount': 999.99,
        'currency': 'ARS',
        'description': 'Integration test transaction',
        'category': 'test',
        'payment_method': 'cash'
    }
    
    response = requests.post(
        f"{API_URL}/ingest",
        headers=headers,
        json=transaction
    )
    assert response.status_code == 200
    transaction_id = response.json()['id']
    
    # 2. Verificar que aparece en query
    query = {
        'sql': f"SELECT * FROM transactions WHERE id = '{transaction_id}'"
    }
    
    response = requests.post(
        f"{API_URL}/query",
        headers=headers,
        json=query
    )
    assert response.status_code == 200
    data = response.json()
    assert data['row_count'] == 1
    assert data['rows'][0][2] == 999.99  # amount column
    
    # 3. Verificar stats
    response = requests.get(
        f"{API_URL}/stats",
        headers=headers
    )
    assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
