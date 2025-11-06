# 🔄 REGENERAR TOKENS - HOW TO

**TradePlus V5.0 - Guía Completa de Regeneración de Tokens**

---

## 🎯 ¿QUÉ ES LA REGENERACIÓN DE TOKENS?

Los **access tokens** de Schwab expiran cada **30 minutos**. La regeneración automática permite obtener nuevos tokens válidos sin intervención manual usando el **refresh token** que dura mucho más tiempo.

---

## 📁 ARCHIVOS FUNDAMENTALES PARA QUE FUNCIONE

### ✅ OBLIGATORIOS - **NUNCA BORRAR**

1. **`.env`** - Credenciales de autenticación
```env
TOS_CLIENT_ID=E5JeBvUNWNkRSt4iH2a9iGOWFnY2HP9s4Y792ftffemWFLLe
TOS_CLIENT_SECRET=3mKEG3P4bgYDGErOEVzPaGswI7ckqN6wBfIljAfZ0wQzjSTMaiyG8AQbnZQGFEPN
TOS_REFRESH_TOKEN=ONgl_BvSoJcl95vmoK1a3y7j1J7llLEzz-3CxEXN8n--3MRgiTWV5ey1vJsWQ6HSil5aPgp6o3Grga5Mj2gSjWVK-7UfWfzUeJHVBnpccrHedRSmh9JanRtRwCktUBTnDYYziHqiiIU@
```

2. **`generate_token.py`** - Script generador automático
3. **`dashboard.html`** - Interfaz web con regeneración integrada
4. **`current_token.json`** - Token actual válido (se regenera automáticamente)

### 🔄 ARCHIVOS GENERADOS AUTOMÁTICAMENTE

- `current_token.json` - Se actualiza cada vez que generas un token
- Logs de consola con timestamps

---

## 🚀 MÉTODOS DE REGENERACIÓN

### **Método 1: Dashboard Web (RECOMENDADO)**

1. **Abre:** `dashboard.html` en tu navegador
2. **Click:** "🔄 Generar Token"
3. **Automático:** Se conecta a Schwab API y genera nuevo token
4. **Resultado:** Token válido por 30 minutos + botones habilitados

```
✅ TOKEN GENERADO EXITOSAMENTE!
Expira en: 30 minutos
🎉 ¡Listo! Ahora puedes usar los botones.
```

### **Método 2: Script Python**

```bash
python generate_token.py
```

**Salida esperada:**
```
🚀 TradePlus V5.0 - Token Manager
✅ ¡TOKEN GENERADO EXITOSAMENTE!
🎫 ACCESS TOKEN: I0.b2F1dGgyLmJkYy5zY2h3YWIuY29t...
⏰ EXPIRA EN: 1800 segundos (30 minutos)
✅ TOKEN VÁLIDO - API SCHWAB RESPONDE
📊 Cuentas encontradas: 1
```

---

## 🔧 CÓMO FUNCIONA TÉCNICAMENTE

### **Flujo de Autenticación OAuth 2.0**

1. **Client ID + Client Secret** → Autenticación básica
2. **Refresh Token** → Solicitud de nuevo access token
3. **Access Token** → Acceso a API de Schwab por 30 minutos
4. **Nuevo Refresh Token** → Para próxima regeneración

### **Endpoint de Regeneración**
```
POST https://api.schwabapi.com/v1/oauth/token

Headers:
  Authorization: Basic <base64(client_id:client_secret)>
  Content-Type: application/x-www-form-urlencoded

Body:
  grant_type=refresh_token
  refresh_token=<tu_refresh_token>
```

### **Respuesta Esperada (HTTP 200)**
```json
{
  "access_token": "I0.b2F1dGgyLmJkYy5zY2h3YWIuY29t...",
  "expires_in": 1800,
  "token_type": "Bearer",
  "scope": "api",
  "refresh_token": "ONgl_BvSoJcl95vmoK1a3y7j1J7ll...",
  "id_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

---

## 🚨 PROBLEMAS COMUNES Y SOLUCIONES

### **❌ Error: "invalid_grant"**
```json
{"error": "invalid_grant", "error_description": "Invalid refresh token"}
```

**Causa:** Refresh token expirado o inválido  
**Solución:** Obtener nuevo refresh token desde Schwab Developer Portal

### **❌ Error: "unauthorized_client"**
```json
{"error": "unauthorized_client"}
```

**Causa:** Client ID o Client Secret incorrectos  
**Solución:** Verificar credenciales en archivo `.env`

### **❌ Error de CORS en navegador**
```
Access to fetch blocked by CORS policy
```

**Causa:** Restricciones de navegador  
**Solución:** Usar script Python o extensión CORS

---

## 📊 MONITOREO Y VALIDACIÓN

### **Validar Token Actual**
```bash
# Ver token guardado
cat current_token.json

# Probar token manualmente
curl -H "Authorization: Bearer <token>" https://api.schwabapi.com/trader/v1/accounts
```

### **Indicadores de Token Válido**
- ✅ HTTP 200 en respuesta
- ✅ Datos de cuenta mostrados
- ✅ Timestamp reciente en `current_token.json`

### **Indicadores de Token Expirado**
- ❌ HTTP 401 Unauthorized
- ❌ Error "token expired"
- ❌ Timestamp > 30 minutos

---

## 📋 CHECKLIST DE MANTENIMIENTO

### **Diario:**
- [ ] Verificar que dashboard web funciona
- [ ] Confirmar datos de cuenta actualizados

### **Semanal:**
- [ ] Ejecutar `python generate_token.py` como backup
- [ ] Verificar que `.env` no ha cambiado

### **Mensual:**
- [ ] Revisar logs de errores
- [ ] Validar que refresh token sigue funcionando

---

## 🎯 COMANDOS RÁPIDOS

```bash
# Generar nuevo token
python generate_token.py

# Abrir dashboard
start dashboard.html

# Ver token actual
type current_token.json

# Verificar archivos críticos
dir .env generate_token.py dashboard.html
```

---

## 🚀 AUTOMATIZACIÓN AVANZADA

### **Auto-regeneración cada 25 minutos**
```python
import schedule
import time

def auto_regenerate():
    # Lógica de regeneración automática
    pass

schedule.every(25).minutes.do(auto_regenerate)
```

### **Webhook para notificaciones**
```python
# Notificar cuando token se renueva
requests.post("webhook_url", {"status": "token_renewed"})
```

---

## ✅ RESUMEN EJECUTIVO

**ARCHIVOS CRÍTICOS:** `.env`, `generate_token.py`, `dashboard.html`  
**FRECUENCIA:** Cada 30 minutos máximo  
**MÉTODOS:** Dashboard web + Script Python  
**VALIDACIÓN:** HTTP 200 + datos de cuenta  
**BACKUP:** `current_token.json` + logs  

**🎉 SISTEMA 100% FUNCIONAL Y PROBADO**

---

*Generado para TradePlus V5.0 - Mantener actualizado*