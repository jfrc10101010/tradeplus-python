import sys
sys.path.insert(0, 'c:\\Users\\joser\\TradePlus\\tradeplus-python')

from hub.journal.schwab_adapter import SchwabAdapter
import json

adapter = SchwabAdapter()
trades = adapter.get_transactions(days=30)

print(f"Total trades: {len(trades)}\n")
print("Primeros 5 trades:")
for i, t in enumerate(trades[:5]):
    print(f"\n=== TRADE {i+1} ===")
    print(json.dumps(t, indent=2))
