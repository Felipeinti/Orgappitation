-- SQL Schema optimizado para text-to-SQL con modelos pequeños
-- Diseñado para facilitar queries en lenguaje natural

-- Tabla principal: transactions
-- Contiene todos los datos importantes en una sola tabla para simplificar queries
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,  -- ISO format: YYYY-MM-DD HH:MM:SS
    amount REAL NOT NULL CHECK(amount > 0),
    currency TEXT NOT NULL DEFAULT 'ARS',
    
    -- Clasificación del gasto
    expense_type TEXT,  -- 'fixed' o 'variable'
    category TEXT,      -- 'food', 'housing', 'transport', etc.
    is_income INTEGER NOT NULL DEFAULT 0,  -- 0 = gasto, 1 = ingreso
    
    -- Método de pago
    payment_method TEXT,  -- 'cash', 'credit_card', 'debit_card', 'transfer', etc.
    money_source TEXT,    -- 'Tarjeta Canadá', 'MercadoPago', etc (texto libre)
    
    -- Descripción
    description TEXT,
    notes TEXT,
    
    -- Conversión de moneda (opcional)
    exchange_rate REAL,
    converted_amount REAL,
    converted_currency TEXT,
    
    -- Metadata
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar performance de queries comunes
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_is_income ON transactions(is_income);
CREATE INDEX IF NOT EXISTS idx_transactions_expense_type ON transactions(expense_type);
CREATE INDEX IF NOT EXISTS idx_transactions_payment_method ON transactions(payment_method);

-- Tabla auxiliar: categories (catálogo de categorías usadas)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insertar categorías comunes
INSERT OR IGNORE INTO categories (name, description) VALUES
    ('food', 'Comida y bebidas'),
    ('housing', 'Alquiler, servicios, mantenimiento'),
    ('transport', 'Transporte público, combustible, Uber'),
    ('entertainment', 'Entretenimiento, salidas'),
    ('health', 'Salud, medicamentos, gimnasio'),
    ('work', 'Trabajo, salario, proyectos'),
    ('shopping', 'Compras, ropa, varios'),
    ('services', 'Servicios varios'),
    ('education', 'Educación, cursos'),
    ('travel', 'Viajes, vacaciones');

-- Tabla auxiliar: payment_methods (catálogo de métodos de pago)
CREATE TABLE IF NOT EXISTS payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insertar métodos de pago comunes
INSERT OR IGNORE INTO payment_methods (name, description) VALUES
    ('cash', 'Efectivo'),
    ('credit_card', 'Tarjeta de crédito'),
    ('debit_card', 'Tarjeta de débito'),
    ('transfer', 'Transferencia bancaria'),
    ('other', 'Otro método');

-- Tabla auxiliar: money_sources (catálogo de fuentes de dinero)
CREATE TABLE IF NOT EXISTS money_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    country TEXT,  -- 'AR', 'CA', etc.
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Ejemplos de fuentes de dinero (se pueden agregar más dinámicamente)
INSERT OR IGNORE INTO money_sources (name, description, country) VALUES
    ('Tarjeta Canadá', 'Tarjeta de crédito/débito de Canadá', 'CA'),
    ('Tarjeta Argentina', 'Tarjeta de crédito/débito de Argentina', 'AR'),
    ('MercadoPago', 'Cuenta de MercadoPago', 'AR'),
    ('Efectivo ARS', 'Efectivo en pesos argentinos', 'AR'),
    ('Efectivo CAD', 'Efectivo en dólares canadienses', 'CA'),
    ('Efectivo USD', 'Efectivo en dólares americanos', 'US');

-- Tabla: reference_prices (precios de referencia para ETH, USD, etc.)
CREATE TABLE IF NOT EXISTS reference_prices (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    symbol TEXT NOT NULL,  -- 'ETH', 'USD', 'BTC', etc.
    price REAL NOT NULL CHECK(price > 0),
    base_currency TEXT NOT NULL DEFAULT 'ARS',  -- precio en qué moneda
    source TEXT,  -- 'CoinGecko', 'DolarAPI', etc.
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsqueda rápida de precios
CREATE INDEX IF NOT EXISTS idx_reference_prices_date ON reference_prices(date);
CREATE INDEX IF NOT EXISTS idx_reference_prices_symbol ON reference_prices(symbol);

-- Vista útil: resumen de gastos por categoría
CREATE VIEW IF NOT EXISTS expenses_by_category AS
SELECT 
    category,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MIN(date) as first_transaction,
    MAX(date) as last_transaction
FROM transactions
WHERE is_income = 0
GROUP BY category;

-- Vista útil: resumen de gastos por mes
CREATE VIEW IF NOT EXISTS expenses_by_month AS
SELECT 
    strftime('%Y-%m', date) as month,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN is_income = 0 THEN amount ELSE 0 END) as total_expenses,
    SUM(CASE WHEN is_income = 1 THEN amount ELSE 0 END) as total_income,
    SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END) as net_balance
FROM transactions
GROUP BY strftime('%Y-%m', date)
ORDER BY month DESC;

-- Vista útil: balance actual
CREATE VIEW IF NOT EXISTS current_balance AS
SELECT 
    SUM(CASE WHEN is_income = 1 THEN amount ELSE 0 END) as total_income,
    SUM(CASE WHEN is_income = 0 THEN amount ELSE 0 END) as total_expenses,
    SUM(CASE WHEN is_income = 1 THEN amount ELSE -amount END) as balance,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN is_income = 0 THEN 1 END) as expense_count,
    COUNT(CASE WHEN is_income = 1 THEN 1 END) as income_count
FROM transactions;
