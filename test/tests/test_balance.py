import sys
sys.path.insert(0, 'hub')

from journal.schwab_adapter import SchwabAdapter

schwab = SchwabAdapter()
balance = schwab.get_account_balance()

print(f"✅ Balance obtenido:")
print(f"   Cash: ${balance['cash_balance']:,.2f}")
print(f"   Account Value (Net Liq): ${balance['account_value']:,.2f}")
print(f"   Buying Power: ${balance['buying_power']:,.2f}")
print(f"   Long Market Value: ${balance['long_market_value']:,.2f}")
