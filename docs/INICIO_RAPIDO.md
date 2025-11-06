# TradePlus - WebSockets Privados en Vivo

## ✅ Status: COMPLETADO

Ambos WebSockets funcionando con datos reales:
- ✅ **Coinbase**: BTC-USD, ETH-USD
- ✅ **Schwab**: Equities en tiempo real

## 🚀 Inicio Rápido

### Opción 1: Script automatizado (Recomendado)
```bash
python start_tradeplus.py
```
Esto inicia ambos servidores automáticamente.

### Opción 2: Manual (dos terminales)

**Terminal 1 - Hub FastAPI (puerto 8000):**
```bash
python -m hub.main
```

**Terminal 2 - Flask Dashboard (puerto 5000):**
```bash
python server.py
```

## 📊 Acceder al Dashboard

Una vez iniciados los servidores, abre tu navegador:

```
http://localhost:5000/test
```

Verás:
- **Panel en vivo** con ticks de Coinbase y Schwab
- **Estado de conexión** de cada broker
- **Contador de ticks** por segundo
- **Feed en tiempo real** con últimos precios

## 🔌 API Endpoints

El Hub FastAPI está disponible en `http://localhost:8000`:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del Hub |
| `/stats` | GET | Estadísticas en tiempo real |
| `/ticks` | GET | Último tick de cada símbolo |
| `/ws/live` | WS | WebSocket para ticks |
| `/docs` | GET | Documentación interactiva |

## 📁 Estructura de Archivos

```
hub/
├── hub.py                    # Orquestador FastAPI
├── main.py                   # Punto de entrada Hub
├── managers/
│   ├── coinbase_websocket_manager.py
│   └── schwab_websocket_manager.py
└── __init__.py

server.py                      # Dashboard Flask + API REST
start_tradeplus.py            # Script de inicio automático
docs/                         # Documentación
```

## 🔧 Configuración Requerida

Asegúrate de tener:

1. **JWT Coinbase** - Generado en `coinbase_current_jwt.json`
2. **Token OAuth Schwab** - Generado en `current_token.json`

Para regenerar tokens:
```bash
python generate_token.py      # Coinbase JWT
python regenerate_token.py    # Schwab OAuth
```

## 📊 Ejemplo de Respuesta /ticks

```json
{
  "BTC-USD": {
    "price": "42150.50",
    "side": "sell",
    "time": "2025-11-06T13:45:22.123Z"
  },
  "ETH-USD": {
    "price": "2280.75",
    "side": "buy",
    "time": "2025-11-06T13:45:22.456Z"
  }
}
```

## 🐛 Troubleshooting

### Hub no conecta
- Verifica que `current_token.json` tenga token válido (< 30 min)
- Verifica que `coinbase_current_jwt.json` tenga JWT válido (< 2 min)
- Regenera tokens si es necesario

### Dashboard muestra "DESCONECTADO"
- Verifica que el Hub está corriendo en puerto 8000
- Abre en navegador: `http://localhost:8000/health`

### No hay ticks
- Los ticks se capturan después de conectar (espera 5-10 segundos)
- Verifica logs en las terminales para errores

## 🎯 Próximos Pasos

- [ ] Persistencia a base de datos
- [ ] Histórico de ticks
- [ ] Alertas de precios
- [ ] Análisis técnico en vivo
- [ ] Trading automático
