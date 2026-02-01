"""
Tests para yaml_to_modal.py
"""
import pytest
from yaml_to_modal import convert_yaml_to_json


def test_minimal_yaml():
    """Test conversión mínima: solo monto"""
    yaml_str = "monto: 100"
    result = convert_yaml_to_json(yaml_str)
    
    assert result['amount'] == 100.0
    assert result['currency'] == 'ARS'
    assert result['is_income'] is False


def test_full_yaml_spanish():
    """Test conversión completa en español"""
    yaml_str = """
monto: 5000
moneda: ARS
tipo_gasto: variable
metodo_pago: tarjeta_credito
fuente_dinero: Tarjeta Canadá
descripcion: Supermercado
categoria: comida
notas: Compra mensual
es_ingreso: false
"""
    result = convert_yaml_to_json(yaml_str)
    
    assert result['amount'] == 5000.0
    assert result['currency'] == 'ARS'
    assert result['expense_type'] == 'variable'
    assert result['payment_method'] == 'tarjeta_credito'
    assert result['money_source'] == 'Tarjeta Canadá'
    assert result['description'] == 'Supermercado'
    assert result['category'] == 'comida'
    assert result['notes'] == 'Compra mensual'
    assert result['is_income'] is False


def test_english_fields():
    """Test que también acepta campos en inglés"""
    yaml_str = """
amount: 100
currency: USD
description: Test
category: test
"""
    result = convert_yaml_to_json(yaml_str)
    
    assert result['amount'] == 100.0
    assert result['currency'] == 'USD'
    assert result['description'] == 'Test'
    assert result['category'] == 'test'


def test_income_transaction():
    """Test ingreso"""
    yaml_str = """
monto: 50000
es_ingreso: true
descripcion: Sueldo
"""
    result = convert_yaml_to_json(yaml_str)
    
    assert result['amount'] == 50000.0
    assert result['is_income'] is True
    assert result['description'] == 'Sueldo'


def test_currency_conversion():
    """Test conversión de moneda"""
    yaml_str = """
monto: 50
moneda: CAD
tasa_cambio: 880
monto_convertido: 44000
moneda_convertida: ARS
"""
    result = convert_yaml_to_json(yaml_str)
    
    assert result['amount'] == 50.0
    assert result['currency'] == 'CAD'
    assert result['exchange_rate'] == 880.0
    assert result['converted_amount'] == 44000.0
    assert result['converted_currency'] == 'ARS'


def test_missing_amount():
    """Test que falla si no hay monto"""
    yaml_str = "descripcion: Test sin monto"
    
    with pytest.raises(ValueError, match="monto"):
        convert_yaml_to_json(yaml_str)


def test_empty_yaml():
    """Test YAML vacío"""
    yaml_str = ""
    
    with pytest.raises(ValueError, match="vacío"):
        convert_yaml_to_json(yaml_str)


def test_invalid_yaml():
    """Test YAML inválido"""
    yaml_str = "monto: [invalid yaml structure"
    
    with pytest.raises(ValueError):
        convert_yaml_to_json(yaml_str)


def test_decimal_amounts():
    """Test montos decimales"""
    yaml_str = """
monto: 123.45
tasa_cambio: 1050.50
"""
    result = convert_yaml_to_json(yaml_str)
    
    assert result['amount'] == 123.45
    assert result['exchange_rate'] == 1050.50


def test_optional_fields_as_none():
    """Test que campos opcionales vacíos no aparecen o son None"""
    yaml_str = """
monto: 100
descripcion: Test
"""
    result = convert_yaml_to_json(yaml_str)
    
    # Solo debería tener los campos especificados + defaults
    assert 'amount' in result
    assert 'description' in result
    assert 'currency' in result  # default
    assert 'is_income' in result  # default


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
