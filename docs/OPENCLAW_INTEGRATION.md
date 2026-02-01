# 🦞 Integración con OpenClaw

Guía para integrar tu app de finanzas con OpenClaw.

## Setup

### 1. Copiar scripts al workspace de OpenClaw

```bash
# Crear directorio
mkdir -p ~/.openclaw/workspace/tools/finanzas

# Copiar archivos necesarios
cp finanzas_cli.sh ~/.openclaw/workspace/tools/finanzas/
cp yaml_to_modal.py ~/.openclaw/workspace/tools/finanzas/
cp text_to_sql.py ~/.openclaw/workspace/tools/finanzas/
cp .env ~/.openclaw/workspace/tools/finanzas/

# Hacer ejecutable
chmod +x ~/.openclaw/workspace/tools/finanzas/finanzas_cli.sh
```

### 2. Crear Skill de OpenClaw

Crear archivo `~/.openclaw/workspace/skills/finanzas/SKILL.md`:

```markdown
# 💰 Finanzas Skill

Gestiona tus finanzas personales.

## Comandos disponibles

### /gastar [descripción]
Registra un gasto.

**Ejemplos:**
- `/gastar 5000 pesos en supermercado`
- `/gastar pagué 200 de café con tarjeta`
- `/gastar alquiler 45000`

### /ingreso [descripción]
Registra un ingreso.

**Ejemplo:**
- `/ingreso sueldo 150000`

### /balance
Muestra tu balance actual (ingresos - gastos).

### /gastos [pregunta]
Analiza tus gastos con lenguaje natural.

**Ejemplos:**
- `/gastos ¿cuánto gasté este mes?`
- `/gastos gastos por categoría`
- `/gastos ¿cuánto gasto con tarjeta de Canadá?`

## Cómo funciona

Cuando usas un comando, OpenClaw:

1. **Entiende tu intención** (gastar, consultar, etc)
2. **Genera YAML estructurado** con los datos
3. **Ejecuta el script** `finanzas_cli.sh`
4. **Te responde** con confirmación o resultados

## Herramientas disponibles

El skill tiene acceso a:
- `finanzas_cli.sh add` - Agregar transacciones
- `finanzas_cli.sh query` - Consultas en lenguaje natural
- `finanzas_cli.sh balance` - Balance rápido
```

### 3. Agregar función al AGENTS.md de OpenClaw

Editar `~/.openclaw/workspace/AGENTS.md` y agregar:

```markdown
## Finanzas

Tienes acceso a un sistema de finanzas personales.

**Para registrar gastos:**
1. El usuario dirá algo como "gasté 5000 en el super"
2. Extrae: monto, descripción, categoría (opcional)
3. Genera YAML en formato:
   ```yaml
   monto: 5000
   descripcion: Supermercado
   categoria: food
   ```
4. Ejecuta: `cd ~/.openclaw/workspace/tools/finanzas && ./finanzas_cli.sh add "monto: 5000\ndescripcion: Supermercado\ncategoria: food"`

**Para consultas:**
1. El usuario preguntará algo como "¿cuánto gasté este mes?"
2. Ejecuta: `cd ~/.openclaw/workspace/tools/finanzas && ./finanzas_cli.sh query "¿cuánto gasté este mes?"`

**Categorías comunes:**
- food (comida)
- housing (vivienda, alquiler)
- transport (transporte)
- entertainment (entretenimiento)
- health (salud)
- shopping (compras)

**Importante:**
- El campo `monto` es OBLIGATORIO
- Todo lo demás es opcional
- Si el usuario no especifica categoría, déjala vacía
```

## Ejemplos de conversación

### Ejemplo 1: Gasto simple

```
Tú: Gasté 5000 en el supermercado

OpenClaw (piensa):
- Monto: 5000
- Descripción: Supermercado
- Categoría: food (inferido)

OpenClaw (ejecuta):
cd ~/.openclaw/workspace/tools/finanzas && ./finanzas_cli.sh add "monto: 5000
descripcion: Supermercado
categoria: food"

OpenClaw (responde):
✅ Gasto registrado: $5,000 ARS en Supermercado
```

