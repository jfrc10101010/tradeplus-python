# Test Server Setup - Journal Module

## 📋 Requerimientos

- Node.js 16+ instalado
- PM2 instalado globalmente: `npm install -g pm2`
- Python 3.8+ con módulos journal configurados

## 🚀 Instalación Rápida

### Paso 1: Instalar dependencias
```powershell
cd test
npm install
```

### Paso 2: Crear carpeta de logs
```powershell
mkdir logs
```

### Paso 3: Iniciar con PM2
```powershell
# Desde la carpeta raíz del proyecto
pm2 start ecosystem-journal.config.js
```

O desde VS Code terminal:
```powershell
cd c:\Users\joser\TradePlus\tradeplus-python
npm install --prefix test
pm2 start ecosystem-journal.config.js
```

## 📍 Acceder al Servidor

```
http://localhost:8080
```

**Eso es todo.** El servidor está VIVO con datos en tiempo real.

## 🔄 API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/journal` | GET | Journal completo + trades |
| `/api/journal/stats` | GET | Solo estadísticas |
| `/api/journal/broker/schwab` | GET | Trades de Schwab |
| `/api/journal/broker/coinbase` | GET | Fills de Coinbase |
| `/api/status` | GET | Estado del servidor |
| `/api/health` | GET | Health check |
| `/api/refresh` | POST | Fuerza actualización |

## 📊 Ejemplo GET /api/journal

```json
{
  "timestamp": "2025-11-07T15:30:45.123Z",
  "trades": [
    {
      "id": "12345",
      "datetime": "2025-11-07T14:22:00Z",
      "symbol": "AAPL",
      "side": "BUY",
      "quantity": 100,
      "price": 234.50,
      "fee": 0.99,
      "total": 23450.00,
      "broker": "schwab"
    }
  ],
  "stats": {
    "total_trades": 45,
    "total_volume": 156234.50,
    "total_fees": 45.67,
    "buys": 25,
    "sells": 20,
    "by_broker": {
      "schwab": {
        "trades": 30,
        "volume": 89234.50,
        "fees": 25.00
      },
      "coinbase": {
        "trades": 15,
        "volume": 67000.00,
        "fees": 20.67
      }
    }
  }
}
```

## 🎮 Funcionalidades de la UI

- ✅ **Actualización en tiempo real** (cada 30 segundos automático)
- ✅ **Estadísticas por broker** (Schwab vs Coinbase)
- ✅ **Tabla interactiva** de trades
- ✅ **Botón de refresh manual**
- ✅ **Auto-refresh toggleable** (cada 10 seg)
- ✅ **Descargar JSON** de datos completos
- ✅ **Indicadores de status** (online/offline)

## 🛠️ Comandos PM2

```powershell
# Ver estado
pm2 status

# Ver logs en tiempo real
pm2 logs journal-test

# Reiniciar
pm2 restart journal-test

# Parar
pm2 stop journal-test

# Reanudar
pm2 start journal-test

# Eliminar
pm2 delete journal-test

# Monitoreo
pm2 monit
```

## 🧪 Verificar que funciona

```powershell
# Prueba la API directamente
curl http://localhost:8080/api/health

# Debería responder:
# {"status":"healthy","timestamp":"2025-11-07T15:30:45.123Z"}
```

## 📝 Logs

Los logs se guardan automáticamente en:
- `logs/journal-test-out.log` - stdout
- `logs/journal-test-error.log` - errores

Verlos en tiempo real:
```powershell
pm2 logs journal-test
```

## 🚨 Si falla...

### Error: "Cannot find module 'express'"
```powershell
cd test
npm install
```

### Error: "Python script failed"
- Verifica que los adapters están en `hub/journal/`
- Verifica que los token managers funcionan
- Mira el error con: `pm2 logs journal-test`

### Error: "Port 8080 already in use"
```powershell
# Cambiar puerto en ecosystem-journal.config.js
# O: netstat -ano | findstr :8080
```

## ✅ Confirmación de Funcionalidad

Cuando veas esto en navegador:
1. ✅ Tabla de trades visible
2. ✅ Números actualizando cada 30 seg
3. ✅ Status "Online" en verde
4. ✅ Botones funcionando

= **TODO ESTÁ WORKING**
