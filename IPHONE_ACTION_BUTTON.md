# 📱 Configuración del Action Button del iPhone

Guía para configurar el Action Button de tu iPhone para enviar audio directamente al sistema de finanzas.

## 🎯 ¿Cómo funciona?

```
iPhone Action Button
    ↓ (graba audio)
iOS Shortcut
    ↓ (envía POST request)
ngrok → audio_webhook.py (tu Mac)
    ↓ (transcribe con Whisper)
LLM Service (OpenAI)
    ↓ (convierte a YAML)
Modal API
    ↓ (guarda transacción)
✅ Respuesta al iPhone
```

---

## 📋 Requisitos

- iPhone 15 Pro, 16 Pro o 17 Pro (con Action Button)
- ngrok instalado en tu Mac
- Servicios corriendo en tu Mac:
  - `audio_webhook.py` (puerto 8003)
  - `llm_service_openai.py` (puerto 8002)
  - Modal API desplegada

---

## 🚀 Paso 1: Instalar ngrok

### Instalar:
```bash
brew install ngrok
```

### Crear cuenta gratuita:
1. Ve a https://dashboard.ngrok.com/signup
2. Crea una cuenta (gratis)
3. Copia tu authtoken

### Configurar:
```bash
ngrok config add-authtoken TU_AUTHTOKEN_AQUI
```

---

## 💻 Paso 2: Iniciar servicios locales

### Terminal 1: LLM Service
```bash
python llm_service_openai.py
```
Debe estar corriendo en `http://127.0.0.1:8002`

### Terminal 2: Audio Webhook
```bash
python audio_webhook.py
```
Debe estar corriendo en `http://0.0.0.0:8003`

### Terminal 3: ngrok
```bash
ngrok http 8003
```

Verás algo como:
```
Forwarding  https://abcd-1234-5678.ngrok-free.app -> http://localhost:8003
```

**⚠️ IMPORTANTE: Copia esa URL de ngrok, la necesitarás para el Shortcut**

---

## 📱 Paso 3: Crear iOS Shortcut

### 1. Abre la app "Shortcuts" en tu iPhone

### 2. Toca el botón "+" para crear un nuevo Shortcut

### 3. Agrega estas acciones EN ORDEN:

#### Acción 1: **Record Audio**
- Busca: "Record Audio"
- Configuración:
  - Start Recording: On Tap
  - Finish Recording: On Tap
  - Audio Quality: Normal

#### Acción 2: **Get Contents of URL**
- Busca: "Get Contents of URL"
- Configuración:
  - **URL**: `https://TU-URL-DE-NGROK.ngrok-free.app/audio`
    (Reemplaza con tu URL de ngrok del Paso 2)
  - **Method**: POST
  - **Headers**:
    - Toca "Add new header"
    - Key: `Authorization`
    - Value: `Bearer mi_secreto_super_seguro_123`
  - **Request Body**: Form
    - Campo 1:
      - Key: `audio`
      - Type: File
      - Value: `Recorded Audio` (variable del paso anterior)

#### Acción 3: **Show Notification** (opcional pero recomendado)
- Busca: "Show Notification"
- Configuración:
  - Title: "Finanzas"
  - Body: `Contents of URL` (resultado del POST)

### 4. Nombra tu Shortcut
- Toca los "..." en la esquina
- Nombre: "Registrar Gasto" (o lo que prefieras)
- Ícono: Elige uno (💰 recomendado)

### 5. Guarda el Shortcut

---

## 🎛️ Paso 4: Configurar Action Button

### 1. Abre **Configuración** en tu iPhone

### 2. Busca **"Botón de Acción"** o **"Action Button"**

### 3. Desliza hasta encontrar el ícono de **"Atajo"** o **"Shortcut"**

### 4. Toca **"Elegir atajo"**

### 5. Selecciona tu Shortcut: **"Registrar Gasto"**

### 6. ¡Listo!

---

## 🎯 Cómo usar

1. **Presiona y mantén** el Action Button (botón lateral izquierdo)
2. **Habla** tu transacción: "Gasté 3000 en almuerzo"
3. **Suelta el botón** cuando termines
4. **Espera unos segundos** - recibirás una notificación con el resultado

### Ejemplos de lo que puedes decir:
- "Gasté 3000 en almuerzo"
- "Pagué 45000 de alquiler"
- "Me llegó el sueldo de 200000"
- "Compré café por 1500"
- "Gasté 50 dólares en libros con tarjeta de Canadá"

---

## 🔧 Troubleshooting

### Error: "No se pudo conectar"
- ✅ Verifica que `audio_webhook.py` esté corriendo
- ✅ Verifica que ngrok esté corriendo
- ✅ Verifica que la URL en el Shortcut sea correcta

### Error: "401 Unauthorized"
- ✅ Verifica que el header `Authorization` esté configurado
- ✅ Verifica que el valor sea `Bearer mi_secreto_super_seguro_123`

### Error: "Whisper no configurado"
- ✅ Verifica que `OPENAI_API_KEY` esté en tu `.env`
- ✅ Reinicia `audio_webhook.py`

### El audio se graba pero no procesa
- ✅ Revisa los logs en la terminal donde corre `audio_webhook.py`
- ✅ Verifica que `llm_service_openai.py` esté corriendo
- ✅ Verifica que Modal API esté desplegada y funcionando

---

## 🔐 Seguridad

### Cambiar el secret:
1. Edita `.env`:
   ```bash
   WEBHOOK_SECRET=tu_nuevo_secret_aqui_super_seguro
   ```

2. Reinicia `audio_webhook.py`

3. Actualiza el header en tu iOS Shortcut:
   ```
   Authorization: Bearer tu_nuevo_secret_aqui_super_seguro
   ```

### ⚠️ IMPORTANTE:
- **NO compartas** tu URL de ngrok públicamente
- **NO commitees** tu `WEBHOOK_SECRET` al repo
- ngrok URL cambia cada vez que reinicias ngrok (en plan gratuito)

---

## 🌐 Desplegar en Modal (Opcional)

Si quieres que funcione sin tener tu Mac prendida, puedes desplegar el webhook en Modal:

```bash
modal deploy audio_webhook_modal.py
```

(Este archivo aún no existe - lo podemos crear si lo necesitas)

---

## 📊 Ver resultados

Después de enviar el audio:

1. **En el iPhone**: Recibirás una notificación con el resumen

2. **En Telegram**: Envía `/stats` al bot para ver todas tus transacciones

3. **En la terminal**: Verás logs en tiempo real de todo el proceso

---

## ⚡ Tips

- **El Action Button es customizable**: Puedes cambiar qué hace en Configuración
- **Puedes tener múltiples Shortcuts**: Crea uno para gastos y otro para ingresos
- **ngrok gratis tiene límites**: 40 requests/minuto (suficiente para uso personal)
- **Mantén ngrok corriendo**: O usa un dominio estático (plan pago)

---

¡Listo! Ahora puedes registrar tus gastos con solo presionar un botón 🚀
