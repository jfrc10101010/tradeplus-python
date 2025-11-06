# ⚡ TRADEPLUS - QUICK REFERENCE

## 🚀 INICIO RÁPIDO (30 SEGUNDOS)

```powershell
# UNA LÍNEA PARA ARRANCARLO TODO:
cd c:\Users\joser\TradePlus\tradeplus-python; python quick-start.py
```

Se abre todo automáticamente. Abre navegador: **http://localhost:8080**

---

## 📋 PRIMERO: SETUP (UNA SOLA VEZ)

```powershell
# Instalar todo
cd c:\Users\joser\TradePlus\tradeplus-python
python install.py

# Obtener token Schwab (una sola vez)
cd backend
venv\Scripts\activate
python scripts/get_schwab_token.py
# Se abre navegador → Autoriza → Listo
```

---

## 🎬 EJECUCIÓN NORMAL (después del setup)

### Opción 1: AUTOMÁTICA (Recomendada)

```powershell
cd c:\Users\joser\TradePlus\tradeplus-python
python quick-start.py
```

Se abre todo en 3 terminales. Acceso: **http://localhost:8080**

### Opción 2: MANUAL (3 terminales)

```powershell
# TERMINAL 1: Backend
cd c:\Users\joser\TradePlus\tradeplus-python\backend
venv\Scripts\activate
python main.py
```

```powershell
# TERMINAL 2: Frontend
cd c:\Users\joser\TradePlus\tradeplus-python\frontend
npm start
```

```powershell
# TERMINAL 3: Pruebas (opcional)
curl http://localhost:5000/health
```

---

## 🌐 ACCESO

| Qué | Dónde |
|-----|-------|
| Frontend | http://localhost:8080 |
| Health Check | http://localhost:5000/health |
| WebSocket | ws://localhost:5000/ws |

---

## ❌ PROBLEMAS RÁPIDOS

| Problema | Solución |
|----------|----------|
| **"ModuleNotFoundError"** | `cd backend && venv\Scripts\activate && pip install -r requirements.txt` |
| **"Port already in use"** | `taskkill /F /IM python.exe` (mata todos los Python) |
| **"oauth token invalid"** | `cd backend && venv\Scripts\activate && python scripts/get_schwab_token.py` |
| **"npm not found"** | Descargar Node.js desde https://nodejs.org |
| **"Frontend desconectado"** | Verifica backend corriendo: `curl http://localhost:5000/health` |

---

## 📁 ESTRUCTURA

```
tradeplus-python/
├── backend/               → Python FastAPI
├── frontend/              → Node.js Express
├── install.py             → Setup automático ← EJECUTA ESTO PRIMERO
├── quick-start.py         → Arranca todo
└── README.md              → Guía completa
```

---

## ✅ CHECKLIST: "¿Está funcionando?"

- [ ] Terminal 1: Backend mostrando "✅ Conectado a Schwab"
- [ ] Terminal 2: Frontend mostrando "✅ Frontend running"
- [ ] Navegador: http://localhost:8080 muestra "🟢 Conectado"
- [ ] Tabla: Mostrando datos (AAPL, MSFT, BTC, ETH)
- [ ] Gráfico: Actualizándose en tiempo real
- [ ] Health: `curl http://localhost:5000/health` → JSON OK

---

## 🎯 FLUJO TÍPICO

```
1. Primera vez:
   python install.py
   (backend) python scripts/get_schwab_token.py
   
2. Después, siempre:
   python quick-start.py
   
3. Abrir navegador:
   http://localhost:8080
```

---

## 📞 AYUDA

Ver archivo: **DEBUGGING.md** para troubleshooting detallado

---

**¡Listo! Disfruta TRADEPLUS 🚀**
