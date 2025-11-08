#!/usr/bin/env python3
"""
Debug Schwab Data - Análisis detallado de los números
"""
import sys
sys.path.insert(0, 'c:\\Users\\joser\\TradePlus\\tradeplus-python')

from hub.journal.journal_manager import JournalManager
import json

def main():
    jm = JournalManager(capital_initial=5000.0)
    
    print("=" * 80)
    print("ANÁLISIS DETALLADO: SCHWAB")
    print("=" * 80)
    
    # Obtener trades de Schwab
    from hub.journal.schwab_adapter import SchwabAdapter
    schwab_adapter = SchwabAdapter()
    schwab_trades = schwab_adapter.get_transactions(days=30)
    
    print(f"\nTrades crudos de SchwabAdapter: {len(schwab_trades)}")
    
    # Obtener datos con P&L
    data = jm.get_journal_with_pl(trades=schwab_trades, days=30, broker='schwab')
    
    # Resumen principal
    print("\nRESUMEN GENERAL:")
    print(f"   Total trades cargados: {len(data['trades'])}")
    period = data.get('period', {})
    print(f"   Periodo: {period.get('days', 30)} dias")
    if 'start_date' in period:
        print(f"   Desde: {period['start_date']}")
        print(f"   Hasta: {period['end_date']}")
    
    # Capital
    print("\nCAPITAL:")
    capital = data.get('capital', {})
    print(f"   Inicial: ${capital.get('initial', 5000):,.2f}")
    print(f"   Final: ${capital.get('current', 5000):,.2f}")
    print(f"   P&L USD: ${capital.get('pl_total_usd', 0):,.2f}")
    print(f"   P&L %: {capital.get('pl_total_percent', 0):.2f}%")
    
    # Estadísticas
    stats = data.get('stats', {})
    print("\nESTADISTICAS:")
    print(f"   Total Trades: {stats.get('total_trades', 0)}")
    print(f"   Winners: {stats.get('wins', 0)}")
    print(f"   Losers: {stats.get('losses', 0)}")
    print(f"   Win Rate: {stats.get('win_rate', 0):.2f}%")
    print(f"   Avg P&L: ${stats.get('avg_pl_per_trade', 0):.2f}")
    print(f"   Profit Factor: {stats.get('profit_factor', 0):.2f}")
    print(f"   Total Volume: ${stats.get('total_volume', 0):,.2f}")
    print(f"   Total Fees: ${stats.get('total_fees', 0):.2f}")
    max_gain = stats.get('max_gain', {})
    max_loss = stats.get('max_loss', {})
    print(f"   Max Gain: ${max_gain.get('amount', 0):.2f} ({max_gain.get('symbol', 'N/A')})")
    print(f"   Max Loss: ${max_loss.get('amount', 0):.2f} ({max_loss.get('symbol', 'N/A')})")
    
    # Evolución de capital
    print("\nEVOLUCION DE CAPITAL (ultimos 10 dias):")
    evolution = capital.get('evolution', [])[-10:]
    for day in evolution:
        print(f"   {day['date']} | Trades: {day['trades_count']:2d} | "
              f"Capital start: ${day['capital_start']:,.2f} | "
              f"P&L daily: ${day['pl_daily']:8.2f} | "
              f"Capital end: ${day['capital_end']:,.2f}")
    
    # Top símbolos
    print("\nTOP 10 SIMBOLOS (por P&L absoluto):")
    symbols = data.get('symbols', {})
    sorted_symbols = sorted(symbols.items(), 
                           key=lambda x: abs(x[1]['pl_usd']), 
                           reverse=True)[:10]
    for symbol, sdata in sorted_symbols:
        print(f"   {symbol:8s} | Trades: {sdata['trades']:3d} | "
              f"P&L: ${sdata['pl_usd']:10.2f} | "
              f"Fees: ${sdata['total_fees']:8.2f}")
    
    # Últimos 10 trades
    print("\nULTIMOS 10 TRADES:")
    print("   " + "-" * 140)
    print(f"   {'Fecha':<12} {'Simbolo':<8} {'Lado':<4} {'Cantidad':>10} "
          f"{'Precio':>10} {'Total':>12} {'Fee':>8} {'P&L USD':>10} {'P&L %':>8}")
    print("   " + "-" * 140)
    
    for t in data['trades'][-10:]:
        pl_usd = t.get('pl_usd', 0)
        pl_pct = t.get('pl_percent', 0)
        total = t.get('total', t.get('amount', 0))
        
        print(f"   {t['datetime'][:10]:<12} "
              f"{t['symbol']:<8} "
              f"{t['side']:<4} "
              f"{t['quantity']:>10.2f} "
              f"${t['price']:>9.2f} "
              f"${total:>11.2f} "
              f"${t['fee']:>7.2f} "
              f"${pl_usd:>9.2f} "
              f"{pl_pct:>7.2f}%")
    
    # Verificar datos crudos del primer trade
    print("\nDETALLE DEL PRIMER TRADE (raw data):")
    if data['trades']:
        first = data['trades'][0]
        print(json.dumps(first, indent=2))
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
