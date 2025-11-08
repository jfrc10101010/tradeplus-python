import json
from datetime import datetime

with open('test_30days_fixed.json', 'r') as f:
    data = json.load(f)

# Filtrar operaciones cerradas
closed_trades = [t for t in data['trades'] if t.get('is_closed', False)]

print("="*100)
print(f"ANÁLISIS COMPLETO DE OPERACIONES CERRADAS - SCHWAB")
print(f"Período: {data['period']['from']} a {data['period']['to']}")
print(f"Total operaciones cerradas según backend: {data['positions']['closed_count']}")
print(f"Total operaciones cerradas encontradas: {len(closed_trades)}")
print("="*100)
print()

# Tabla detallada
print(f"{'#':<4} {'FECHA':<12} {'SÍMBOLO':<8} {'LADO':<6} {'QTY':<8} {'PRECIO':<10} {'P&L USD':<12} {'P&L %':<10} {'COST BASIS':<12}")
print("-"*100)

total_pl_usd = 0
total_cost_basis = 0

for i, trade in enumerate(closed_trades, 1):
    fecha = trade['datetime'][:10]
    symbol = trade['symbol']
    side = trade['side']
    qty = trade['quantity']
    price = trade['price']
    pl_usd = trade['pl_usd']
    pl_pct = trade['pl_percent']
    cost_basis = trade.get('cost_basis', 0)
    
    total_pl_usd += pl_usd
    total_cost_basis += cost_basis
    
    print(f"{i:<4} {fecha:<12} {symbol:<8} {side:<6} {qty:<8.1f} ${price:<9.2f} ${pl_usd:>10.2f} {pl_pct:>8.2f}% ${cost_basis:>10.2f}")

print("-"*100)
print(f"{'TOTALES':<50} ${total_pl_usd:>10.2f} {'':<10} ${total_cost_basis:>10.2f}")
print()

# Calcular P&L % correcto
pl_percent_correcto = (total_pl_usd / total_cost_basis * 100) if total_cost_basis > 0 else 0
print(f"P&L % MANUAL (PL / Cost Basis): {pl_percent_correcto:.2f}%")
print(f"P&L % BACKEND: {data['stats']['pl_realized_percent']:.2f}%")
print()

# Verificar operaciones problemáticas
print("="*100)
print("VERIFICACIÓN DE OPERACIONES SOSPECHOSAS:")
print("="*100)

# Buscar SELL sin BUY previo
for symbol in set([t['symbol'] for t in data['trades']]):
    symbol_trades = [t for t in data['trades'] if t['symbol'] == symbol]
    symbol_trades_sorted = sorted(symbol_trades, key=lambda x: x['datetime'])
    
    buys = [t for t in symbol_trades_sorted if t['side'] == 'BUY']
    sells = [t for t in symbol_trades_sorted if t['side'] == 'SELL']
    
    # Verificar si el primer trade es SELL
    if symbol_trades_sorted and symbol_trades_sorted[0]['side'] == 'SELL':
        print(f"\n⚠️ {symbol}: PRIMER TRADE ES SELL (sin BUY previo)")
        print(f"   Fecha: {symbol_trades_sorted[0]['datetime'][:10]}")
        print(f"   Cantidad: {symbol_trades_sorted[0]['quantity']}")
        print(f"   Precio: ${symbol_trades_sorted[0]['price']:.2f}")
        print(f"   P&L reportado: ${symbol_trades_sorted[0]['pl_usd']:.2f}")
        print(f"   Is closed: {symbol_trades_sorted[0].get('is_closed', False)}")

print()
print("="*100)
print("RESUMEN FINAL:")
print("="*100)
print(f"Backend reporta:")
print(f"  - Operaciones cerradas: {data['positions']['closed_count']}")
print(f"  - P&L Realizado: ${data['stats']['pl_realized_usd']:.2f}")
print(f"  - P&L %: {data['stats']['pl_realized_percent']:.2f}%")
print()
print(f"Cálculo manual:")
print(f"  - Operaciones cerradas: {len(closed_trades)}")
print(f"  - P&L Realizado: ${total_pl_usd:.2f}")
print(f"  - P&L %: {pl_percent_correcto:.2f}%")
print()
print(f"Diferencia P&L USD: ${abs(data['stats']['pl_realized_usd'] - total_pl_usd):.2f}")
