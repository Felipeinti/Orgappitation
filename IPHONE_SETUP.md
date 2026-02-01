# 📱 Setup iPhone - Action Button para Finanzas

Guía completa para configurar el Action Button de tu iPhone 17 Pro Max para registrar gastos con voz.

## 🎯 Flujo completo

```
1. Presionas Action Button
2. iPhone graba tu voz
3. Audio se envía a bot de Telegram
4. Bot usa Whisper para transcribir
5. LLM procesa y guarda en base de datos
6. Recibes confirmación
```

---

## 📋 Pre-requisitos

- ✅ iPhone 17 Pro o Pro Max (con Action Button)
- ✅ iOS 18+
- ✅ App de Telegram instalada
- ✅ Bot de finanzas configurado y corriendo

---

## 🚀 Setup Paso a Paso

### 1️⃣ Verificar que el bot acepta audios

Primero, prueba manualmente:

1. Abre Telegram en tu iPhone
2. Busca tu bot: `@Orgappitation_bot`
3. Presiona y mantén el botón de micrófono 🎤
4. Di algo como: "Gasté 5000 en café"
5. Suelta para enviar

Deberías recibir:
```
🎤 Transcribiendo audio...
📝 Transcripción: Gasté 5000 en café
🧠 Procesando con LLM...
✅ 1 transacción(es) desde audio:
💸 $5,000 - café (food)
```

Si funciona, continúa al paso 2. Si no, asegúrate de que el bot esté corriendo.

---

### 2️⃣ Crear Shortcut de iOS

#### Opción A: Importar Shortcut (Más fácil)

1. **Abre Safari en tu iPhone**
2. **Ve a esta URL**: [Próximamente - te la daré cuando esté lista]
3. **Toca "Get Shortcut"**
4. **Toca "Add Shortcut"**
5. **Edita el shortcut**:
   - Cambia `@Orgappitation_bot` por tu username del bot
   - Guarda

#### Opción B: Crear Shortcut Manualmente

1. **Abre la app "Shortcuts" (Atajos)**

2. **Toca el botón "+"** (arriba a la derecha)

3. **Agrega estas acciones en orden**:

   **Acción 1: Dictate Text**
   - Busca: "Dictate Text"
   - Agrégala
   - Configura:
     - Language: Spanish
     - Show When Run: OFF (para que no pregunte)

   **Acción 2: Set Variable**
   - Busca: "Set Variable"
   - Agrégala
   - Nombra la variable: `TranscripcionAudio`

   **Acción 3: Send Message**
   - Busca: "Send Message" 
   - Agrégala
   - En "Message": Toca y selecciona la variable `TranscripcionAudio`
   - En "Recipient": Selecciona tu bot de Telegram `@Orgappitation_bot`
   - Configura:
     - Show When Run: OFF

   **Acción 4: Show Notification** (Opcional)
   - Busca: "Show Notification"
   - Agrégala
   - Mensaje: "✅ Enviado a Finanzas"

4. **Toca "Done"**

5. **Nombra el Shortcut**: "💰 Registrar Gasto"

---

### 3️⃣ Configurar Action Button

1. **Ve a Ajustes → Action Button**

2. **Selecciona "Shortcut"**

3. **Elige tu shortcut**: "💰 Registrar Gasto"

4. **Prueba**:
   - Presiona y mantén el Action Button
   - Di: "Gasté 3000 en taxi"
   - Suelta el botón
   - Deberías ver notificación "✅ Enviado a Finanzas"

5. **Ve a Telegram**:
   - Abre el chat con tu bot
   - Deberías ver tu mensaje y la respuesta del bot

---

## 🎤 Cómo Usarlo

### Uso Normal:

1. **Presiona y mantén** el Action Button
2. **Habla claramente**: "Gasté cinco mil pesos en café"
3. **Suelta** el botón
4. **Espera 2-3 segundos**
5. **Revisa Telegram** para ver confirmación

### Ejemplos de lo que puedes decir:

```
"Gasté cinco mil en café"
"Pagué cuarenta y cinco mil de alquiler"
"Compré comida por doce mil"
"Taxi tres mil quinientos"
"Me llegó el sueldo de doscientos mil"
"Cena en restaurante ocho mil"
```

### Tips para mejor reconocimiento:

✅ **Habla claro y despacio**
✅ **Di los números completos**: "cinco mil" mejor que "5000"
✅ **Ambiente silencioso** (no en la calle ruidosa)
✅ **Espera un segundo** después de presionar antes de hablar
✅ **No tapes el micrófono** con la funda

