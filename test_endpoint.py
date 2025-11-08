import requests
import json

print("Probando endpoint: http://localhost:8080/api/journal?days=7")
print("="*60)

try:
    response = requests.get('http://localhost:8080/api/journal?days=7', timeout=30)
    data = response.json()
    
    print(f"\n✅ ENDPOINT FUNCIONANDO")
    print(f"\nCapital Actual: ${data['capital']['current']:,.2f}")
    print(f"Posiciones Abiertas: {data['positions']['open_count']}")
    print(f"Posiciones Cerradas: {data['positions']['closed_count']}")
    print(f"Total Operaciones: {data['stats']['total_ops']}")
    print(f"Win Rate: {data['stats']['win_rate']}%")
    print(f"Wins: {data['stats']['wins']}")
    print(f"Losses: {data['stats']['losses']}")
    print(f"P&L Realizado: ${data['stats']['pl_realized_usd']:+,.2f} ({data['stats']['pl_realized_percent']:+.2f}%)")
    
    print(f"\n✅ LISTO - Puedes abrir http://localhost:8080/journal.html")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nVerifica que el servidor esté corriendo:")
    print("  pm2 list")
