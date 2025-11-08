import requests
import json

print("Diagnosticando problema en journal...")
print("="*70)

try:
    response = requests.get('http://localhost:8080/api/journal?days=30', timeout=30)
    data = response.json()
    
    print(f"\n📊 DATOS DEL API (30 días):")
    print(f"  Total trades: {data['period']['trades_count']}")
    print(f"  Abiertas: {data['positions']['open_count']}")
    print(f"  Cerradas: {data['positions']['closed_count']}")
    print(f"  Total Ops: {data['stats']['total_ops']}")
    
    print(f"\n💰 CAPITAL:")
    print(f"  Current: ${data['capital']['current']}")
    print(f"  P&L Total: ${data['capital']['pl_total_usd']}")
    
    print(f"\n🎯 STATS:")
    print(f"  Wins: {data['stats']['wins']}")
    print(f"  Losses: {data['stats']['losses']}")
    print(f"  Win Rate: {data['stats']['win_rate']}%")
    print(f"  Profit Factor: {data['stats']['profit_factor']}")
    print(f"  P&L Realizado: ${data['stats']['pl_realized_usd']}")
    print(f"  P&L %: {data['stats']['pl_realized_percent']}%")
    print(f"  P&L Unrealized: ${data['stats']['pl_unrealized_usd']}")
    
    print(f"\n📋 POSICIONES ABIERTAS:")
    for pos in data['positions']['open_detail'][:5]:
        print(f"  {pos['symbol']:10s} | {pos['qty']:8.2f} | ${pos['cost_basis']:10.2f}")
    
    print(f"\n📋 TRADES (primeros 5):")
    for trade in data['trades'][:5]:
        print(f"  {trade['datetime'][:10]} | {trade['symbol']:8s} | {trade['side']:4s} | {trade.get('pl_usd', 0):+8.2f}")
    
    # Guardar JSON completo para análisis
    with open('debug_api_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ JSON guardado en debug_api_response.json")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
