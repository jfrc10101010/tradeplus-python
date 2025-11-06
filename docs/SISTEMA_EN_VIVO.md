# 🎯 COMPLETADO - TradePlus WebSockets en Vivo

## ✅ Status Final: LISTO PARA USAR

### 📊 Dashboard En Vivo Disponible
- **URL**: `http://localhost:5000/test`
- **Estado**: ✅ FUNCIONANDO
- **Conectividad**: 
  - ✅ Coinbase WebSocket (BTC-USD, ETH-USD)
  - ⏳ Schwab WebSocket (pendiente token válido)

---

## 🚀 Inicio Rápido

### Opción 1: Script Automatizado (RECOMENDADO)
```bash
python start_tradeplus.py
```

### Opción 2: Manual en Dos Terminales

**Terminal 1 - Hub API (puerto 8000):**
```bash
python -m hub.main
```

**Terminal 2 - Dashboard Flask (puerto 5000):**
```bash
python server.py
```

Luego abre en navegador:
```
http://localhost:5000/test
```

---

## 📈 Lo Que Ves En El Dashboard

### Panel Principal
- **Estado del Hub**: 🟢 CONECTADO (Coinbase Online)
- **Coinbase**: ✅ Conectado - BTC-USD, ETH-USD en vivo
- **Schwab**: ⏳ Desconectado (necesita token válido)

### Feed En Tiempo Real
- **Precio actual** de cada activo
- **Timestamp** exacto de cada tick
- **Información de volumen/side** (buy/sell)
- **Animación suave** con nuevos ticks

### Métricas En Vivo
- Ticks recibidos por broker
- Ticks por segundo (TPS)
- Histórico de últimos 50 ticks

---

## 🔧 Arquitectura

```
┌─────────────────────────────────────┐
│     NAVEGADOR (Dashboard)           │
│  http://localhost:5000/test         │
└──────────────────┬──────────────────┘
                   │ HTTP/Polling (500ms)
                   │
┌──────────────────▼──────────────────┐
│    FLASK (Puerto 5000)              │
│  ├─ /test          (HTML Dashboard) │
│  └─ /api/health    (Status API)     │
└──────────────────┬──────────────────┘
                   │ HTTP/REST
                   │
┌──────────────────▼──────────────────┐
│    FASTAPI HUB (Puerto 8000)        │
│  ├─ /health        (Status)         │
│  ├─ /stats         (Estadísticas)   │
│  ├─ /ticks         (Últimos ticks)  │
│  └─ /ws/live       (WebSocket)      │
└──────────────────┬──────────────────┘
                   │ Conexiones Privadas
        ┌──────────┴──────────┐
        │                     │
┌───────▼──────────┐  ┌──────▼────────────┐
│ COINBASE         │  │ SCHWAB            │
│ WebSocket        │  │ WebSocket         │
│ ✅ ACTIVO        │  │ ⏳ (Token 401)   │
│ BTC-USD          │  │ Equities          │
│ ETH-USD          │  │                   │
└──────────────────┘  └───────────────────┘
```

---

## 📡 Endpoints API Disponibles

### Hub FastAPI (http://localhost:8000)

| Endpoint | Método | Respuesta |
|----------|--------|-----------|
| `/health` | GET | Estado conectado |
| `/stats` | GET | Estadísticas en tiempo real |
| `/ticks` | GET | Últimos ticks (JSON) |
| `/ws/live` | WS | Stream WebSocket |
| `/docs` | GET | Documentación interactiva |

### Ejemplo GET /health
```json
{
  "status": "healthy",
  "stats": {
    "uptime_seconds": 45.2,
    "total_ticks": 23,
    "ticks_per_second": 0.51,
    "coinbase_connected": true,
    "schwab_connected": false,
    "coinbase_ticks": 23,
    "schwab_ticks": 0
  }
}
```

### Ejemplo GET /ticks
```json
{
  "BTC-USD": {
    "price": "42150.50",
    "side": "sell",
    "time": "2025-11-06T15:52:35.123Z"
  },
  "ETH-USD": {
    "price": "2280.75",
    "side": "buy",
    "time": "2025-11-06T15:52:35.456Z"
  }
}
```

