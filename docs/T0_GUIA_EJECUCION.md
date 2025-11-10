# 🚀 T0: GUÍA DE EJECUCIÓN Y VALIDACIÓN

**Fecha:** 2025-11-08  
**Versión:** T0 - Journal Manager Refactor  
**Objetivo:** Validar agrupación FIFO, métricas correctas, endpoint compatible

---

## 📦 ARCHIVOS ENTREGADOS

### 1️⃣ **Código Refactorizado**
```
hub/journal/journal_manager_t0.py
```
**Nueva función core:** `compute_metrics(trades, days, current_prices)`
- Agrupación por símbolo con FIFO
- Abiertas/cerradas separadas
- Win rate solo operaciones cerradas
- Profit factor implementado
- P&L realizado USD + porcentaje
- P&L no realizado con precios actuales

### 2️⃣ **Scripts de Validación**
```
test/verify_positions.py  - Valida conteo de operaciones
test/verify_metrics.py    - Valida cálculos de métricas
```

### 3️⃣ **Configuración**
```
test/public/journal.html  - REFRESH_MS=5000 configurado
```

### 4️⃣ **Fixtures de Test**
```
test/fixtures/schwab_sample.json   - 8 trades Schwab
test/fixtures/coinbase_sample.json - 1 fill Coinbase
```

---

## ✅ PASO 1: EJECUTAR TESTS DE VALIDACIÓN

### Test 1: Verificar Posiciones
```powershell
cd c:\Users\joser\TradePlus\tradeplus-python
python test\verify_positions.py
```

**Debe mostrar:**
```
✅ open_count correcto: 5
✅ closed_count correcto: 1
✅ total_ops correcto: 6
✅ HOOD tiene 2 entradas (correcto)
✅ NU tiene 2 entradas (correcto)
✅ TODOS LOS TESTS PASARON
```

**Si FALLA:** Revisar fixtures en `test/fixtures/`

---

### Test 2: Verificar Métricas
```powershell
python test\verify_metrics.py
```

**Debe mostrar:**
```
✅ Wins correcto: 1
✅ Losses correcto: 0
✅ Win Rate correcto: 100.0%
✅ P&L USD correcto: $16.50
✅ P&L % correcto: 2.32%
✅ TODOS LOS TESTS PASARON
```

**Si FALLA:** Revisar cálculos FIFO en `journal_manager_t0.py`

---

## ✅ PASO 2: INTEGRAR CON SISTEMA ACTUAL

### Opción A: Reemplazar archivo actual (RECOMENDADO PARA PRODUCCIÓN)

```powershell
# Backup del original
Copy-Item hub\journal\journal_manager.py hub\journal\journal_manager_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').py

# Reemplazar con T0
Copy-Item hub\journal\journal_manager_t0.py hub\journal\journal_manager.py
```

### Opción B: Test con módulo temporal (PARA VALIDACIÓN)

Modificar `test/server.js` línea 58:
```javascript
// ANTES:
from journal.journal_manager import JournalManager

// DESPUÉS (temporal para test):
from journal.journal_manager_t0 import JournalManager
```

---

## ✅ PASO 3: REINICIAR SERVIDOR

```powershell
# Reiniciar PM2
pm2 restart journal-test

# O si no usa PM2:
# Ctrl+C en terminal del servidor
# node test/server.js
```

---

## ✅ PASO 4: PROBAR ENDPOINT API

### Test 1: Journal Combinado
```powershell
# PowerShell
$response = Invoke-RestMethod -Uri "http://localhost:8080/api/journal?days=7" -Method Get
$response | ConvertTo-Json -Depth 10
```

**Validar estructura:**
```json
{
  "timestamp": "...",
  "period": {
    "days": 7,
    "from": "2025-11-03",
    "to": "2025-11-07"
  },
  "capital": {
    "initial": 5000.0,
    "current": 5807.16,
    "pl_total_usd": 807.16,
    "pl_total_percent": 16.14
  },
  "positions": {
    "open_count": 5,
    "closed_count": 1,
    "open_detail": [...]
  },
  "stats": {
    "total_ops": 6,
    "wins": 1,
    "losses": 0,
    "win_rate": 100.0,
    "profit_factor": 0.0,
    "pl_realized_usd": 16.50,
    "pl_realized_percent": 2.32,
    "pl_unrealized_usd": 0.0,
    "avg_pl_per_trade": 16.50
  },
  "trades": [...]
}
```

---

### Test 2: Broker Específico (Schwab)
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/journal/broker/schwab?days=7" | ConvertTo-Json -Depth 5
```

---

### Test 3: Broker Específico (Coinbase)
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/journal/broker/coinbase?days=7" | ConvertTo-Json -Depth 5
```

---

## ✅ PASO 5: VALIDAR FRONTEND

### Abrir Dashboard
```
http://localhost:8080/journal.html
```

### Verificar Métricas

1. **Capital Actual:**
   - Debe mostrar balance real de Schwab API
   - NO debe mostrar $5,000 hardcoded

