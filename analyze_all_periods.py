import json
import requests

def analyze_period(days, label):
    print("\n" + "="*100)
    print(f"PERÍODO: {label} ({days} días)")
    print("="*100)
    
    # Obtener datos del API
    url = f"http://localhost:8080/api/journal/broker/schwab?days={days}"
    response = requests.get(url)
    data = response.json()
    
    # Filtrar operaciones cerradas
    closed_trades = [t for t in data['trades'] if t.get('is_closed', False)]
    
    # Estadísticas del backend
    stats = data['stats']
    period = data['period']
    
    print(f"Rango de fechas: {period['from']} → {period['to']}")
    print(f"Total trades en período: {period['trades_count']}")
    print()
    
    # Tabla compacta
    print(f"{'#':<4} {'FECHA':<12} {'SÍMBOLO':<8} {'QTY':<7} {'P&L USD':<11} {'P&L %':<9} {'COST BASIS':<12}")
    print("-"*100)
    
    total_pl_usd = 0
    total_cost_basis = 0
    
    for i, trade in enumerate(closed_trades, 1):
        fecha = trade['datetime'][:10]
        symbol = trade['symbol']
        qty = trade['quantity']
        pl_usd = trade['pl_usd']
        pl_pct = trade['pl_percent']
        cost_basis = trade.get('cost_basis', 0)
        
        total_pl_usd += pl_usd
        total_cost_basis += cost_basis
        
        print(f"{i:<4} {fecha:<12} {symbol:<8} {qty:>6.1f} ${pl_usd:>9.2f} {pl_pct:>7.2f}% ${cost_basis:>10.2f}")
    
    print("-"*100)
    print(f"{'TOTALES':<33} ${total_pl_usd:>9.2f} {'':<9} ${total_cost_basis:>10.2f}")
    print()
    
    # Calcular P&L % manual
    pl_percent_manual = (total_pl_usd / total_cost_basis * 100) if total_cost_basis > 0 else 0
    
    # Resumen comparativo
    print("RESUMEN:")
    print(f"  Backend:")
    print(f"    - Operaciones cerradas: {stats['total_ops']}")
    print(f"    - P&L Realizado USD: ${stats['pl_realized_usd']:.2f}")
    print(f"    - P&L Realizado %: {stats['pl_realized_percent']:.2f}%")
    print(f"    - Win Rate: {stats['win_rate']:.2f}%")
    print(f"    - Profit Factor: {stats['profit_factor']:.2f}")
    print()
    print(f"  Manual:")
    print(f"    - Operaciones cerradas: {len(closed_trades)}")
    print(f"    - P&L Realizado USD: ${total_pl_usd:.2f}")
    print(f"    - P&L Realizado %: {pl_percent_manual:.2f}%")
    print(f"    - Promedio por trade: ${total_pl_usd / len(closed_trades):.2f}" if closed_trades else "    - N/A")
    print()
    print(f"  ✅ Match: {'SÍ' if abs(stats['pl_realized_usd'] - total_pl_usd) < 0.01 else 'NO'}")
    print(f"  ✅ Match %: {'SÍ' if abs(stats['pl_realized_percent'] - pl_percent_manual) < 0.01 else 'NO'}")
    
    return {
        'label': label,
        'days': days,
        'closed_ops': len(closed_trades),
        'pl_usd': total_pl_usd,
        'pl_percent': pl_percent_manual,
        'cost_basis': total_cost_basis,
        'win_rate': stats['win_rate'],
        'profit_factor': stats['profit_factor']
    }

# Analizar todos los períodos
print("\n" + "🔍 ANÁLISIS COMPLETO DE TODOS LOS PERÍODOS - SCHWAB".center(100))
print("="*100)

periods = []
periods.append(analyze_period(7, "7 DÍAS"))
periods.append(analyze_period(30, "30 DÍAS"))
periods.append(analyze_period(90, "90 DÍAS"))
periods.append(analyze_period(365, "1 AÑO"))

# Tabla resumen final
print("\n\n" + "="*100)
print("📊 RESUMEN COMPARATIVO DE TODOS LOS PERÍODOS")
print("="*100)
print(f"{'PERÍODO':<15} {'OPS':<8} {'P&L USD':<13} {'P&L %':<10} {'WIN RATE':<11} {'PROFIT FACTOR':<15} {'COST BASIS':<15}")
print("-"*100)

for p in periods:
    print(f"{p['label']:<15} {p['closed_ops']:<8} ${p['pl_usd']:>10.2f} {p['pl_percent']:>8.2f}% {p['win_rate']:>9.2f}% {p['profit_factor']:>13.2f} ${p['cost_basis']:>13.2f}")

print("-"*100)
print()
print("OBSERVACIONES:")
print("  - Win Rate 100% = Solo operaciones ganadoras")
print("  - Profit Factor 999.99 = Sin pérdidas (indicador especial)")
print("  - P&L % = (P&L USD / Cost Basis) * 100")
print()
