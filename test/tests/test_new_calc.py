import sys
sys.path.insert(0, 'c:\\Users\\joser\\TradePlus\\tradeplus-python')

from hub.journal.schwab_adapter import SchwabAdapter
from hub.journal.journal_manager import JournalManager

# Test nuevo cálculo
adapter = SchwabAdapter()
trades = adapter.get_transactions(days=30)

jm = JournalManager(5000.0)
trades_with_pl, positions = jm.calculate_trades_with_fifo_pl(trades)

print("=" * 80)
print("VERIFICACIÓN DATOS REALES CON NUEVO CÁLCULO")
print("=" * 80)

print(f"\nTotal trades: {len(trades_with_pl)}")
print(f"\nPosiciones cerradas: {positions['closed_count']}")
print(f"Posiciones abiertas: {len(positions['open'])}")
print(f"\nP&L Realizado (cerradas): ${positions['realized_pl']:,.2f}")
print(f"P&L Unrealized (abiertas): ${positions['unrealized_pl']:,.2f}")

print("\n--- POSICIONES ABIERTAS ---")
for pos in positions['open']:
    print(f"{pos['symbol']}: {pos['qty']} shares @ ${pos['avg_cost']:.2f} = ${pos['current_value']:,.2f}")

# Verificar trades cerrados
closed_trades = [t for t in trades_with_pl if t.get('is_closed')]
print(f"\n--- TRADES CERRADOS (sample 5) ---")
for t in closed_trades[:5]:
    print(f"{t['datetime'][:10]} | {t['symbol']:6s} | {t['side']:4s} | P&L: ${t['pl_realized']:8.2f}")

print("\n" + "=" * 80)
print("✅ ESTOS SON TUS NÚMEROS REALES SIN FAKE DATA")
print("=" * 80)
