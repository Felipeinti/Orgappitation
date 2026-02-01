"""
Tests para migrate_csv_to_sql.py
"""
import pytest
from migrate_csv_to_sql import convert_csv_to_sql_format


def test_convert_full_row():
    """Test conversión completa de fila CSV"""
    csv_row = {
        'id': '123-456',
        'fecha': '2026-01-31T10:30:00',
        'monto': '5000',
        'moneda': 'ARS',
        'tipo_gasto': 'variable',
        'metodo_pago': 'tarjeta_credito',
        'fuente_dinero': 'Tarjeta Canadá',
        'descripcion': 'Supermercado',
        'categoria': 'comida',
        'notas': 'Compra mensual',
        'es_ingreso': 'False',
        'tasa_cambio': '',
        'monto_convertido': '',
        'moneda_convertida': ''
    }
    
    result = convert_csv_to_sql_format(csv_row)
    
    assert result['id'] == '123-456'
    assert result['date'] == '2026-01-31T10:30:00'
    assert result['amount'] == 5000.0
    assert result['currency'] == 'ARS'
    assert result['expense_type'] == 'variable'
    assert result['payment_method'] == 'tarjeta_credito'
    assert result['money_source'] == 'Tarjeta Canadá'
    assert result['description'] == 'Supermercado'
    assert result['category'] == 'comida'
    assert result['notes'] == 'Compra mensual'
    assert result['is_income'] is False


def test_convert_minimal_row():
    """Test conversión mínima (solo campos requeridos)"""
    csv_row = {
        'id': '789',
        'fecha': '2026-01-31',
        'monto': '100',
        'moneda': '',
        'tipo_gasto': '',
        'metodo_pago': '',
        'fuente_dinero': '',
        'descripcion': '',
        'categoria': '',
        'notas': '',
        'es_ingreso': '',
    }
    
    result = convert_csv_to_sql_format(csv_row)
    
    assert result['amount'] == 100.0
    assert result['currency'] == 'ARS'  # default
    assert result['is_income'] is False  # default


def test_convert_income():
    """Test conversión de ingreso"""
    csv_row = {
        'id': '999',
        'fecha': '2026-01-31',
        'monto': '50000',
        'moneda': 'ARS',
        'es_ingreso': 'True',
        'descripcion': 'Sueldo'
    }
    
    result = convert_csv_to_sql_format(csv_row)
    
    assert result['amount'] == 50000.0
    assert result['is_income'] is True
    assert result['description'] == 'Sueldo'


def test_convert_boolean_variations():
    """Test diferentes formatos de booleanos"""
    # True variations
    for true_val in ['True', 'true', '1', 'yes', 'YES']:
        csv_row = {
            'id': '1',
            'fecha': '2026-01-31',
            'monto': '100',
            'es_ingreso': true_val
        }
        result = convert_csv_to_sql_format(csv_row)
        assert result['is_income'] is True
    
    # False variations
    for false_val in ['False', 'false', '0', 'no', 'NO', '']:
        csv_row = {
            'id': '1',
            'fecha': '2026-01-31',
            'monto': '100',
            'es_ingreso': false_val
        }
        result = convert_csv_to_sql_format(csv_row)
        assert result['is_income'] is False


def test_convert_with_exchange_rate():
    """Test conversión con tasa de cambio"""
    csv_row = {
        'id': '111',
        'fecha': '2026-01-31',
        'monto': '50',
        'moneda': 'CAD',
        'tasa_cambio': '880',
        'monto_convertido': '44000',
        'moneda_convertida': 'ARS'
    }
    
    result = convert_csv_to_sql_format(csv_row)
    
    assert result['amount'] == 50.0
    assert result['currency'] == 'CAD'
    assert result['exchange_rate'] == 880.0
    assert result['converted_amount'] == 44000.0
    assert result['converted_currency'] == 'ARS'


def test_convert_invalid_amount():
    """Test que falla con monto inválido"""
    csv_row = {
        'id': '1',
        'fecha': '2026-01-31',
        'monto': 'invalid',
        'moneda': 'ARS'
    }
    
    with pytest.raises(ValueError):
        convert_csv_to_sql_format(csv_row)


def test_convert_missing_amount():
    """Test que falla sin monto"""
    csv_row = {
        'id': '1',
        'fecha': '2026-01-31',
        'monto': '',
        'moneda': 'ARS'
    }
    
    with pytest.raises(ValueError):
        convert_csv_to_sql_format(csv_row)


def test_convert_empty_strings_to_none():
    """Test que strings vacíos se convierten a None"""
    csv_row = {
        'id': '1',
        'fecha': '2026-01-31',
        'monto': '100',
        'descripcion': '',  # Vacío
        'categoria': '',     # Vacío
        'notas': ''          # Vacío
    }
    
    result = convert_csv_to_sql_format(csv_row)
    
    assert result.get('description') is None
    assert result.get('category') is None
    assert result.get('notes') is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
