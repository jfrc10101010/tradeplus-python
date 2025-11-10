# 📦 INSUMOS PARA T0 - JOURNAL MANAGER REFACTOR
**Fecha:** 2025-11-08  
**Para:** Claude Arquitecto (Perplexity)  
**Objetivo:** Entregar T0 en <60 minutos

---

## ✅ INSUMO #1: Fixtures de Datos Reales

### 📄 `/test/fixtures/coinbase_sample.json`
**Estado:** ✅ Generado con datos reales  
**Ubicación:** `c:\Users\joser\TradePlus\tradeplus-python\test\fixtures\coinbase_sample.json`

**Estructura de cada trade:**
```json
{
  "id": "515e7804-eeb5-4922-b659-ab4be6dcf519",
  "datetime": "2025-11-07T15:23:20.415658+00:00",
  "symbol": "BTC-USD",
  "side": "BUY",
  "quantity": 0.00492942,
  "price": 100823.16,
  "fee": 2.9819982082032,
  "amount": 497.0,
  "broker": "coinbase"
}
```

**Campos normalizados:**
- `id`: UUID único del fill
- `datetime`: ISO 8601 con timezone UTC
- `symbol`: Par crypto (BTC-USD, ETH-USD, etc.)
- `side`: "BUY" | "SELL"
- `quantity`: Cantidad de base currency (BTC, ETH)
- `price`: Precio de ejecución
- `fee`: Comisión cobrada
- `amount`: Total en USD (sin fee)
- `broker`: "coinbase"

---

### 📄 `/test/fixtures/schwab_sample.json`
**Estado:** ✅ Generado con datos de muestra basados en estructura real  
**Ubicación:** `c:\Users\joser\TradePlus\tradeplus-python\test\fixtures\schwab_sample.json`

**Estructura esperada de cada trade (basada en adapter actual):**
```json
{
  "id": "123456789",
  "datetime": "2025-11-07T14:30:00+00:00",
  "symbol": "HOOD",
  "side": "BUY",
  "quantity": 5.0,
  "price": 35.42,
  "total": 177.10,
  "broker": "schwab"
}
```

**Campos normalizados:**
- `id`: Transaction ID de Schwab
- `datetime`: ISO 8601 con timezone
- `symbol`: Ticker de equity (HOOD, NU, AMD, etc.)
- `side`: "BUY" | "SELL"
- `quantity`: Número de acciones
- `price`: Precio por acción
- `total`: Total USD (quantity * price)
- `broker`: "schwab"

**NOTA:** Datos de muestra creados manualmente siguiendo la estructura del adapter actual.  
Incluye casos de prueba para:
- Posiciones abiertas: HOOD (15 shares en 2 compras), NU (2 shares en 2 compras), NVDA, COIN
- Posiciones cerradas: AMD (compra + venta completa con profit)
- Mix de fechas últimos 7 días

---

## ✅ INSUMO #2: Endpoint Actual de API Journal

### 🌐 **URL Base del Servidor**
```
http://localhost:8080
```

### 📍 **Endpoints Disponibles:**

#### 1️⃣ **GET `/api/journal`** - Journal Combinado
```
URL: http://localhost:8080/api/journal?days=30
Método: GET
Query Params:
  - days: número de días hacia atrás (default: 30)

Respuesta Actual:
{
  "trades": [...],        // Array combinado Schwab + Coinbase
  "stats": {
    "total_trades": 48,
    "open_positions": 5,
    "closed_positions": 9,
    "win_rate": 72.92,
    "profit_factor": 2.62
  },
  "capital": {
    "initial": 5000.0,
    "current": 5807.16,     // ⚠️ Puede estar cacheado
    "pl_total_usd": 807.16
  },
  "timestamp": "2025-11-08T..."
}
```

#### 2️⃣ **GET `/api/journal/broker/:name`** - Broker Específico
```
URL: http://localhost:8080/api/journal/broker/schwab?days=7
     http://localhost:8080/api/journal/broker/coinbase?days=7
Método: GET
Path Params:
  - name: 'schwab' | 'coinbase'
Query Params:
  - days: número de días (default: 7)

Respuesta:
{
  "trades": [...],        // Solo del broker solicitado
  "stats": { ... },       // Stats calculados con P&L
  "capital": { ... },
  "broker": "schwab",
  "timestamp": "..."
}
```

#### 3️⃣ **GET `/api/journal/stats`** - Solo Estadísticas
```
URL: http://localhost:8080/api/journal/stats
Método: GET

Respuesta:
{
  "stats": { ... },
  "timestamp": "..."
}
```

### 🔧 **Implementación Actual (Backend):**
```javascript
// test/server.js - Línea ~45
function fetchJournalData(days = 30) {
    // Ejecuta Python subprocess en cada request
    const pythonScript = `