### Ejemplo 2: Gasto con detalles

```
Tú: Pagué 45000 de alquiler con transferencia

OpenClaw (genera):
monto: 45000
descripcion: Alquiler
categoria: housing
tipo_gasto: fixed
metodo_pago: transfer

OpenClaw (responde):
✅ Gasto fijo registrado: $45,000 ARS - Alquiler
```

### Ejemplo 3: Consulta

```
Tú: ¿Cuánto gasté este mes en comida?

OpenClaw (ejecuta):
./finanzas_cli.sh query "¿Cuánto gasté este mes en comida?"

OpenClaw (responde):
📊 Gastaste $22,000 ARS en comida este mes

Detalle:
- Supermercado: $15,000
- Restaurantes: $5,000
- Café: $2,000
```

### Ejemplo 4: Audio desde iPhone

```
Tú: [Grabas audio] "Gasté 200 pesos en café"

OpenClaw:
1. Transcribe: "Gasté 200 pesos en café"
2. Genera YAML
3. Registra gasto
4. Responde: ✅ Café registrado: $200 ARS
```

## Prompt sugerido para OpenClaw

Cuando el usuario mencione finanzas, usa este flujo:

```
SI el usuario quiere REGISTRAR un gasto/ingreso:
  1. Extrae información del mensaje
  2. Genera YAML con formato:
     monto: [número]
     descripcion: [texto]
     categoria: [food/housing/transport/etc] (opcional)
     metodo_pago: [cash/credit_card/debit_card] (opcional)
     fuente_dinero: [texto libre] (opcional)
     es_ingreso: [true para ingresos, false o vacío para gastos]
  3. Ejecuta: cd ~/.openclaw/workspace/tools/finanzas && ./finanzas_cli.sh add "yaml_aqui"
  4. Confirma al usuario

SI el usuario quiere CONSULTAR:
  1. Ejecuta: cd ~/.openclaw/workspace/tools/finanzas && ./finanzas_cli.sh query "pregunta_del_usuario"
  2. Muestra resultados de forma clara

SI el usuario pide BALANCE:
  1. Ejecuta: cd ~/.openclaw/workspace/tools/finanzas && ./finanzas_cli.sh balance
  2. Resume: "Tu balance es X (ingresos Y - gastos Z)"
```

## Testing de la integración

Una vez configurado, prueba:

```bash
# Desde OpenClaw en Telegram:
Tú: /gastar 100 pesos café
Bot: ✅ Gasto registrado: $100 ARS en café

Tú: /balance
Bot: 💰 Balance: $-100 ARS
     Ingresos: $0
     Gastos: $100

Tú: /gastos ¿cuánto gasté?
Bot: 📊 Gastaste $100 ARS en total
```

## Troubleshooting

### OpenClaw no encuentra el script

Verifica paths:
```bash
ls -la ~/.openclaw/workspace/tools/finanzas/finanzas_cli.sh
```

### Permission denied

```bash
chmod +x ~/.openclaw/workspace/tools/finanzas/finanzas_cli.sh
```

### .env not found

```bash
cp .env ~/.openclaw/workspace/tools/finanzas/
```

### API key error

Verifica que `.env` tenga:
```
MODAL_API_URL=https://...
FINANZAS_API_KEY=...
```

## Ventajas de este setup

✅ **YAML = Menos tokens**: El LLM genera YAML (más compacto que JSON)  
✅ **Validación robusta**: Pydantic valida todo en el backend  
✅ **Flexible**: El usuario puede ser vago ("gasté 100 en café") u específico  
✅ **Multi-canal**: Funciona en Telegram, WhatsApp, Discord, etc  
✅ **Audio-ready**: OpenClaw puede transcribir y procesar audio  

## Next steps

Una vez funcionando, puedes:
- Configurar comandos custom en OpenClaw
- Agregar triggers automáticos (ej: recordatorio semanal de balance)
- Integrar con notificaciones
- Crear reportes mensuales automáticos
