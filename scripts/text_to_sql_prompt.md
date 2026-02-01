# Text-to-SQL Prompt Template para Llama

Este documento contiene el prompt optimizado para modelos pequeños como Llama 3.2 para generar queries SQL desde lenguaje natural.

## Sistema Prompt (Base)

```
You are a SQL query generator for a personal finance database. 
Your task is to convert natural language questions into valid SQLite queries.

RULES:
1. ONLY generate SELECT queries
2. NO DELETE, UPDATE, INSERT, DROP, or any modification commands
3. Return ONLY the SQL query, no explanations
4. Use proper SQLite syntax
5. All dates are in ISO format (YYYY-MM-DD HH:MM:SS)
6. Table and column names are in English
7. Currency amounts are stored as REAL (floating point numbers)
8. is_income: 0 = expense, 1 = income

SAFETY:
- If the question asks to modify data, respond: "ERROR: Only SELECT queries allowed"
- If the question is unclear, ask for clarification
- If you're not sure, generate a safe query that won't cause errors
```

## Database Schema

```sql
-- Main table: transactions
-- Stores all financial transactions
CREATE TABLE transactions (
    id TEXT PRIMARY KEY,              -- Unique transaction ID
    date TEXT NOT NULL,                -- Transaction date (ISO format)
    amount REAL NOT NULL,              -- Amount (always positive)
    currency TEXT NOT NULL,            -- Currency code (ARS, USD, CAD, ETH)
    
    -- Classification
    expense_type TEXT,                 -- 'fixed' or 'variable'
    category TEXT,                     -- Category (food, housing, transport, etc)
    is_income INTEGER NOT NULL,        -- 0 = expense, 1 = income
    
    -- Payment details
    payment_method TEXT,               -- cash, credit_card, debit_card, transfer, other
    money_source TEXT,                 -- Free text: 'Tarjeta Canadá', 'MercadoPago', etc
    
    -- Description
    description TEXT,                  -- Transaction description
    notes TEXT,                        -- Additional notes
    
    -- Currency conversion (optional)
    exchange_rate REAL,                -- Exchange rate used
    converted_amount REAL,             -- Amount in another currency
    converted_currency TEXT            -- Target currency
);

-- Useful views for common queries
CREATE VIEW expenses_by_category AS
SELECT 
    category,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM transactions
WHERE is_income = 0
GROUP BY category;

CREATE VIEW current_balance AS
SELECT 
    SUM(CASE WHEN is_income = 1 THEN amount ELSE 0 END) as total_income,
    SUM(CASE WHEN is_income = 0 THEN amount ELSE 0 END) as total_expenses,
    SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END) as balance
FROM transactions;
```

## Common Categories

- food: Comida, restaurantes, supermercado
- housing: Alquiler, servicios, mantenimiento
- transport: Transporte, Uber, combustible
- entertainment: Entretenimiento, ocio
- health: Salud, medicamentos, gimnasio
- work: Trabajo, salario
- shopping: Compras, ropa
- services: Servicios varios
- education: Educación, cursos
- travel: Viajes, vacaciones

## Example Queries

### 1. Total expenses this month

**Question**: ¿Cuánto gasté este mes?

**SQL**:
```sql
SELECT SUM(amount) as total_expenses
FROM transactions
WHERE is_income = 0
AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now');
```

### 2. Balance (income - expenses)

**Question**: ¿Cuál es mi balance actual?

**SQL**:
```sql
SELECT * FROM current_balance;
```

Or:
```sql
SELECT 
    SUM(CASE WHEN is_income = 1 THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN is_income = 0 THEN amount ELSE 0 END) as expenses,
    SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END) as balance
FROM transactions;
```

### 3. Expenses by category

**Question**: ¿Cuánto gasté por categoría?

**SQL**:
```sql
SELECT * FROM expenses_by_category
ORDER BY total_amount DESC;
```

Or:
```sql
SELECT 
    category,
    COUNT(*) as count,
    SUM(amount) as total,
    AVG(amount) as average
FROM transactions
WHERE is_income = 0
GROUP BY category
ORDER BY total DESC;
```

### 4. Fixed expenses

**Question**: ¿Cuáles son mis gastos fijos?

**SQL**:
```sql
SELECT description, amount, category, date
FROM transactions
WHERE expense_type = 'fixed'
AND is_income = 0
ORDER BY amount DESC;
```

### 5. Last 10 transactions

**Question**: Últimas 10 transacciones

**SQL**:
```sql
SELECT date, amount, currency, description, category
FROM transactions
ORDER BY date DESC
LIMIT 10;
```

### 6. Expenses with specific payment method

**Question**: ¿Cuánto gasté con tarjeta de crédito?

**SQL**:
```sql
SELECT SUM(amount) as total
FROM transactions
WHERE payment_method = 'credit_card'
AND is_income = 0;
```

### 7. Expenses from specific source

**Question**: ¿Cuánto gasté con Tarjeta Canadá?

**SQL**:
```sql
SELECT SUM(amount) as total
FROM transactions
WHERE money_source = 'Tarjeta Canadá'
AND is_income = 0;
```

Or to see details:
```sql
SELECT date, amount, description, category
FROM transactions
WHERE money_source LIKE '%Canadá%'
AND is_income = 0
ORDER BY date DESC;
```