---

## 🔧 Configuración Avanzada

### Opción 1: Con confirmación visual

Modifica el shortcut para agregar:

**Después de "Send Message":**
- Acción: **Wait** → 3 seconds
- Acción: **Get Latest Messages** → From: Tu bot → Count: 1
- Acción: **Show Notification** → Con el contenido del mensaje

Así verás la respuesta del bot sin abrir Telegram.

### Opción 2: Modo batch (múltiples transacciones)

Puedes decir varias cosas en un solo audio:

```
"Gasté cinco mil en café, 
pagué cuarenta y cinco mil de alquiler 
y compré comida por doce mil"
```

El bot procesará las 3 transacciones.

### Opción 3: Modo silencioso

Si no quieres que vibre:
1. En el shortcut, elimina "Show Notification"
2. Solo revisa Telegram cuando quieras

---

## 🐛 Troubleshooting

### "No se pudo enviar el mensaje"
- ✅ Verifica que Telegram tenga permisos de red
- ✅ Asegúrate de estar conectado a internet
- ✅ Revisa que el username del bot sea correcto

### "El bot no responde"
- ✅ Verifica que el bot esté corriendo (`python telegram/bot.py`)
- ✅ Revisa los logs del bot en tu compu
- ✅ Prueba enviar un mensaje de texto primero

### "Whisper no transcribe bien"
- ✅ Habla más despacio y claro
- ✅ Reduce el ruido ambiente
- ✅ Di los números en palabras ("cinco mil" vs "5000")
- ✅ Repite si falla, Whisper es muy bueno generalmente

### "El LLM no entiende"
- ✅ Sé más explícito: "Gasté X en Y"
- ✅ Usa palabras clave: "gasté", "pagué", "compré", "cobré"
- ✅ Revisa la transcripción que te muestra el bot

### "Action Button no funciona"
- ✅ Ve a Ajustes → Action Button
- ✅ Asegúrate de que esté en "Shortcut"
- ✅ Verifica que el shortcut sea el correcto
- ✅ Reinicia el iPhone si hace falta

---

## 💡 Tips Pro

### 1. Contexto implícito
El LLM es inteligente, puedes decir:
```
"Café 5000" → Entiende que es un gasto en café
"Supermercado" → Si mencionas solo el lugar, pregunta el monto
```

### 2. Categorías automáticas
El LLM infiere la categoría:
```
"Café" → food
"Alquiler" → housing  
"Taxi" → transport
"Ropa" → shopping
```

### 3. Múltiples transacciones
Habla en una sola grabación:
```
"Gasté cinco mil en café,
tres mil quinientos en taxi,
y me llegó el sueldo de doscientos mil"
```

El bot procesará las 3 transacciones.

### 4. Revisa tu día
Al final del día:
```
/balance → Ver cuánto gastaste
/stats → Ver desglose completo
```

### 5. Usa Siri (Alternativa)
También puedes decir:
```
"Hey Siri, registrar gasto"
```
Y ejecutará el mismo shortcut.

---

## 📊 Estadísticas de uso

Para ver cuánto estás usando el bot:

1. **Ver mensajes de voz procesados**:
   ```bash
   cat logs/openai_tokens.csv | grep voice | wc -l
   ```

2. **Ver costo de Whisper**:
   - Cada segundo de audio: ~$0.0001
   - Audio de 10 segundos: ~$0.001
   - 100 audios al mes: ~$0.10

---

## 🎯 Próximos Pasos

Una vez que domines el Action Button:

1. ✅ **Configura Face ID** para Telegram (privacidad)
2. ✅ **Crea widgets** de estadísticas
3. ✅ **Automatiza reportes** diarios/semanales
4. ✅ **Integra con Shortcuts** más complejos

---

## 🆘 Soporte

Si algo no funciona:

1. **Revisa los logs del bot** en tu compu
2. **Prueba manualmente** enviando audio en Telegram
3. **Verifica las APIs**:
   - OpenAI API funcionando
   - Modal API respondiendo
4. **Reinicia el bot** si hace falta

---

**¡Listo! Ahora puedes registrar gastos con un solo botón.** 🎉

Tu flujo diario:
1. Compras café → Presionas Action Button → "Gasté cinco mil en café"
2. Tomas taxi → Presionas Action Button → "Taxi tres mil quinientos"
3. Al final del día → Abres Telegram → `/balance`

**Total tiempo**: <5 segundos por transacción ⚡
