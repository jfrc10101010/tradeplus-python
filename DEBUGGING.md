# ✅ TRADEPLUS - GUÍA RÁPIDA DE DEBUGGING

## ❓ "¿Cómo sé si está funcionando?"

Usa esta checklist:

### 1️⃣ Backend Corriendo (Puerto 5000)

En terminal con backend:

```
Debería ver algo EXACTO como esto:

🔐 Autenticando con Schwab...
✅ Cliente Schwab autenticado
🔌 Obteniendo credenciales del streamer...
✅ Credenciales del streamer obtenidas
   URL: wss://streamer-api.schwab.com/ws
   User: tu_usuario_schwab
✅ Suscrito a Schwab: ['AAPL', 'MSFT', 'TSLA']
🔄 Iniciando loop de datos...
📊 Tick AAPL: $150.25
📊 Tick MSFT: $325.10
✅ Conectado a Coinbase (REAL)
✅ Suscrito a Coinbase: ['BTC-USD', 'ETH-USD']
📨 Mensaje de suscripción enviado a: ['BTC-USD', 'ETH-USD']
📊 Tick BTC-USD: $42500.50
✅ Cliente conectado. Total: 1
```

### 2️⃣ Frontend Corriendo (Puerto 8080)

En terminal con frontend:

```
Debería ver:

✅ Frontend running on http://localhost:8080
```

### 3️⃣ Probar desde Terminal 3

```powershell
# Verificar que backend está respondiendo
curl http://localhost:5000/health

# Salida esperada:
{"status":"ok","service":"TRADEPLUS API","connected_clients":1}
```

### 4️⃣ Navegador: http://localhost:8080

Debería mostrar:
- ✅ "🟢 Conectado" en la esquina superior
- 📊 Tabla con datos (Schwab AAPL/MSFT/TSLA + Coinbase BTC/ETH)
- 📈 Gráfico actualizándose en tiempo real

---

## ❌ ERRORES COMUNES Y SOLUCIONES

### Error: "ModuleNotFoundError: No module named 'fastapi'"

```
PROBLEMA: No está instalado el venv o faltan dependencias

SOLUCIÓN:
  cd backend
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
```

### Error: "ConnectionRefusedError: [Errno 10061]"

```
PROBLEMA: Frontend no puede conectar a backend (puerto 5000 no disponible)

SOLUCIÓN:
  1. Verifica que backend está corriendo:
     curl http://localhost:5000/health
  
  2. Si dice "connection refused", backend no está activo
     - Abre otra terminal
     - cd backend
     - venv\Scripts\activate
     - python main.py
```

### Error: "Port 5000 already in use"

```
PROBLEMA: Otro proceso usa puerto 5000

SOLUCIONES:
  Opción 1: Cambiar puerto en backend/main.py (línea final):
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
  
  Opción 2: Matar proceso existente:
    netstat -ano | findstr :5000
    taskkill /PID <PID> /F
```

### Error: "ModuleNotFoundError: schwab"

```
PROBLEMA: schwab-py no está instalado

SOLUCIÓN:
  cd backend
  venv\Scripts\activate
  pip install schwab-py==0.4.8
```

### Error: "Token inválido" o "oauth error"

```
PROBLEMA: Token de Schwab expirado o no existe

SOLUCIÓN:
  cd backend
  venv\Scripts\activate
  python scripts/get_schwab_token.py
  
  Se abrirá navegador para autorizar
  Presiona "Allow" cuando se pida
  Token se guardará en .schwab_token.json
```

### Error: "npm: command not found"

```
PROBLEMA: Node.js no está instalado

SOLUCIÓN:
  1. Descargar desde https://nodejs.org
  2. Instalar (seguir wizard)
  3. Abrir nueva terminal PowerShell
  4. Probar: npm --version
```

### Error: "WebSocket connection failed" en frontend

```
PROBLEMA: Frontend no puede conectar a WebSocket del backend

SOLUCIÓN:
  1. Verificar backend está corriendo:
     curl http://localhost:5000/health
  
  2. Si no responde, iniciar backend:
     cd backend
     venv\Scripts\activate
     python main.py
  
  3. Esperar a que diga "Cliente conectado"
  
  4. Recargar frontend en navegador (F5)
```

---

## 📊 VALIDACIÓN PASO A PASO

### ¿Tengo Python 3.9+?

```powershell
python --version
# Debe mostrar algo como: Python 3.10.5 o superior
```

### ¿Tengo Node.js 16+?

```powershell
node --version
npm --version
# node debe ser v16 o superior
```

### ¿Está el venv creado?

```powershell
cd backend
ls venv
# Debe haber carpeta venv
```

### ¿Está activado el venv?

```powershell
cd backend
venv\Scripts\activate
# El prompt debe cambiar a mostrar (venv) al principio
```

### ¿Están instaladas dependencias Python?

```powershell
cd backend
venv\Scripts\activate
pip list
# Debe mostrar: fastapi, uvicorn, schwab-py, websockets, etc.
```

### ¿Están instaladas dependencias Node?

```powershell
cd frontend
npm list --depth=0
# Debe mostrar: express@^4.18.2
```

### ¿Tengo token Schwab?

```powershell
cd backend
ls .schwab_token.json
# Si no existe, ejecutar:
venv\Scripts\activate
python scripts/get_schwab_token.py
```

### ¿Funciona el health check?

```powershell
# En terminal separada
curl http://localhost:5000/health

# Debe responder algo como:
{"status":"ok","service":"TRADEPLUS API","connected_clients":0}
```

---

## 🎬 FLUJO CORRECTO DE INICIO

```
1. Abre Terminal 1
   cd backend
   venv\Scripts\activate
   python main.py
   
   ✅ Espera a ver:
      "✅ Conectado a Schwab"
      "✅ Conectado a Coinbase"
   
2. Abre Terminal 2
   cd frontend
   npm start
   
   ✅ Espera a ver:
      "✅ Frontend running on http://localhost:8080"
   
3. Abre navegador
   http://localhost:8080
   
   ✅ Espera a ver:
      "🟢 Conectado" en esquina superior
      Tabla con datos actualizándose
      Gráfico moviéndose

4. (Opcional) Terminal 3
   curl http://localhost:5000/health
   
   ✅ Debe responder JSON con status "ok"
```

---

## 💡 TIPS

- **Mantén ambas terminales abiertas**: Backend y Frontend deben estar corriendo juntos
- **Si recarga el navegador**: Será reconectado automáticamente
- **Logs en tiempo real**: Los ves en las terminales de backend y frontend
- **Para parar**: Ctrl+C en cualquier terminal (o cierra la ventana)

---

## ✅ "OK, ¿cómo sé que está perfecto?"

Si ves TODO esto = ✅ ÉXITO:

```
BACKEND TERMINAL:
✅ Conectado a Schwab
📊 Tick AAPL: $...
📊 Tick MSFT: $...
✅ Conectado a Coinbase
📊 Tick BTC-USD: $...
✅ Cliente conectado

FRONTEND TERMINAL:
✅ Frontend running on http://localhost:8080

NAVEGADOR:
🟢 Conectado
[Tabla con datos actualizándose]
[Gráfico en tiempo real]

CURL:
curl http://localhost:5000/health
→ {"status":"ok", ...}
```

**¡Si lo ves, TRADEPLUS está 100% funcionando! 🚀**
