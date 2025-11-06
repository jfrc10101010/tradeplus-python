# 🚀 WebSocket Dashboard - TradePlus

Dashboard web en tiempo real que muestra datos privados de **Schwab** y **Coinbase** simultáneamente.

## ✨ Características

- **Tiempo Real**: Actualiza datos cada 5 segundos
- **Paralelo**: Schwab y Coinbase funcionan independientemente
- **Sin conflictos**: Un broker no interfiere con el otro
- **Autenticación**: Tokens se renuevan automáticamente
- **UI Responsiva**: Interfaz web moderna y fluida

## 📊 Secciones del Dashboard

### Schwab
- Saldo de la cuenta (Cash, Buying Power, Liquidation Value)
- Posiciones abiertas (hasta 5 principales)
- Información en tiempo real

### Coinbase  
- Wallets/Cuentas (hasta 10)
- Saldos por moneda
- Fondos disponibles

## 🎯 Cómo Usar

### Opción 1: Script .bat (Recomendado para Windows)
```bash
start-dashboard.bat
```

### Opción 2: Comando Python
```bash
python websocket_dashboard.py
```

### Opción 3: Script de Inicio Robusto
```bash
python run_dashboard.py
```

## 🌐 Acceder al Dashboard

Una vez iniciado, abre en tu navegador:
```
http://localhost:8000
```

## 🔄 Renovación Automática de Tokens

- **Schwab**: Token OAuth renovado cada 25 minutos (antes del vencimiento de 30 min)
- **Coinbase**: JWT renovado cada 100 segundos (válido 120 segundos)

## 📋 Arquitectura

El dashboard usa:
- **FastAPI**: Backend WebSocket
- **Uvicorn**: Servidor ASGI
- **Asyncio**: Tareas paralelas independientes
- **JavaScript/WebSocket**: Frontend en tiempo real

### Tareas en Background

1. `update_schwab_data()` - Obtiene datos cada 5 segundos
2. `update_coinbase_data()` - Obtiene datos cada 5 segundos
3. WebSocket servers para broadcasting

**Importante**: Cada tarea es completamente independiente. Si una falla, la otra continúa.

## 🔧 Configuración

Los archivos de configuración esperados:
```
hub/
  ├── .env (SCHWAB_CREDENTIALS)
  └── apicoinbase1fullcdp_api_key.json (API KEY + PRIVATE KEY)
```

## ⚠️ Solución de Problemas

### "Error: No se puede conectar a localhost:8000"
- Asegúrate que el servidor está corriendo
- Verifica que el puerto 8000 está disponible
- Intenta acceder a `http://127.0.0.1:8000`

### "Schwab: Connected ❌"
- Verifica credenciales en `.env`
- Comprueba que el token de refresh es válido
- Revisa logs del servidor

### "Coinbase: Connected ❌"
- Verifica `apicoinbase1fullcdp_api_key.json`
- Asegúrate que la clave privada es válida
- Revisa que tienes permisos de lectura en API

## 📈 Performance

- Latencia: ~500ms-2s por actualización
- Usando: 1-3 conexiones HTTP simultáneas
- Memoria: ~50-100 MB
- CPU: Bajo (<5% cuando inactivo)

## 🎓 Ejemplos de Datos

### Schwab Response
```json
{
  "balance": {
    "cash": 50000,
    "buying_power": 100000,
    "liquidation_value": 150000
  },
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "averagePrice": 150.50,
      "marketValue": 18500
    }
  ]
}
```

### Coinbase Response
```json
{
  "accounts": [
    {
      "uuid": "...",
      "currency": "BTC",
      "balance": "0.5",
      "hold": "0.1",
      "available": "0.4"
    }
  ]
}
```

## 🛠️ Desarrollo

Para personalizar el dashboard:

1. Edita estilos CSS en `websocket_dashboard.py` (sección HTML)
2. Modifica lógica de actualización en funciones `update_*`
3. Agrega nuevos endpoints/WebSockets según necesites

## 📝 Licencia

Parte del proyecto TradePlus
