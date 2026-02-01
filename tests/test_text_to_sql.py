"""
Tests para text_to_sql.py
"""
import pytest
from text_to_sql import is_safe_query


def test_safe_select_query():
    """Test query SELECT seguro"""
    sql = "SELECT * FROM transactions WHERE is_income = 0"
    assert is_safe_query(sql) is True


def test_safe_select_with_aggregate():
    """Test SELECT con agregaciones"""
    sql = "SELECT SUM(amount) FROM transactions GROUP BY category"
    assert is_safe_query(sql) is True


def test_safe_select_with_join():
    """Test SELECT con JOIN"""
    sql = """
    SELECT t.amount, c.name 
    FROM transactions t 
    LEFT JOIN categories c ON t.category = c.name
    """
    assert is_safe_query(sql) is True


def test_unsafe_delete():
    """Test que DELETE es rechazado"""
    sql = "DELETE FROM transactions WHERE id = '123'"
    assert is_safe_query(sql) is False


def test_unsafe_update():
    """Test que UPDATE es rechazado"""
    sql = "UPDATE transactions SET amount = 0 WHERE id = '123'"
    assert is_safe_query(sql) is False


def test_unsafe_insert():
    """Test que INSERT es rechazado"""
    sql = "INSERT INTO transactions (amount) VALUES (100)"
    assert is_safe_query(sql) is False


def test_unsafe_drop():
    """Test que DROP es rechazado"""
    sql = "DROP TABLE transactions"
    assert is_safe_query(sql) is False


def test_unsafe_alter():
    """Test que ALTER es rechazado"""
    sql = "ALTER TABLE transactions ADD COLUMN test TEXT"
    assert is_safe_query(sql) is False


def test_unsafe_create():
    """Test que CREATE es rechazado"""
    sql = "CREATE TABLE test (id TEXT)"
    assert is_safe_query(sql) is False


def test_unsafe_truncate():
    """Test que TRUNCATE es rechazado"""
    sql = "TRUNCATE TABLE transactions"
    assert is_safe_query(sql) is False


def test_unsafe_pragma():
    """Test que PRAGMA es rechazado"""
    sql = "PRAGMA table_info(transactions)"
    assert is_safe_query(sql) is False


def test_select_with_dangerous_keyword_in_string():
    """Test que keyword en string literal no causa falso positivo"""
    # Este es un edge case: la palabra DELETE aparece en un string
    sql = "SELECT description FROM transactions WHERE description LIKE '%DELETE%'"
    # Este test debería fallar con la implementación actual (que es conservadora)
    # En producción, podrías usar un parser SQL real para evitar falsos positivos
    assert is_safe_query(sql) is False  # Conservador: rechaza


def test_case_insensitive():
    """Test que detección es case-insensitive"""
    sql = "delete from transactions"
    assert is_safe_query(sql) is False
    
    sql = "DeLeTe FrOm transactions"
    assert is_safe_query(sql) is False


def test_not_starting_with_select():
    """Test que queries que no empiezan con SELECT son rechazadas"""
    sql = "WITH cte AS (SELECT * FROM transactions) SELECT * FROM cte"
    # CTEs son seguros pero nuestra validación simple no los permite
    # En producción, podrías mejorar esto
    assert is_safe_query(sql) is False


def test_whitespace_handling():
    """Test manejo de espacios en blanco"""
    sql = "  SELECT * FROM transactions  "
    assert is_safe_query(sql) is True
    
    sql = "\n\nSELECT * FROM transactions\n\n"
    assert is_safe_query(sql) is True


# Tests de ejemplos de queries comunes
def test_common_query_total_expenses():
    """Test query común: total expenses"""
    sql = "SELECT SUM(amount) FROM transactions WHERE is_income = 0"
    assert is_safe_query(sql) is True


def test_common_query_by_category():
    """Test query común: by category"""
    sql = """
    SELECT category, SUM(amount) as total
    FROM transactions
    WHERE is_income = 0
    GROUP BY category
    ORDER BY total DESC
    """
    assert is_safe_query(sql) is True


def test_common_query_this_month():
    """Test query común: this month"""
    sql = """
    SELECT SUM(amount)
    FROM transactions
    WHERE is_income = 0
    AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """
    assert is_safe_query(sql) is True


def test_common_query_balance():
    """Test query común: balance"""
    sql = """
    SELECT 
        SUM(CASE WHEN is_income = 1 THEN amount ELSE 0 END) as income,
        SUM(CASE WHEN is_income = 0 THEN amount ELSE 0 END) as expenses,
        SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END) as balance
    FROM transactions
    """
    assert is_safe_query(sql) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