2. **Posiciones del Período:**
   - **Abiertas:** 5 (HOOD, NU, NVDA, COIN, BTC-USD)
   - **Cerradas:** 1 (AMD)
   - **Total:** 6 operaciones

3. **Win Rate:**
   - Debe mostrar: `100.00%`
   - Detalle: `1 Wins / 0 Losses`

4. **Profit Factor:**
   - Debe mostrar: `0.00` (sin losses)

5. **P&L Realizado:**
   - Debe mostrar: `$16.50 USD | 2.32%`

6. **Auto-Refresh:**
   - Observar consola del navegador (F12)
   - Debe refrescar cada 5 segundos
   - Verificar: `console.log("Refreshing at 5s interval")`

---

## ✅ PASO 6: PROBAR FILTROS DE PERÍODO

### Cambiar de 7d → 30d
1. Click en botón "30 días"
2. Verificar que:
   - NO tarda 15 segundos
   - Se actualiza rápidamente
   - Métricas se recalculan correctamente

### Cambiar de 30d → 90d
- Misma verificación

### Cambiar a "All"
- Debe incluir todos los trades sin filtro

---

## 🐛 TROUBLESHOOTING

### Error: "Module 'journal_manager_t0' not found"
```powershell
# Verificar que existe:
Test-Path hub\journal\journal_manager_t0.py

# Verificar imports en server.js
```

### Error: "Fixtures not found"
```powershell
# Verificar fixtures:
Test-Path test\fixtures\schwab_sample.json
Test-Path test\fixtures\coinbase_sample.json

# Re-generar si faltan:
python generate_fixtures.py
```

### Error: "API returns 500"
```powershell
# Ver logs del servidor:
pm2 logs journal-test

# O en terminal del servidor buscar stack trace
```

### Frontend no actualiza
```powershell
# Hard refresh en navegador:
# Ctrl + Shift + R (Chrome/Edge)
# Ctrl + F5 (Firefox)

# Limpiar cache:
# F12 → Network → Disable cache
```

---

## 📊 MÉTRICAS ESPERADAS (Fixtures T0)

### Posiciones Abiertas (5)
```
HOOD:    15.00 shares | $535.10 | 2 entradas
NU:       2.00 shares | $30.55  | 2 entradas
NVDA:     2.00 shares | $1441.00 | 1 entrada
COIN:     3.00 shares | $737.25  | 1 entrada
BTC-USD:  0.00492942  | $497.00  | 1 entrada
```

### Posiciones Cerradas (1)
```
AMD: 5 shares @ $142.50 → $145.80 | P&L: +$16.50 (+2.32%)
```

### Estadísticas
```
Total Ops:         6
Wins:              1
Losses:            0
Win Rate:          100.0%
Profit Factor:     0.0 (sin losses)
P&L Realizado:     $16.50 (2.32%)
P&L No Realizado:  $0.00 (sin precios actuales)
```

---

## ✅ CHECKLIST FINAL DE APROBACIÓN

- [ ] `verify_positions.py` pasa todos los tests
- [ ] `verify_metrics.py` pasa todos los tests
- [ ] Endpoint `/api/journal?days=7` retorna estructura correcta
- [ ] Endpoint `/api/journal/broker/schwab` funciona
- [ ] Endpoint `/api/journal/broker/coinbase` funciona
- [ ] Frontend muestra balance real (no $5,000)
- [ ] Posiciones: 5 abiertas, 1 cerrada, 6 total
- [ ] Win rate: 100% (1W/0L)
- [ ] P&L realizado: $16.50 (2.32%)
- [ ] Auto-refresh cada 5 segundos funciona
- [ ] Filtros de período responden rápido
- [ ] No hay errores en consola del navegador
- [ ] No hay errores en logs del servidor

---

## 🚀 SIGUIENTES PASOS (POST-T0)

1. **Si todo funciona:** Aprobar y mergear a `journal_manager.py`
2. **Implementar cache backend** (Fase 2) para mejorar performance de filtros
3. **WebSocket con FastAPI** (Fase 3) para tiempo real verdadero
4. **Coinbase decimales** (Fase 4) con `quote_increment`
5. **Órdenes multi-broker** (Fase 5) con adaptadores específicos

---

## 📞 REPORTE DE RESULTADOS

**Después de ejecutar todos los pasos, reportar:**

```
✅ PASO 1: verify_positions.py → [PASS/FAIL]
✅ PASO 2: verify_metrics.py → [PASS/FAIL]
✅ PASO 3: Servidor reiniciado → [OK/ERROR]
✅ PASO 4: Endpoint /api/journal → [OK/ERROR]
✅ PASO 5: Frontend journal.html → [OK/ERROR]
✅ PASO 6: Filtros de período → [RÁPIDO/LENTO]

ISSUES DETECTADOS:
- [Listar cualquier error o comportamiento inesperado]

SCREENSHOTS:
- [Adjuntar capturas del dashboard con nuevas métricas]
```

---

**Guía generada:** 2025-11-08  
**T0 Delivery:** Journal Manager con FIFO correcto  
**Tiempo estimado de ejecución:** 15-20 minutos
