# 🚀 Guía Rápida de Uso

## Instalación

```bash
pip install -r requirements.txt
```

## Uso Básico

### 1. Agregar una transacción única (modo interactivo)

```bash
python cli.py add
```

Luego escribe tu YAML y presiona Enter dos veces:

```yaml
monto: 5000
descripcion: Supermercado
categoria: comida
```

### 2. Agregar transacción desde YAML en una línea

```bash
echo "monto: 100
descripcion: Café
metodo_pago: efectivo" | python -c "
from cli import FinanzasCLI
import sys
cli = FinanzasCLI()
cli.agregar_desde_yaml(sys.stdin.read())
"
```

### 3. Importar múltiples transacciones desde archivo

Primero crea tu archivo YAML (ej: `mis_gastos.yaml`):

```yaml
transacciones:
  - monto: 5000
    descripcion: Supermercado
    categoria: comida
    tipo_gasto: variable
    metodo_pago: tarjeta_debito
    fuente_dinero: Tarjeta Argentina

  - monto: 45000
    descripcion: Alquiler
    categoria: vivienda
    tipo_gasto: fijo

  - monto: 200
    descripcion: Café
    metodo_pago: efectivo
```

Luego importa:

```bash
python import_yaml.py mis_gastos.yaml
```

### 4. Ver estadísticas

```bash
python cli.py stats
```

### 5. Listar transacciones

```bash
python cli.py list       # Últimas 10
python cli.py list 20    # Últimas 20
```

### 6. Análisis completo

```bash
python analizar.py              # Análisis completo
python analizar.py categoria    # Solo por categoría
python analizar.py metodo       # Solo por método de pago
python analizar.py fuente       # Solo por fuente de dinero
python analizar.py tipos        # Solo fijos vs variables
```

## Ejemplos Prácticos

### Gasto mínimo (solo monto)

```yaml
monto: 100
```

### Gasto con tarjeta de crédito

```yaml
monto: 5000
tipo_gasto: variable
metodo_pago: tarjeta_credito
fuente_dinero: Tarjeta Canadá
descripcion: Cena en restaurante
categoria: comida
```

### Gasto fijo mensual

```yaml
monto: 45000
tipo_gasto: fijo
descripcion: Alquiler enero
categoria: vivienda
metodo_pago: transferencia
```

### Gasto en efectivo

```yaml
monto: 200
metodo_pago: efectivo
descripcion: Propina
```

### Ingreso

```yaml
monto: 150000
es_ingreso: true
descripcion: Sueldo mensual
categoria: trabajo
```

### Gasto con MercadoPago

```yaml
monto: 8500
descripcion: Compra online
categoria: varios
metodo_pago: transferencia
fuente_dinero: MercadoPago
```

### Gasto con conversión de moneda

```yaml
monto: 50
moneda: CAD
tasa_cambio: 880
monto_convertido: 44000
moneda_convertida: ARS
descripcion: Compra en Canadá
categoria: viajes
metodo_pago: tarjeta_credito
fuente_dinero: Tarjeta Canadá
```

## Campos Disponibles

### Obligatorios
- `monto`: Monto de la transacción (número)

### Opcionales
- `moneda`: ARS (default), USD, CAD, ETH
- `tipo_gasto`: fijo, variable
- `metodo_pago`: efectivo, tarjeta_credito, tarjeta_debito, transferencia, otro
- `fuente_dinero`: Texto libre (ej: "Tarjeta Canadá", "MercadoPago", "Efectivo")
- `descripcion`: Descripción del gasto
- `categoria`: Categoría (ej: comida, transporte, servicios, vivienda)
- `notas`: Notas adicionales
- `es_ingreso`: true/false (default: false)
- `tasa_cambio`: Tasa de cambio si aplica
- `monto_convertido`: Monto en otra moneda
- `moneda_convertida`: Moneda de conversión

## Tips

1. **Todos los campos son opcionales excepto `monto`** - puedes empezar simple y agregar más detalles después
2. **Usa `fuente_dinero` libremente** - no hay límites, pon lo que tenga sentido para ti
3. **Las categorías son flexibles** - crea las que necesites
4. **Importa en lote** - es más rápido crear un archivo YAML con todos tus gastos y luego importarlo
5. **Los CSV están en `data/`** - puedes abrirlos con Excel o cualquier editor

## Estructura de Archivos

```
Orgappitation/
├── models.py                    # Modelos Pydantic
├── database.py                  # Gestión de CSV
├── cli.py                       # CLI principal
├── import_yaml.py               # Importador masivo
├── analizar.py                  # Análisis y reportes
├── requirements.txt             # Dependencias
├── ejemplo_transacciones.yaml   # Archivo de ejemplo
└── data/                        # Datos (generado automáticamente)
    ├── transacciones.csv
    └── precios_referencia.csv
```

## Próximos Pasos

- [ ] Agregar integración con APIs de precios (ETH, USD)
- [ ] Preparar para deploy en Modal
- [ ] Crear filtros por fecha
- [ ] Exportar reportes mensuales
- [ ] Búsqueda avanzada
