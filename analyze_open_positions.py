import json
import requests

def analyze_open_positions(days, label):
    print("\n" + "="*100)
    print(f"PERÍODO: {label} ({days} días)")
    print("="*100)
    
    # Obtener datos del API
    url = f"http://localhost:8080/api/journal/broker/schwab?days={days}"
    response = requests.get(url)
    data = response.json()
    
    # Posiciones abiertas
    open_positions = data['positions']['open_detail']
    stats = data['stats']
    
    print(f"Total posiciones abiertas: {len(open_positions)}")
    print()
    
    # Tabla detallada
    print(f"{'#':<4} {'SÍMBOLO':<8} {'QTY':<8} {'AVG COST':<11} {'CURRENT':<11} {'COST BASIS':<13} {'CURRENT VAL':<13} {'P&L USD':<12} {'P&L %':<9}")
    print("-"*100)
    
    total_pl_unrealized = 0
    total_cost_basis = 0
    total_current_value = 0
    
    for i, pos in enumerate(open_positions, 1):
        symbol = pos['symbol']
        qty = pos['qty']
        avg_cost = pos['avg_cost']
        current_price = pos['current_price']
        cost_basis = pos['cost_basis']
        current_value = pos['current_value']
        pl_usd = pos['unrealized_pl']
        pl_pct = pos['unrealized_percent']
        
        total_pl_unrealized += pl_usd
        total_cost_basis += cost_basis
        total_current_value += current_value
        
        # Calcular P&L manual para verificar
        pl_manual = current_value - cost_basis
        pl_pct_manual = (pl_manual / cost_basis * 100) if cost_basis > 0 else 0
        
        match = "✅" if abs(pl_usd - pl_manual) < 0.01 else "❌"
        
        color = "📈" if pl_usd >= 0 else "📉"
        print(f"{i:<4} {symbol:<8} {qty:>7.1f} ${avg_cost:>9.2f} ${current_price:>9.2f} ${cost_basis:>11.2f} ${current_value:>11.2f} ${pl_usd:>10.2f} {pl_pct:>7.2f}% {color} {match}")
    
    print("-"*100)
    print(f"{'TOTALES':<21} {'':<11} {'':<11} ${total_cost_basis:>11.2f} ${total_current_value:>11.2f} ${total_pl_unrealized:>10.2f}")
    print()
    
    # Calcular P&L % manual
    pl_pct_manual = (total_pl_unrealized / total_cost_basis * 100) if total_cost_basis > 0 else 0
    
    # Resumen comparativo
    print("RESUMEN:")
    print(f"  Backend:")
    print(f"    - Posiciones abiertas: {data['positions']['open_count']}")
    print(f"    - P&L Unrealized USD: ${stats['pl_unrealized_usd']:.2f}")
    print(f"    - P&L Unrealized %: {stats['pl_unrealized_percent']:.2f}%")
    print()
    print(f"  Manual:")
    print(f"    - Posiciones abiertas: {len(open_positions)}")
    print(f"    - P&L Unrealized USD: ${total_pl_unrealized:.2f}")
    print(f"    - P&L Unrealized %: {pl_pct_manual:.2f}%")
    print(f"    - Total invertido: ${total_cost_basis:.2f}")
    print(f"    - Valor actual: ${total_current_value:.2f}")
    print()
    print(f"  ✅ Match USD: {'SÍ' if abs(stats['pl_unrealized_usd'] - total_pl_unrealized) < 0.01 else 'NO'}")
    print(f"  ✅ Match %: {'SÍ' if abs(stats['pl_unrealized_percent'] - pl_pct_manual) < 0.01 else 'NO'}")
    
    # Desglose por ganadores/perdedores
    print()
    print("DESGLOSE:")
    winners = [p for p in open_positions if p['unrealized_pl'] >= 0]
    losers = [p for p in open_positions if p['unrealized_pl'] < 0]
    
    total_winners_usd = sum([p['unrealized_pl'] for p in winners])
    total_losers_usd = sum([p['unrealized_pl'] for p in losers])
    
    print(f"  📈 Ganadoras: {len(winners)} posiciones → ${total_winners_usd:.2f}")
    for w in winners:
        print(f"     {w['symbol']:6} ${w['unrealized_pl']:>8.2f} ({w['unrealized_percent']:>6.2f}%)")
    
    print()
    print(f"  📉 Perdedoras: {len(losers)} posiciones → ${total_losers_usd:.2f}")
    for l in losers:
        print(f"     {l['symbol']:6} ${l['unrealized_pl']:>8.2f} ({l['unrealized_percent']:>6.2f}%)")
    
    return {
        'label': label,
        'days': days,
        'open_count': len(open_positions),
        'pl_unrealized_usd': total_pl_unrealized,
        'pl_unrealized_percent': pl_pct_manual,
        'cost_basis': total_cost_basis,
        'current_value': total_current_value,
        'winners': len(winners),
        'losers': len(losers)
    }

# Analizar todos los períodos
print("\n" + "🔍 ANÁLISIS DE POSICIONES ABIERTAS - SCHWAB".center(100))
print("="*100)

periods = []
periods.append(analyze_open_positions(7, "7 DÍAS"))
periods.append(analyze_open_positions(30, "30 DÍAS"))
periods.append(analyze_open_positions(90, "90 DÍAS"))
periods.append(analyze_open_positions(365, "1 AÑO"))

# Tabla resumen final
print("\n\n" + "="*100)
print("📊 RESUMEN COMPARATIVO - POSICIONES ABIERTAS")
print("="*100)
print(f"{'PERÍODO':<15} {'POSICIONES':<12} {'P&L USD':<13} {'P&L %':<10} {'GANADORAS':<12} {'PERDEDORAS':<12} {'COST BASIS':<15}")
print("-"*100)

for p in periods:
    print(f"{p['label']:<15} {p['open_count']:<12} ${p['pl_unrealized_usd']:>10.2f} {p['pl_unrealized_percent']:>8.2f}% {p['winners']:<12} {p['losers']:<12} ${p['cost_basis']:>13.2f}")

print("-"*100)
print()
print("NOTAS:")
print("  - P&L Unrealized = (Valor actual - Cost basis)")
print("  - P&L % = (P&L USD / Cost basis) * 100")
print("  - Las posiciones pueden variar entre períodos si entraron en diferentes fechas")
print()