---

## 🔑 Configuración Requerida

### Tokens Necesarios

#### 1. **Coinbase JWT** 
- Archivo: `coinbase_current_jwt.json`
- TTL: 2 minutos (regenerate automáticamente)
- Estado: ✅ **VÁLIDO**

#### 2. **Schwab OAuth Token**
- Archivo: `current_token.json`
- TTL: 30 minutos
- Estado: ❌ **EXPIRADO** (HTTP 401)

### Regenerar Tokens

**Para Coinbase (Si vence):**
```bash
python generate_token.py
```

**Para Schwab (Si vence):**
```bash
python regenerate_token.py
```

---

## 🐛 Estado Actual

### ✅ Funcionando
- [x] Hub FastAPI iniciado
- [x] Flask Dashboard operativo
- [x] Coinbase WebSocket conectado
- [x] Dashboard mostrando ticks reales de BTC/ETH
- [x] Polling a 500ms para actualización
- [x] API endpoints respondiendo
- [x] Interfaz visual en tiempo real

### ⏳ En Progreso
- [ ] Schwab WebSocket (esperando token válido)
- [ ] Persistencia a base de datos
- [ ] Histórico de ticks

### 📝 Próximas Fases
- [ ] Alertas de precios
- [ ] Análisis técnico en vivo (RSI, EMA)
- [ ] Trading automático
- [ ] Exportación de datos

---

## 📁 Estructura de Archivos

```
tradeplus-python/
├── hub/
│   ├── hub.py                      # Orquestador FastAPI
│   ├── main.py                     # Punto de entrada
│   └── managers/
│       ├── coinbase_websocket_manager.py
│       └── schwab_websocket_manager.py
│
├── server.py                       # Dashboard Flask
├── start_tradeplus.py             # Script inicio automático
│
├── coinbase_current_jwt.json      # JWT válido
├── current_token.json             # OAuth token Schwab
│
└── docs/                          # Documentación
    ├── INICIO_RAPIDO.md          # Este archivo
    └── [otros documentos]
```

---

## 💡 Tips & Tricks

### Ver logs en tiempo real
```bash
# Terminal 1: Hub
python -m hub.main

# Terminal 2: Flask
python server.py
```

### Verificar conectividad API
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
curl http://localhost:8000/ticks
```

### Debuggear desde Python
```python
import requests
response = requests.get('http://localhost:8000/health')
print(response.json())
```

### Acceder a documentación API
```
http://localhost:8000/docs
```

---

## ⚠️ Troubleshooting

### "DESCONECTADO" en Dashboard
1. Verifica que Hub está corriendo: `python -m hub.main`
2. Verifica que Flask está corriendo: `python server.py`
3. Abre http://localhost:8000/health en navegador

### Schwab: "HTTP 401"
1. Token OAuth expiró (30 min TTL)
2. Regenera: `python regenerate_token.py`
3. Reinicia Hub: Presiona Ctrl+C y ejecuta `python -m hub.main`

### No hay ticks de Coinbase
1. JWT expiró (2 min TTL)
2. Regenera: `python generate_token.py`
3. Reinicia Hub
4. Espera 5-10 segundos para que conecte

### Puerto ya en uso
```bash
# Matara proceso en puerto 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

## 🎓 Tecnologías Usadas

- **Backend**: Python
  - FastAPI + Uvicorn (Hub API)
  - Flask (Dashboard)
  - WebSockets (Coinbase & Schwab)
  
- **Frontend**: HTML5 + CSS3 + JavaScript
  - Polling a 500ms
  - Animaciones suaves
  - Terminal styling

- **Brokers**:
  - Coinbase (Advanced Trade API)
  - Schwab (Private Streamer API)

---

## 📞 Soporte

Para problemas:
1. Revisa los logs en las terminales
2. Verifica `/health` endpoint
3. Regenera tokens si es necesario
4. Consulta la documentación en `/docs`

---

**Última actualización:** 2025-11-06  
**Estado:** ✅ LISTO PARA USAR  
**Coinbase:** ✅ FUNCIONANDO  
**Schwab:** ⏳ PENDIENTE TOKEN
