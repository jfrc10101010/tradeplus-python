# 📊 Journal Dashboard - Especificaciones Técnicas

## 🎯 Información General

**Versión**: 1.0.0  
**Framework**: Tailwind CSS + AG Grid + Chart.js  
**Puerto**: 8080  
**Ruta**: `http://localhost:8080/journal`  
**Fuente de Datos**: API `/api/journal` (Python backend)  

---

## 🎨 Diseño Visual

### Tema Dark Mode Profesional
- **Background Principal**: `linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%)`
- **Cards**: Glass-morphism con `rgba(30, 41, 59, 0.7)` + backdrop blur
- **Borders**: `rgba(51, 65, 85, 0.3)` con efecto hover

### Paleta de Colores

| Uso | Color | Hex | RGB |
|-----|-------|-----|-----|
| **Ganancias/Compras** | Verde | `#10b981` | `16, 185, 129` |
| **Pérdidas/Ventas** | Rojo | `#ef4444` | `239, 68, 68` |
| **Schwab** | Azul | `#3b82f6` | `59, 130, 246` |
| **Coinbase** | Naranja | `#fb923c` | `251, 146, 60` |
| **Neutral** | Gris | `#6b7280` | `107, 116, 128` |
| **Background Dark** | Azul oscuro | `#0f172a` | `15, 23, 42` |
| **Card Background** | Azul medio | `#1e293b` | `30, 41, 59` |
| **Border** | Gris oscuro | `#334155` | `51, 65, 85` |
| **Texto Principal** | Gris claro | `#e2e8f0` | `226, 232, 240` |

---

## 📊 KPIs Principales (Header)

### 4 Métricas Clave

1. **📈 Total Operaciones**
   - Valor: Conteo total de trades
   - Subtítulo: "Últimos 7 días"
   - Icono: 📊

2. **💰 Volumen Total (USD)**
   - Valor: Suma de `amount` de todos los trades
   - Formato: `$XX,XXX.XX`
   - Subtítulo: "Acumulado"
   - Icono: 💵

3. **🎯 Ratio Compra/Venta**
   - Valor: `(Compras / Total) * 100`
   - Formato: `XX.X%`
   - Color: Verde (profit-text)
   - Subtítulo: "BUY vs SELL"
   - Icono: 🏆

4. **💸 Comisiones Totales**
   - Valor: Suma de `fee` de todos los trades
   - Formato: `$XX.XX`
   - Color: Rojo (loss-text)
   - Subtítulo: "Fees acumulados"
   - Icono: 💸

---

## 📑 Tabs de Navegación

### Tab 1: 📊 Overview

**Contenido**:
- **3 Gráficos superiores** (grid 3 columnas):
  1. **🔄 Compras vs Ventas** (Doughnut chart)
     - Verde: Compras
     - Rojo: Ventas
  
  2. **🏢 Por Broker** (Pie chart)
     - Azul: Schwab
     - Naranja: Coinbase
  
  3. **🥇 Top 5 Símbolos** (Lista interactiva)
     - Clickeable para abrir modal
     - Muestra: Symbol, count, volumen, buy/sell split

- **Gráfico inferior**:
  - **📅 Actividad Diaria** (Bar chart dual-axis)
    - Eje Y izquierdo: Operaciones (verde)
    - Eje Y derecho: Volumen USD (azul)
    - Eje X: Fechas

### Tab 2: 📋 Trades

**Contenido**: Tabla AG Grid con TODAS las operaciones

**Columnas**:
| Campo | Ancho | Formato | Funcionalidad |
|-------|-------|---------|---------------|
| Fecha | 180px | `DD/MM/YYYY HH:MM:SS` | Filtrable |
| Broker | 100px | Badge coloreado | Schwab (azul) / Coinbase (naranja) |
| Símbolo | 100px | Bold + hover | Clickeable → Modal |
| Lado | 80px | BUY (verde) / SELL (rojo) | Bold |
| Cantidad | 100px | `X.XXXX` | - |
| Precio | 100px | `$XXX.XX` | - |
| Total | 120px | `$X,XXX.XX` | - |
| Comisión | 100px | `$X.XX` | - |

**Features**:
- Paginación: 20 filas por página
- Ordenamiento: Todas las columnas
- Filtros: Fecha, Broker, Símbolo
- Resize: Columnas redimensionables

### Tab 3: 🎯 Por Símbolo

**Contenido**:

