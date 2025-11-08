"""
Debug win rate - Llamar al API REST directamente
"""
import requests
import json

def main():
    base_url = 'http://localhost:8080/api/journal'
    
    print("=" * 80)
    print("DEBUG WIN RATE - API REST REAL")
    print("=" * 80)
    
    for days in [7, 30]:
        print(f"\n{'=' * 80}")
        print(f"PERIODO: {days} DIAS")
        print(f"{'=' * 80}\n")
        
        # Llamar al API
        url = f"{base_url}/all/{days}"
        print(f"Llamando: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"ERROR al llamar API: {e}")
            continue
        
        if data.get('error'):
            print(f"ERROR del backend: {data['error']}")
            continue
        
        # Extraer datos
        period = data.get('period', {})
        positions = data.get('positions', {})
        stats = data.get('stats', {})
        trades = data.get('trades', [])
        
        print(f"📅 RANGO: {period.get('from')} → {period.get('to')}")
        print(f"📊 TRADES TOTALES: {period.get('trades_count', 0)}")
        print(f"📦 OPERACIONES ABIERTAS: {positions.get('open_count', 0)}")
        print(f"✅ OPERACIONES CERRADAS: {positions.get('closed_count', 0)}")
        print(f"🎯 TOTAL OPERACIONES: {stats.get('total_ops', 0)}")
        
        print(f"\n{'─' * 80}")
        print("MÉTRICAS CALCULADAS:")
        print(f"{'─' * 80}")
        print(f"  Wins: {stats.get('wins', 0)}")
        print(f"  Losses: {stats.get('losses', 0)}")
        print(f"  Win Rate: {stats.get('win_rate', 0):.2f}%")
        print(f"  Profit Factor: {stats.get('profit_factor', 0):.2f}")
        print(f"  P&L Realizado: ${stats.get('pl_realized_usd', 0):,.2f} ({stats.get('pl_realized_percent', 0):+.2f}%)")
        print(f"  P&L No Realizado: ${stats.get('pl_unrealized_usd', 0):,.2f}")
        
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
                symbol = t.get('symbol', 'N/A')
                qty = t.get('quantity', 0)
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
            win_rate_calc = wins/(wins+losses)*100 if (wins+losses) > 0 else 0
            print(f"VERIFICACIÓN: Wins={wins}, Losses={losses}, Win Rate={win_rate_calc:.2f}%")
            print(f"API devuelve: Wins={stats.get('wins')}, Losses={stats.get('losses')}, Win Rate={stats.get('win_rate')}%")
            
            if wins != stats.get('wins') or losses != stats.get('losses'):
                print("⚠️  INCONSISTENCIA DETECTADA!")
            else:
                print("✅ Cálculo correcto")
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
                symbol = pos.get('symbol', 'N/A')
                qty = pos.get('quantity', 0)
                avg_price = pos.get('avg_buy_price', 0)
                current_price = pos.get('current_price', avg_price)
                unrealized_pl = pos.get('unrealized_pl', 0)
                pl_pct = (unrealized_pl / (qty * avg_price) * 100) if (qty * avg_price) > 0 else 0
                
                print(f"{symbol:<10} {qty:>10.4f} ${avg_price:>11.2f} ${current_price:>11.2f} ${unrealized_pl:>11.2f} {pl_pct:>7.2f}%")
            
            print(f"{'─' * 80}")
        
        print("\n")

if __name__ == '__main__':
    main()
