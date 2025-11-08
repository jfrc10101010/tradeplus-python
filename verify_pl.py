import json

with open('test_7days.json', 'r') as f:
    data = json.load(f)

closed_trades = [t for t in data['trades'] if t.get('is_closed', False)]
print(f"Total operaciones cerradas: {len(closed_trades)}")
print(f"\nDetalle de P&L por operación:")
print("-" * 60)

total_pl = 0
for i, trade in enumerate(closed_trades, 1):
    pl = trade['pl_usd']
    total_pl += pl
    print(f"{i}. {trade['datetime'][:10]} {trade['symbol']:6} {trade['side']:4} {trade['quantity']:6.1f} @ ${trade['price']:8.2f} -> PL: ${pl:8.2f}")

print("-" * 60)
print(f"TOTAL P&L Realizado (manual): ${total_pl:.2f}")
print(f"TOTAL P&L Realizado (backend): ${data['stats']['pl_realized_usd']:.2f}")
print(f"Diferencia: ${abs(total_pl - data['stats']['pl_realized_usd']):.2f}")

# Verificar el MSFT que tiene is_closed pero pl_usd extraño
msft_trades = [t for t in data['trades'] if t['symbol'] == 'MSFT']
print(f"\n⚠️ Trades de MSFT: {len(msft_trades)}")
for t in msft_trades:
    print(f"  {t['side']:4} {t['quantity']} @ ${t['price']:.2f} - PL: ${t['pl_usd']:.2f} - Closed: {t.get('is_closed', False)}")