**Sección Superior** (grid 2 columnas):
1. **🥇 Top Símbolos (Volumen)**
   - Lista ordenada por volumen
   - Clickeable para modal
   - Muestra: Symbol, count, volumen

2. **📊 Distribución** (Bar chart horizontal)
   - Top 10 símbolos por volumen
   - Eje Y: Símbolos
   - Eje X: Volumen USD

**Sección Inferior**:
- **Tabla AG Grid**: Análisis detallado

**Columnas**:
| Campo | Descripción | Formato |
|-------|-------------|---------|
| Símbolo | Clickeable → Modal | Bold |
| Ops | Total operaciones | Número |
| Compras | Count de BUY | Verde |
| Ventas | Count de SELL | Rojo |
| Cantidad Total | Suma de quantity | `X.XXXX` |
| Volumen | Suma de amount | `$X,XXX.XX` (verde) |
| Precio Prom. | Volumen / Cantidad | `$XXX.XX` |

### Tab 4: 📈 Analytics

**Sección Superior** (grid 2 columnas):

1. **🕐 Horas Más Activas** (Line chart)
   - Eje X: 0:00 a 23:00
   - Eje Y: Cantidad de operaciones
   - Línea verde con relleno
   - Puntos destacados

2. **💰 Volumen por Hora del Día** (Bar chart)
   - Eje X: 0:00 a 23:00
   - Eje Y: Volumen en USD
   - Barras azules

**Sección Inferior** (grid 3 columnas):

**Estadísticas Generales**:

1. **🏆 Total Compras**
   - Count de trades BUY
   - Subtítulo: Volumen total compras
   - Color: Verde

2. **📉 Total Ventas**
   - Count de trades SELL
   - Subtítulo: Volumen total ventas
   - Color: Rojo

3. **📊 Promedio por Trade**
   - Volumen total / Total operaciones
   - Formato: `$XXX.XX`
   - Subtítulo: "Valor promedio"

---

## 🔍 Modal: Detalle de Símbolo

**Trigger**: Click en símbolo (cualquier tabla)

**Contenido**:

**Header**:
- Nombre del símbolo (grande, bold)
- Botón cerrar (✕)

**KPIs del Símbolo** (grid 2x2):
1. **Operaciones**: Total count
2. **Volumen Total**: USD (verde)
3. **Compras**: Count BUY (verde)
4. **Ventas**: Count SELL (rojo)

**Tabla de Trades**:
- AG Grid con TODOS los trades del símbolo
- Columnas: Fecha, Broker, Lado, Qty, Precio, Total, Fee
- Sorteable por fecha

---

## 📈 Métricas Calculadas

### Por Operación Individual
```javascript
// No calculamos P&L real (requiere entry/exit match)
// Solo mostramos datos directos de la API
amount = trade.amount
fee = trade.fee
quantity = trade.quantity
price = trade.price
```

### Por Símbolo
```javascript
tradesBySymbol[symbol] = {
    count: total_operaciones,
    volume: suma_de_amount,
    buys: count_de_BUY,
    sells: count_de_SELL,
    totalQty: suma_de_quantity,
    avgPrice: volume / totalQty,
    trades: [array_de_trades]
}
```

### Temporales
```javascript
tradesByDate[fecha] = {
    count: operaciones_del_dia,
    volume: suma_amount_del_dia,
    trades: [...]
}

tradesByHour[hora] = {
    count: operaciones_de_la_hora,
    volume: suma_amount_de_la_hora
}
```

### Por Broker
```javascript
brokerSplit = {
    schwab: count_schwab,
    coinbase: count_coinbase
}

brokerVolume = {
    schwab: suma_amount_schwab,
    coinbase: suma_amount_coinbase
}
```

### Agregados
```javascript
totalTrades = trades.length
buys = count(side === 'BUY')
sells = count(side === 'SELL')
totalVolume = sum(amount)
totalFees = sum(fee)
avgPerTrade = totalVolume / totalTrades
```

---

## 🎮 Interactividad

### Eventos de Usuario

| Acción | Comportamiento |
|--------|----------------|
| **Click en Símbolo** | Abre modal con detalles del símbolo |
| **Click en Tab** | Cambia vista + re-renderiza grids |
| **Hover en Chart** | Muestra tooltip con valores |
| **Botón Actualizar** | Llama `refreshDashboard()` → fetch API |
| **Filtro en Grid** | AG Grid built-in filtering |
| **Sort en Grid** | AG Grid built-in sorting |
| **Resize columna** | AG Grid built-in resize |

