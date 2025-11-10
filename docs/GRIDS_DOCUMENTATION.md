# 📊 Documentación de Grids del Journal - TradePlus

## 📋 Resumen

Este documento explica cómo funcionan los grids (tablas) del journal de TradePlus, sus características, estructura y comportamiento actual.

## 🎯 Objetivo

Los grids muestran información detallada de trades con todas las columnas disponibles, ordenados cronológicamente de más reciente a más antiguo.

## 📊 Tipos de Grids

### 1. 📊 Top por P&L USD (mejor → peor)
**Función:** `renderTopPLGrid()`
- **Ubicación:** Línea ~2278
- **Propósito:** Mostrar todos los trades ordenados por fecha (más nuevo primero)
- **Columnas:** Todas las columnas disponibles
- **Ordenamiento:** Por fecha descendente
- **Características:** Muestra trades individuales con información completa

### 2. 📈 Top por Cantidad de Operaciones
**Función:** `renderTopOpsGrid()`
- **Ubicación:** Línea ~2445
- **Propósito:** Mostrar todos los trades con contador de operaciones por símbolo
- **Columnas:** Todas las columnas + columna adicional "# Trades Símbolo"
- **Ordenamiento:** Por fecha descendente
- **Características:** Incluye `symbol_trade_count` con cantidad acumulada de trades por símbolo

### 3. Historial por Fecha
**Función:** `renderDatesGrid()`
- **Ubicación:** Línea ~2615
- **Propósito:** Mostrar todos los trades ordenados por fecha
- **Columnas:** Todas las columnas disponibles
- **Ordenamiento:** Por fecha descendente
- **Características:** Vista cronológica completa de todos los trades

### 4. 📊 Historial por Símbolo
**Función:** `renderSymbolsGrid()`
- **Ubicación:** Línea ~2802
- **Propósito:** Mostrar todos los trades con contador de operaciones por símbolo
- **Columnas:** Todas las columnas + columna adicional "# Trades Símbolo"
- **Ordenamiento:** Por fecha descendente
- **Características:** Incluye `symbol_trade_count` con cantidad acumulada de trades por símbolo

### 5. 📋 Detalle de Trades (Grid Principal)
**Función:** Renderizado principal
- **Ubicación:** Línea ~1834
- **Propósito:** Mostrar el detalle completo de todos los trades
- **Columnas:** Columnas completas estándar
- **Ordenamiento:** Por fecha descendente
- **Características:** Grid principal con toda la información

## 📋 Estructura de Columnas

### Columnas Estándar (Todas las grids):
1. **Broker** (solo cuando broker === 'all')
   - Ancho: 100px
   - Etiquetas coloridas: azul para Schwab, naranja para Coinbase

2. **Fecha**
   - Campo: `datetime`
   - Ancho: 160px
   - Formato: "Mié 11/06, 14:30"
   - Incluye día de la semana

3. **Símbolo**
   - Campo: `symbol`
   - Ancho: 110px
   - Estilo: texto verde en negrita

4. **Lado**
   - Campo: `side`
   - Ancho: 100px
   - Iconos: 📈 para BUY, 📉 para SELL
   - Colores: verde para BUY, rojo para SELL

5. **Cantidad**
   - Campo: `quantity`
   - Ancho: 120px
   - Tipo: numérica
   - Decimales: 8 para Coinbase, 2 para Schwab

6. **Precio**
   - Campo: `price`
   - Ancho: 110px
   - Tipo: numérica
   - Formato: USD con 2 decimales

7. **Total**
   - Campo: `total` o `amount`
   - Ancho: 110px
   - Tipo: numérica
   - Formato: USD con 2 decimales

8. **Fee**
   - Campo: `fee`
   - Ancho: 90px
   - Tipo: numérica
   - Formato: USD con 2 decimales

9. **P&L USD**
   - Campo: `pl_usd`
   - Ancho: 120px
   - Tipo: numérica
   - Colores: verde para ganancias, rojo para pérdidas
   - Formato: USD con signo (+$1,234.56)

10. **P&L %**
    - Campo: `pl_percent`
    - Ancho: 110px
    - Tipo: numérica
    - Colores: verde para ganancias, rojo para pérdidas
    - Formato: porcentaje con signo (+12.34%)

### Columna Adicional (Grids específicos):
11. **# Trades Símbolo** (solo Top Ops e Historial por Símbolo)
    - Campo: `symbol_trade_count`
    - Ancho: 130px
    - Tipo: numérica
    - Estilo: texto azul en negrita
    - Formato: "X ops" (ejemplo: "5 ops")

## ⚙️ Características Técnicas

### Paginación
- 20 filas por página (configurable: 10, 20, 50)
- Selector de tamaño de página disponible

### Funcionalidades
- **Ordenamiento:** Click en encabezados para ordenar
- **Filtros:** Cajas de filtro en cada columna
- **Selección:** Single row selection
- **Responsive:** Se adapta al tamaño de pantalla
- **Animaciones:** Transiciones suaves al interactuar

### Estilos
- Tema: `ag-theme-alpine-dark`
- Colores de ganancias: verde (#10b981)
- Colores de pérdidas: rojo (#ef4444)
- Fondo: gradiente oscuro profesional

## 🔄 Flujo de Datos

1. **Carga:** Los trades se cargan desde la API o datos locales
2. **Filtrado:** Se filtran trades cerrados (`is_closed: true`)
3. **Ordenamiento:** Se ordenan por fecha descendente
4. **Procesamiento:** Se calculan campos adicionales como `symbol_trade_count`
5. **Renderizado:** Se muestran en el grid con todas las columnas

## 📝 Notas Importantes

- Todos los grids ahora muestran **trades individuales** en lugar de resúmenes agrupados
- El ordenamiento es **cronológico inverso** (más reciente primero)
- Las columnas son **consistentes** en todos los grids
- La funcionalidad de "click para ver detalles" fue removida ya que ahora se muestra todo el detalle

## 🚀 Próximos Pasos

El proyecto está en fase de "grids completos por pulir sin tops aún". Los próximos pasos podrían incluir:

1. **Optimización de rendimiento** para grandes volúmenes de datos
2. **Mejoras visuales** y de experiencia de usuario
3. **Nuevas funcionalidades** de análisis y filtrado
4. **Integración** con más brokers y fuentes de datos

## 📁 Ubicación de Archivos

- **Journal principal:** `/test/public/journal.html`
- **Documentación:** `/docs/GRIDS_DOCUMENTATION.md`
- **Tests:** `/test/`
- **Documentos del proyecto:** `/docs/`