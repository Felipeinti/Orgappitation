# 🗑️ Guía para Borrar Datos

Guía completa para eliminar transacciones de tu base de datos.

## ⚠️ Importante

**Los borrados son permanentes y no se pueden deshacer.** Asegúrate de tener backups si es necesario.

## 1️⃣ Borrar TODAS las transacciones

### Opción A: Con script wrapper (recomendado)

```bash
./finanzas_cli.sh delete-all
```

### Opción B: Directo con Python

```bash
python yaml_to_modal.py --delete-all --verbose
```

Te pedirá confirmar escribiendo `SI`:

```
⚠️  ¿Estás seguro que quieres eliminar TODAS las transacciones?
   Escribe 'SI' para confirmar:
SI
⚠️  Eliminando TODAS las transacciones...
✅ 10 transacciones eliminadas exitosamente
```

### Opción C: Con script no interactivo

```bash
echo "SI" | python yaml_to_modal.py --delete-all --verbose
```

## 2️⃣ Borrar una transacción específica

Primero necesitas el **ID de la transacción**. Puedes obtenerlo de varias formas:

### A. Ver últimas transacciones

```bash
curl "https://tu-url--finanzas-api-fastapi-app.modal.run/transactions/recent?limit=10" \
  -H "X-API-Key: tu_api_key" | python -m json.tool
```

O más simple:

```bash
# Configurar en tu shell
export FINANZAS_API_KEY=$(grep FINANZAS_API_KEY .env | cut -d '=' -f2)
export MODAL_API_URL=$(grep MODAL_API_URL .env | cut -d '=' -f2)

# Ver últimas transacciones
curl -s "$MODAL_API_URL/transactions/recent?limit=10" \
  -H "X-API-Key: $FINANZAS_API_KEY" | python -m json.tool
```

### B. Eliminar por ID

Una vez que tienes el ID:

```bash
# Con script wrapper
./finanzas_cli.sh delete abc-123-def-456

# O directo
python yaml_to_modal.py --delete abc-123-def-456 --verbose
```

Ejemplo real:

```bash
$ python yaml_to_modal.py --delete b1fc12ff-c17f-466b-8eb1-3f1a31425d37 --verbose
🗑️  Eliminando transacción b1fc12ff-c17f-466b-8eb1-3f1a31425d37...
✅ Transacción b1fc12ff-c17f-466b-8eb1-3f1a31425d37 eliminada exitosamente
```

## 3️⃣ Verificar después de borrar

```bash
# Ver estadísticas
./finanzas_cli.sh stats

# O directo
curl -s "$MODAL_API_URL/stats" -H "X-API-Key: $FINANZAS_API_KEY" | python -m json.tool
```

## 4️⃣ Casos de uso comunes

### Empezar de cero (borrar todo)

```bash
# Borrar todas las transacciones
./finanzas_cli.sh delete-all

# Verificar que esté vacío
./finanzas_cli.sh stats
# Deberías ver: total_transactions: 0
```

### Corregir un error (borrar transacción incorrecta)

```bash
# 1. Ver últimas transacciones para encontrar el ID
curl -s "$MODAL_API_URL/transactions/recent?limit=5" \
  -H "X-API-Key: $FINANZAS_API_KEY" | python -m json.tool

# 2. Copiar el ID de la transacción incorrecta
# 3. Borrarla
./finanzas_cli.sh delete <ID_AQUI>

# 4. Agregar la correcta
echo "monto: 5000
descripcion: Supermercado (corregido)" | python yaml_to_modal.py --stdin
```

### Limpiar transacciones de prueba

```bash
# Si agregaste transacciones de test con categoria: test
# No hay filtro directo por categoría en DELETE, pero puedes:

# 1. Ver todas
curl -s "$MODAL_API_URL/transactions/recent?limit=100" \
  -H "X-API-Key: $FINANZAS_API_KEY" | python -m json.tool > all.json

# 2. Filtrar manualmente las de test y extraer IDs
# 3. Borrar una por una
./finanzas_cli.sh delete <ID_TEST_1>
./finanzas_cli.sh delete <ID_TEST_2>
# etc...

# O más simple: borrar todo y volver a importar solo las buenas
./finanzas_cli.sh delete-all
python yaml_to_modal.py --file transacciones_reales.yaml --batch
```

## 5️⃣ Endpoints de la API

Si quieres usar la API directamente:

### DELETE una transacción

```bash
curl -X DELETE "$MODAL_API_URL/transactions/<transaction_id>" \
  -H "X-API-Key: $FINANZAS_API_KEY"
```

### DELETE todas las transacciones

```bash
curl -X DELETE "$MODAL_API_URL/transactions?confirm=DELETE_ALL" \
  -H "X-API-Key: $FINANZAS_API_KEY"
```

**Nota**: El parámetro `confirm=DELETE_ALL` es obligatorio para evitar borrados accidentales.

## 6️⃣ Backup antes de borrar

Si tienes datos importantes, haz backup primero:

```bash
# Exportar todas las transacciones a JSON
curl -s "$MODAL_API_URL/transactions/recent?limit=10000" \
  -H "X-API-Key: $FINANZAS_API_KEY" > backup_$(date +%Y%m%d).json

# Ahora puedes borrar con confianza
./finanzas_cli.sh delete-all
```

## 7️⃣ Errors comunes

### "Transaction not found"

El ID no existe o ya fue borrado. Verifica el ID:

```bash
curl -s "$MODAL_API_URL/transactions/recent?limit=10" \
  -H "X-API-Key: $FINANZAS_API_KEY" | python -m json.tool
```

### "API key inválida"

Verifica tu `.env`:

```bash
cat .env
# Debe tener:
# MODAL_API_URL=https://...
# FINANZAS_API_KEY=...
```

### "confirm=DELETE_ALL required"

Cuando usas la API directamente, debes incluir el parámetro de confirmación:

```bash
# ❌ Incorrecto
curl -X DELETE "$MODAL_API_URL/transactions"

# ✅ Correcto
curl -X DELETE "$MODAL_API_URL/transactions?confirm=DELETE_ALL" \
  -H "X-API-Key: $FINANZAS_API_KEY"
```

## Resumen de comandos

```bash
# Borrar todas
./finanzas_cli.sh delete-all

# Borrar una específica
./finanzas_cli.sh delete <transaction_id>

# Ver transacciones para obtener IDs
curl -s "$MODAL_API_URL/transactions/recent?limit=10" \
  -H "X-API-Key: $FINANZAS_API_KEY" | python -m json.tool

# Verificar estado
./finanzas_cli.sh stats
```

## Seguridad

- ✅ Requiere API key para todos los deletes
- ✅ DELETE all requiere confirmación explícita
- ✅ No se pueden hacer deletes masivos por accidente
- ✅ Los IDs son UUIDs únicos y difíciles de adivinar

---

**Recuerda**: Los borrados son permanentes. Haz backups si es necesario.