### Auto-refresh
```javascript
// Carga inicial al abrir página
loadDashboardData();

// Actualización automática cada 30 segundos
setInterval(loadDashboardData, 30000);
```

---

## 📦 Consumo de Datos

### Endpoint API
```
GET /api/journal
```

### Estructura de Respuesta
```json
{
  "timestamp": "2025-11-07T12:00:00.000Z",
  "trades": [
    {
      "id": "106403717567",
      "datetime": "2025-11-06T18:38:29+00:00",
      "symbol": "ORCL",
      "side": "SELL",
      "quantity": 3,
      "price": 245.42,
      "fee": 0,
      "amount": 736.26,
      "status": "VALID",
      "broker": "schwab"
    }
  ],
  "stats": {
    "total_trades": 62,
    "total_volume": 46416.28,
    "total_fees": 2.98,
    "buys": 37,
    "sells": 25,
    "by_broker": {
      "schwab": {
        "trades": 61,
        "volume": 45919.28,
        "fees": 0
      },
      "coinbase": {
        "trades": 1,
        "volume": 497,
        "fees": 2.98
      }
    }
  }
}
```

### Campos Requeridos por Trade
- `id`: String único
- `datetime`: ISO 8601 timestamp
- `symbol`: String (ticker)
- `side`: "BUY" | "SELL"
- `quantity`: Number
- `price`: Number (USD)
- `amount`: Number (USD total)
- `fee`: Number (USD comisión)
- `broker`: "schwab" | "coinbase"

---

## 🛠️ Tecnologías Utilizadas

### Frontend
- **Tailwind CSS 3.x**: Framework CSS utility-first
- **AG Grid Community 31.0.0**: Tablas profesionales
- **Chart.js 4.4.0**: Gráficos interactivos
- **Vanilla JavaScript**: Sin frameworks adicionales

### Backend (Python)
- **Express.js 4.18.2**: Servidor Node.js
- **Python 3.11.9**: Backend con adapters
- **PM2**: Process manager

### CDN Dependencies
```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- AG Grid -->
<script src="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/ag-grid-community.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/styles/ag-grid.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community@31.0.0/dist/styles/ag-theme-quartz-dark.css">

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
```

---

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 768px
  - Stack de 1 columna
  - KPIs en columna simple
  - Gráficos 100% width
  
- **Tablet**: 768px - 1024px
  - Grid 2 columnas para KPIs
  - Gráficos en 2 columnas
  
- **Desktop**: > 1024px
  - Grid 4 columnas para KPIs
  - Gráficos en 3 columnas
  - Tablas full width

---

## 🚀 Instalación y Uso

### Prerrequisitos
```bash
# Node.js + PM2 instalados
npm install -g pm2

# Dependencias del proyecto
cd test/
npm install
```

### Iniciar Servidor
```bash
# Con PM2
pm2 start ecosystem-journal.config.js

# O manualmente
cd test/
node server.js
```

### Acceso
```
http://localhost:8080/journal
```

### Verificar API
```bash
curl http://localhost:8080/api/journal
```

---

## 🐛 Troubleshooting

### Dashboard no carga
```javascript
// Verificar en consola del navegador:
// 1. Error de red → Verificar que server está corriendo
// 2. Error 404 → Verificar ruta /journal en server.js
// 3. Error de CORS → No debería ocurrir (mismo origen)
```

### Gráficos no se muestran
```javascript
// Verificar en consola:
// 1. Error Chart.js → Verificar CDN cargado
// 2. Canvas no encontrado → Verificar IDs en HTML
// 3. Datos vacíos → Verificar API /api/journal
```

### Grids vacías
```javascript
// Verificar en consola:
// 1. Error AG Grid → Verificar CDN cargado
// 2. rowData undefined → Verificar processTradeData()
// 3. Grid no inicializado → Verificar createGrid()
```

---

## 📝 Mantenimiento

### Agregar Nueva Métrica
1. Calcular en `processTradeData()`
2. Agregar card en HTML
3. Actualizar en `updateKPIs()`

### Agregar Nuevo Gráfico
1. Agregar canvas en HTML con ID único
2. Crear config en `updateCharts()`
3. Llamar `updateChart(canvasId, config)`

### Agregar Nueva Columna en Grid
1. Agregar en `columnDefs` del grid
2. Asegurar que el dato existe en `rowData`
3. Opcional: Agregar `cellRenderer` personalizado

---

## 📄 Licencia

Parte del proyecto TRADEPLUS V5.0  
Uso interno - Multi-Broker Trading Journal  
© 2025
