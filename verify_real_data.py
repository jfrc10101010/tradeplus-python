import sys
sys.path.insert(0, 'c:\\Users\\joser\\TradePlus\\tradeplus-python')

from hub.journal.schwab_adapter import SchwabAdapter

# Obtener datos DIRECTOS de Schwab API (sin ningún cálculo)
adapter = SchwabAdapter()
trades = adapter.get_transactions(days=30)

print(f"Total trades de Schwab API: {len(trades)}\n")

# Análisis manual de BUY vs SELL
buy_total = 0
sell_total = 0
fees_total = 0

for t in trades:
    side = t['side']
    amount = float(t['amount'])
    fee = float(t['fee'])
    
    if side == 'BUY':
        buy_total += amount
    else:  # SELL
        sell_total += amount
    
    fees_total += fee

print("=== ANÁLISIS RAW (sin matching, solo sumas) ===")
print(f"Total COMPRADO (BUY):  ${buy_total:,.2f}")
print(f"Total VENDIDO (SELL):  ${sell_total:,.2f}")
print(f"Total Fees:            ${fees_total:,.2f}")
print(f"Diferencia bruta:      ${sell_total - buy_total:,.2f}")
print(f"Diferencia neta:       ${sell_total - buy_total - fees_total:,.2f}")

print("\n=== BREAKDOWN POR SÍMBOLO ===")
symbols = {}
for t in trades:
    sym = t['symbol']
    if sym not in symbols:
        symbols[sym] = {'buy_qty': 0, 'buy_amount': 0, 'sell_qty': 0, 'sell_amount': 0, 'fees': 0}
    
    qty = float(t['quantity'])
    amount = float(t['amount'])
    fee = float(t['fee'])
    
    if t['side'] == 'BUY':
        symbols[sym]['buy_qty'] += qty
        symbols[sym]['buy_amount'] += amount
    else:
        symbols[sym]['sell_qty'] += qty
        symbols[sym]['sell_amount'] += amount
    
    symbols[sym]['fees'] += fee

for sym, data in sorted(symbols.items()):
    net = data['sell_amount'] - data['buy_amount'] - data['fees']
    print(f"\n{sym}:")
    print(f"  BUY:  {data['buy_qty']:7.2f} shares @ ${data['buy_amount']:10,.2f}")
    print(f"  SELL: {data['sell_qty']:7.2f} shares @ ${data['sell_amount']:10,.2f}")
    print(f"  Fees: ${data['fees']:.2f}")
    print(f"  Net:  ${net:,.2f}")
    
    if data['buy_qty'] > data['sell_qty']:
        print(f"  ⚠️  POSICIÓN ABIERTA: {data['buy_qty'] - data['sell_qty']:.2f} shares")

print("\n" + "="*60)
print("ESTOS SON TUS NÚMEROS REALES DIRECTOS DE SCHWAB API")
print("Sin ningún cálculo, solo sumas brutas")
print("="*60)
