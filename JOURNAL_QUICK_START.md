# 🚀 GUÍA RÁPIDA - Journal

## ¿Qué se integró?

3 archivos nuevos del Journal:

1. **`hub/journal/journal_manager.py`** - Backend que obtiene trades de ambos brokers
2. **`frontend/journal.html`** - Frontend con interfaz profesional oscura
3. **`hub/hub.py`** - Actualizado con endpoint `/api/journal`

---

## Verificación Rápida

```bash
# Verificar que todo importa correctamente
python test_journal_integration.py

# Output esperado:
# [OK] JournalManager importado correctamente
# [OK] HubCentral inicializado
# [OK] Metodo 'get_journal' disponible
# [OK] Endpoint /api/journal esta en hub.py
```

---

## Endpoint Disponible

```
GET http://localhost:8000/api/journal?broker=schwab&days=7
```

**Parámetros:**
- `broker`: "schwab" o "coinbase"
- `days`: número de días (default 30)

**Response:**
```json
{
  "trades": [...],      // Array de trades normalizados
  "stats": {
    "total_trades": 15,
    "total_volume": 12345.67,
    "total_fees": 45.50,
    "buys": 10,
    "sells": 5
  }
}
```

---

## Información Técnica

### JournalManager

Ubicación: `hub/journal/journal_manager.py`

**Métodos:**
- `async get_journal(broker, days)` - Obtiene trades del broker
- `calculate_stats(trades)` - Calcula estadísticas

**Características:**
- ✅ Soporta Schwab y Coinbase
- ✅ Normaliza a formato común
- ✅ Manejo de errores robusto
- ✅ Logging detallado

### Formato Normalizado

Todos los trades se normalizan a:

```python
{
    "id": "12345",
    "datetime": "2025-11-06T10:30:00Z",
    "symbol": "AAPL",
    "side": "BUY",           # BUY o SELL
    "quantity": 10.0,
    "price": 178.50,
    "fee": 0.50,
    "total": 1785.00,
    "broker": "schwab"       # schwab o coinbase
}
```

### UI Frontend

Ubicación: `frontend/journal.html`

**Características:**
- ✅ Diseño oscuro profesional
- ✅ 2 pestañas (Schwab / Coinbase)
- ✅ Tabla con AG Grid (sorteable, filtrable)
- ✅ Stats cards con totales
- ✅ Formato de moneda automático
- ✅ Colores: BUY (verde), SELL (rojo)

---

## Flujo de Datos

```
HubCentral
    ↓
JournalManager
    ├── Schwab API (/api/journal?broker=schwab)
    │   └── Normaliza transacciones
    │
    └── Coinbase API (/api/journal?broker=coinbase)
        └── Normaliza fills
    
Respuesta JSON
    ↓
Frontend (journal.html)
    └── Renderiza con AG Grid
```

---

## Próximos Pasos

1. **Ejecutar el hub:**
   ```bash
   python hub/main.py
   ```

2. **Probar endpoint:**
   ```bash
   curl "http://localhost:8000/api/journal?broker=schwab&days=7"
   ```

3. **Abrir UI (si existe servidor en 5000):**
   ```
   http://localhost:5000/journal.html
   ```

---

## Troubleshooting

**P: ¿Qué pasa si Coinbase JWT falla?**
R: El JournalManager lo crea automáticamente desde las credenciales.

**P: ¿Qué pasa si Schwab token no existe?**
R: El SchwabTokenManager lo genera automáticamente al iniciar.

**P: ¿Los datos son en tiempo real?**
R: No, es REST (obtiene histórico). Para real-time se podría agregar WebSocket.

**P: ¿Soporta más de 30 días?**
R: Sí, pasar `?days=90` para los últimos 90 días.

---

## Archivos Ubicaciones

```
hub/
  journal/
    __init__.py              ← Módulo
    journal_manager.py       ← Backend
  hub.py                     ← Actualizado con endpoint

frontend/
  journal.html               ← UI

tests/
  test_journal_integration.py ← Tests (opcional)
```

---

**Estado: ✅ LISTO PARA USAR**

Todos los archivos están integrados y validados.