import sys
sys.path.insert(0, '${hubPath}')
from journal.journal_manager import JournalManager
manager = JournalManager(capital_initial=5000.0)
result = manager.get_combined_journal(days=${days})
print(json.dumps(result, indent=2, default=str))
    `;
    
    const python = spawn('python', ['-c', pythonScript], {
        cwd: projectRoot,  // ⚠️ Importante: donde está .env
        timeout: 30000
    });
}
```

**⚠️ PROBLEMA DE PERFORMANCE IDENTIFICADO:**
- Cada cambio de filtro (7d → 30d) ejecuta un proceso Python completo
- Importa módulos, conecta APIs, genera tokens: **10-15 segundos**
- Usuario espera demasiado por cada cambio

**NOTA:** Este endpoint DEBE seguir funcionando después del refactor. El nuevo `journalmanager.py` debe ser compatible.

---

## ✅ INSUMO #3: Frecuencia de Refresh

### ⏱️ **Configuración Actual:**

#### Frontend (`test/public/journal.html` - Línea 1192):
```javascript
// Auto-refresh cada 2 segundos (API REST)
setInterval(loadData, 2 * 1000);
```

**REFRESH_MS = 2000** (2 segundos)

#### Otros intervalos en el sistema:
```javascript
// test/public/index.html
setInterval(refreshData, 30000);  // Dashboard general: 30s

// Auto-refresh manual
autoRefreshInterval = setInterval(refreshData, 10000);  // 10s
```

### 🎯 **Decisión para T0:**

**Usar REFRESH_MS = 5000 (5 segundos)** por estas razones:

1. **Balance perfecto:**
   - No es tan agresivo como 2s (reduce carga en API)
   - Sigue siendo "casi tiempo real" para el usuario
   - Suficiente para P&L no realizado (precios cambian cada ~1s pero no es crítico)

2. **Compatible con API REST actual:**
   - 5s no saturará el servidor Node.js
   - Da tiempo al subprocess Python a completar (si hay cola)

3. **Preparado para WebSocket futuro:**
   - Cuando migremos a WebSocket, bajaremos a 2s o push on-change
   - Por ahora 5s es conservador y funcional

**CONFIRMADO: REFRESH_MS = 5000**

---

## 📋 CHECKLIST PARA T0

Con estos 3 insumos, el arquitecto debe entregar:

### ✅ **1. `hub/journal/journal_manager.py` refactorizado**
- [ ] Agrupación por símbolo (FIFO)
- [ ] Separar operaciones abiertas vs cerradas
- [ ] Wins/losses count
- [ ] Win rate calculado
- [ ] Profit factor
- [ ] P&L realizado USD + porcentaje
- [ ] P&L no realizado USD (con precios actuales)
- [ ] Salida JSON estándar multi-broker

### ✅ **2. Scripts de test en `/test`**
- [ ] `test/verify_positions.py` - Verifica conteo de posiciones
- [ ] `test/verify_metrics.py` - Valida cálculos P&L, win rate, etc.
- [ ] Sin mocks, solo asserts contra fixtures reales
- [ ] Guía de ejecución paso a paso

### ✅ **3. Compatibilidad con sistema actual**
- [ ] `/api/journal?days=30` sigue funcionando
- [ ] Estructura JSON de respuesta compatible
- [ ] Frontend no requiere cambios inmediatos

---

## 🚀 EJECUCIÓN POST-ENTREGA

Una vez recibido el código del arquitecto:

1. **Copiar archivos:**
   ```bash
   # Copiar journal_manager.py refactorizado
   cp [archivo_del_arquitecto] hub/journal/journal_manager.py
   
   # Copiar tests
   cp [tests] test/
   ```

2. **Ejecutar tests con datos reales:**
   ```bash
   cd test
   python verify_positions.py
   python verify_metrics.py
   ```

3. **Validar endpoint:**
   ```bash
   # Reiniciar servidor
   pm2 restart journal-test
   
   # Probar endpoint
   curl http://localhost:8080/api/journal?days=7
   ```

4. **Revisar frontend:**
   - Abrir `http://localhost:8080/journal.html`
   - Verificar que métricas se actualizan correctamente
   - Probar filtros de período

5. **Aprobar o reportar issues**

---

## 📝 NOTAS FINALES

### **Capital Inicial:**
```python
manager = JournalManager(capital_initial=5000.0)
```
Confirmado en `server.js` línea 58.

### **Formato de Trades Normalizado:**
Ambos brokers ya devuelven formato común. Ver fixtures arriba.

### **Timezone:**
Todos los datetimes en UTC (ISO 8601 con `+00:00` o `Z`).

### **Balance Real:**
Se obtiene de `schwab_adapter.get_account_balance()` en tiempo real.  
⚠️ Puede estar cacheado en frontend si no se hizo hard refresh.

---

**Este documento contiene TODO lo necesario para que el arquitecto entregue T0.**

**Generado:** 2025-11-08 11:55 UTC  
**Por:** Claude VS Code (Ejecutor)  
**Para:** Claude Perplexity (Arquitecto)
