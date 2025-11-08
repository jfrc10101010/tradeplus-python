"""
Debug win rate calculation - Mostrar TODOS los datos del cálculo
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hub.journal.journal_manager import JournalManager
import json

def main():
    jm = JournalManager(capital_initial=5000.0)
    
    print("=" * 80)
    print("DEBUG WIN RATE - DATOS REALES")
    print("=" * 80)
    
    # Probar con diferentes períodos
    for days in [7, 30]:
        print(f"\n{'=' * 80}")
        print(f"PERIODO: {days} DIAS")
        print(f"{'=' * 80}\n")
        
        result = jm.compute_metrics(days=days)
        
        if result.get('error'):
            print(f"ERROR: {result['error']}")
            continue
        
        # Extraer datos
        period = result['period']
        positions = result['positions']
        stats = result['stats']
        trades = result['trades']
        
        print(f"📅 RANGO: {period['from']} → {period['to']}")
        print(f"📊 TRADES TOTALES: {period['trades_count']}")
        print(f"📦 OPERACIONES ABIERTAS: {positions['open_count']}")
        print(f"✅ OPERACIONES CERRADAS: {positions['closed_count']}")
        print(f"🎯 TOTAL OPERACIONES: {stats['total_ops']}")
        
        print(f"\n{'─' * 80}")
        print("MÉTRICAS CALCULADAS:")
        print(f"{'─' * 80}")
        print(f"  Wins: {stats['wins']}")
        print(f"  Losses: {stats['losses']}")
        print(f"  Win Rate: {stats['win_rate']}%")
        print(f"  Profit Factor: {stats['profit_factor']}")
        print(f"  P&L Realizado: ${stats['pl_realized_usd']:,.2f} ({stats['pl_realized_percent']:+.2f}%)")
        print(f"  P&L No Realizado: ${stats['pl_unrealized_usd']:,.2f}")
        
        # DETALLAR CADA OPERACIÓN CERRADA
        closed_trades = [t for t in trades if t.get('is_closed')]
        
        if closed_trades:
            print(f"\n{'─' * 80}")
            print(f"DETALLE DE {len(closed_trades)} OPERACIONES CERRADAS:")
            print(f"{'─' * 80}")
            print(f"{'Símbolo':<10} {'Qty':>8} {'Compra':>10} {'Venta':>10} {'P&L $':>12} {'%':>8} {'Resultado':>10}")
            print(f"{'─' * 80}")
            
            wins = 0
            losses = 0
            
            for t in closed_trades:
                symbol = t['symbol']
                qty = t['quantity']
                buy_price = t.get('buy_price', 0)
                sell_price = t.get('price', 0)
                pl_usd = t.get('pl_usd', 0)
                pl_pct = t.get('pl_percent', 0)
                
                resultado = "WIN ✅" if pl_usd > 0 else "LOSS ❌"
                if pl_usd > 0:
                    wins += 1
                else:
                    losses += 1
                
                print(f"{symbol:<10} {qty:>8.4f} ${buy_price:>9.2f} ${sell_price:>9.2f} ${pl_usd:>11.2f} {pl_pct:>7.2f}% {resultado:>10}")
            
            print(f"{'─' * 80}")
            print(f"TOTALES: Wins={wins}, Losses={losses}, Win Rate={wins/(wins+losses)*100:.2f}%")
            print(f"{'─' * 80}")
        
        # DETALLAR POSICIONES ABIERTAS
        open_positions = positions.get('open_detail', [])
        
        if open_positions:
            print(f"\n{'─' * 80}")
            print(f"DETALLE DE {len(open_positions)} POSICIONES ABIERTAS:")
            print(f"{'─' * 80}")
            print(f"{'Símbolo':<10} {'Qty':>10} {'Precio':>12} {'Actual':>12} {'P&L $':>12} {'%':>8}")
            print(f"{'─' * 80}")
            
            for pos in open_positions:
                symbol = pos['symbol']
                qty = pos['quantity']
                avg_price = pos['avg_buy_price']
                current_price = pos.get('current_price', avg_price)
                unrealized_pl = pos.get('unrealized_pl', 0)
                pl_pct = (unrealized_pl / (qty * avg_price) * 100) if (qty * avg_price) > 0 else 0
                
                print(f"{symbol:<10} {qty:>10.4f} ${avg_price:>11.2f} ${current_price:>11.2f} ${unrealized_pl:>11.2f} {pl_pct:>7.2f}%")
            
            print(f"{'─' * 80}")
        
        print("\n")

if __name__ == '__main__':
    main()
