# 🚀 TRADEPLUS - Multi-broker Trading Platform

**Stack Oficial:** Python 3.9+ | FastAPI | Node.js 16+ | Real-time WebSocket

---

## 📋 REQUISITOS

- **Python 3.9+** (descargar desde https://python.org)
- **Node.js 16+** (descargar desde https://nodejs.org)
- **Credenciales Schwab/TOS** (token OAuth necesario)

---

## ⚡ INSTALACIÓN RÁPIDA (3 pasos)

### Opción A: AUTOMÁTICA (Recomendada)

```powershell
# Windows PowerShell
cd tradeplus-python
python install.py
```

Esto hará TODO automáticamente:
- ✅ Crear venv Python
- ✅ Instalar paquetes Python
- ✅ Instalar dependencias Node.js
- ✅ Validar estructura completa

### Opción B: MANUAL (paso a paso)

#### PASO 1: Backend Python

```powershell
cd backend

# Crear venv
python -m venv venv

# Activar venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

#### PASO 2: Obtener Token Schwab (SOLO PRIMERA VEZ)

```powershell
# Desde la terminal con venv activado
python scripts/get_schwab_token.py
```

Se abrirá navegador automáticamente para autorizar. Después:
- ✅ Token guardado en `.schwab_token.json`
- ✅ Backend listo para usar

#### PASO 3: Frontend Node.js

```powershell
cd frontend
npm install
```

---

## 🎬 EJECUCIÓN

### OPCIÓN 1: QUICK START (Automático - RECOMENDADO)

Una línea y se abre todo:

```powershell
cd tradeplus-python
python quick-start.py
```

Se abrirán 3 terminales automáticamente:
1. Backend corriendo
2. Frontend corriendo
3. Monitor con URLs

### OPCIÓN 2: MANUAL (3 terminales)

**Terminal 1 - Backend (Puerto 5000)**
```powershell
cd backend
venv\Scripts\activate
python main.py
```

Verás:
```
🔐 Autenticando con Schwab...
✅ Cliente Schwab autenticado
📊 Tick AAPL: $150.25
📊 Tick MSFT: $325.10
✅ Conectado a Coinbase (REAL)
📊 Tick BTC-USD: $42500.50
```

**Terminal 2 - Frontend (Puerto 8080)**
```powershell
cd frontend
npm start
```

Verás:
```
✅ Frontend running on http://localhost:8080
```

**Terminal 3 - Pruebas (opcional)**
```powershell
# Verificar salud del API
curl http://localhost:5000/health

# Obtener output
{"status": "ok", "service": "TRADEPLUS API", "connected_clients": 1}
```

---

## 🌐 ACCESO

Abre en tu navegador:

| URL | Descripción |
|-----|-------------|
| http://localhost:8080 | **Frontend en tiempo real** (datos REALES de Schwab + Coinbase) |
| http://localhost:5000/health | API health check |
| ws://localhost:5000/ws | WebSocket para datos en vivo |

---

## 🏗️ ESTRUCTURA DEL PROYECTO

```
tradeplus-python/
├── backend/
│   ├── adapters/
│   │   ├── base.py                 # Clase base para adapters
│   │   ├── schwab_adapter.py       # ✅ REAL: Schwab/TOS con schwab-py
│   │   └── coinbase_adapter.py     # ✅ REAL: Coinbase WebSocket
│   ├── core/
│   │   ├── models.py               # Tick, Candle (modelos normalizados)
│   │   ├── normalizer.py           # Convierte raw data a modelos
│   │   └── candle_builder.py       # Genera velas cada minuto
│   ├── scripts/
│   │   └── get_schwab_token.py     # OAuth para Schwab (primera vez)
│   ├── main.py                     # 🚀 FastAPI + WebSocket
│   ├── requirements.txt            # Dependencias Python
│   ├── .env                        # Credenciales Schwab
│   └── venv/                       # Virtual environment (creado por install.py)
│
├── frontend/
│   ├── js/
│   │   └── client.js               # WebSocket client + AG Grid + Charts
│   ├── index.html                  # Interface HTML
│   ├── package.json                # Dependencias Node
│   └── server.js                   # Express server
│
├── install.py                      # 🔧 Setup automático
├── quick-start.py                  # ⚡ Arranca todo en una línea
├── start-tradeplus.bat             # 🪟 Batch para Windows
└── README.md                       # Este archivo
```

---

## 🔌 STACK TÉCNICO (100% OFICIAL)

| Componente | Librería | Versión |
|-----------|----------|---------|
| **Schwab/TOS** | `schwab-py` | 0.4.8 ✅ OFICIAL |
| **Coinbase** | WebSocket nativa | wss-feed pública |
| **API/WebSocket** | FastAPI | 0.104.1 |
| **Server HTTP** | Uvicorn | 0.24.0 |
| **Frontend** | Express + Vanilla JS | 4.18.2 |
| **Charts** | Chart.js | 4.4.0 |
| **Grid** | AG Grid | community |

---

## 📊 CARACTERÍSTICAS

✅ **Multi-broker en tiempo real** (Schwab + Coinbase)  
✅ **WebSocket bidireccional**  
✅ **Velas OHLCV normalizadas** (1 minuto por defecto)  
✅ **Frontend interactivo** con gráficos en vivo  
✅ **100% REAL** (no simulado)  
✅ **Sin rate limiting** (respeta límites de brokers)  

---

## 🆘 TROUBLESHOOTING

### ❌ Error: "ModuleNotFoundError: No module named 'schwab'"

**Solución:** Falta instalar venv y dependencias
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### ❌ Error: "OAuth token inválido"

**Solución:** Obtener token nuevo
```powershell
# Desde backend con venv activado
python scripts/get_schwab_token.py
# Se abre navegador para autorizar
# Se guarda en .schwab_token.json
```

### ❌ Error: "Port 5000 already in use"

**Solución:** Otra app usa puerto 5000
```powershell
# Cambiar puerto en backend/main.py (línea final)
# O matar proceso existente
taskkill /F /IM python.exe  # Cuidado: mata todos los Python
```

### ❌ Error: "npm not found"

**Solución:** Instalar Node.js desde https://nodejs.org

### ❌ Frontend muestra "Desconectado"

**Solución:** Verificar que backend esté corriendo
```powershell
# En otra terminal
curl http://localhost:5000/health
# Si da error, backend no está corriendo
```

---

## 📝 PRÓXIMOS PASOS

- [ ] Integración de órdenes (place trades)
- [ ] Base de datos (SQLite para histórico)
- [ ] Indicadores técnicos (RSI, MACD, etc)
- [ ] Backtest engine
- [ ] Dashboard de performance

---

## 🎓 NOTAS IMPORTANTES

1. **Token Schwab**: Válido por ~90 días. Se renueva automáticamente.
2. **Coinbase**: API pública, sin autenticación necesaria.
3. **Rate Limiting**: Schwab limita a X llamadas/segundo. Ya manejado.
4. **Datos reales**: NO es simulación. Están los precios reales de mercado.

---

## 📞 SOPORTE

¿Problemas? Verifica:
1. Python 3.9+ instalado: `python --version`
2. Node.js 16+ instalado: `npm --version`
3. Credenciales Schwab correctas en `.env`
4. Token obtenido: `.schwab_token.json` existe
5. Puertos 5000 y 8080 libres

---

**¡Disfruta TRADEPLUS! 🚀**