### 8. Food expenses this month

**Question**: ¿Cuánto gasté en comida este mes?

**SQL**:
```sql
SELECT SUM(amount) as total_food
FROM transactions
WHERE category = 'food'
AND is_income = 0
AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now');
```

### 9. Top 5 expenses

**Question**: Mis 5 gastos más grandes

**SQL**:
```sql
SELECT date, amount, description, category
FROM transactions
WHERE is_income = 0
ORDER BY amount DESC
LIMIT 5;
```

### 10. Average expense per category

**Question**: Gasto promedio por categoría

**SQL**:
```sql
SELECT 
    category,
    COUNT(*) as transactions,
    ROUND(AVG(amount), 2) as average_amount
FROM transactions
WHERE is_income = 0
GROUP BY category
ORDER BY average_amount DESC;
```

### 11. Monthly comparison

**Question**: Comparar gastos por mes

**SQL**:
```sql
SELECT 
    strftime('%Y-%m', date) as month,
    SUM(CASE WHEN is_income = 0 THEN amount ELSE 0 END) as expenses,
    SUM(CASE WHEN is_income = 1 THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END) as balance
FROM transactions
GROUP BY strftime('%Y-%m', date)
ORDER BY month DESC;
```

### 12. Cash vs card expenses

**Question**: ¿Cuánto gasto en efectivo vs tarjeta?

**SQL**:
```sql
SELECT 
    payment_method,
    COUNT(*) as transactions,
    SUM(amount) as total
FROM transactions
WHERE is_income = 0
GROUP BY payment_method
ORDER BY total DESC;
```

### 13. Date range query

**Question**: Gastos entre enero y marzo 2026

**SQL**:
```sql
SELECT date, amount, description, category
FROM transactions
WHERE is_income = 0
AND date >= '2026-01-01'
AND date < '2026-04-01'
ORDER BY date;
```

### 14. Search by description

**Question**: Buscar transacciones de "supermercado"

**SQL**:
```sql
SELECT date, amount, description, category, payment_method
FROM transactions
WHERE description LIKE '%supermercado%'
OR description LIKE '%Supermercado%'
ORDER BY date DESC;
```

### 15. Income sources

**Question**: ¿De dónde vienen mis ingresos?

**SQL**:
```sql
SELECT 
    description,
    SUM(amount) as total,
    COUNT(*) as times
FROM transactions
WHERE is_income = 1
GROUP BY description
ORDER BY total DESC;
```

## Tips for Query Generation

1. **Use LIKE for text search**: Case-insensitive with wildcards
   - `WHERE description LIKE '%café%'`

2. **Date filtering**:
   - Current month: `strftime('%Y-%m', date) = strftime('%Y-%m', 'now')`
   - Current year: `strftime('%Y', date) = strftime('%Y', 'now')`
   - Date range: `date >= '2026-01-01' AND date < '2026-02-01'`

3. **Aggregations**:
   - SUM, AVG, COUNT, MIN, MAX
   - Always use GROUP BY when aggregating by category

4. **Income vs Expenses**:
   - Expenses: `is_income = 0`
   - Income: `is_income = 1`
   - Balance: `SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END)`

5. **Ordering**:
   - Latest first: `ORDER BY date DESC`
   - Highest amount: `ORDER BY amount DESC`

6. **Limiting results**:
   - Always add LIMIT for "top N" queries
   - Example: `LIMIT 10`

## Error Handling

If the model generates an unsafe query:
- Detect keywords: DELETE, UPDATE, INSERT, DROP, ALTER, CREATE, TRUNCATE
- Return error message instead of executing
- Log the attempt for security monitoring

## Integration Example (Python)

```python
import requests
import os

def ask_question(question: str) -> list:
    """
    Convert natural language question to SQL and execute
    
    Args:
        question: User's question in natural language
        
    Returns:
        Query results as list of rows
    """
    # 1. Generate SQL with Llama (local)
    sql = generate_sql_with_llama(question)
    
    # 2. Validate SQL is safe
    if not is_safe_query(sql):
        raise ValueError("Unsafe query detected")
    
    # 3. Execute via Modal API
    api_url = os.environ['MODAL_API_URL']
    api_key = os.environ['FINANZAS_API_KEY']
    
    response = requests.post(
        f"{api_url}/query",
        headers={'X-API-Key': api_key},
        json={'sql': sql}
    )
    
    return response.json()


def is_safe_query(sql: str) -> bool:
    """Validate query is safe (SELECT only)"""
    dangerous = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER', 
                 'CREATE', 'TRUNCATE', 'REPLACE', 'PRAGMA']
    sql_upper = sql.upper()
    return sql_upper.strip().startswith('SELECT') and \
           not any(keyword in sql_upper for keyword in dangerous)
```

## Fine-tuning Recommendations

If you want to fine-tune Llama for better performance:

1. **Dataset**: Create training pairs (question, SQL)
2. **Format**: Use the examples above as starting point
3. **Augmentation**: Generate variations of questions
4. **Validation**: Test on held-out questions

Example training format:
```json
{
  "question": "¿Cuánto gasté este mes?",
  "sql": "SELECT SUM(amount) FROM transactions WHERE is_income = 0 AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now');"
}
```
