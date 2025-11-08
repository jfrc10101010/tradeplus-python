"""
TEST REAL: Validación con datos de API en vivo
Sin fixtures, directamente de Schwab + Coinbase
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from journal.journal_manager_t0 import JournalManager

def test_real_data_7_days():
    """Prueba con datos reales de últimos 7 días"""
    print("\n" + "="*70)
    print("TEST REAL: Últimos 7 días - Datos de API en vivo")
    print("="*70)
    
    manager = JournalManager(capital_initial=5000.0)
    result = manager.get_combined_journal(days=7)
    
    print(f"\n📊 PERÍODO:")
    print(f"  Días: {result['period']['days']}")
    print(f"  Desde: {result['period']['from']}")
    print(f"  Hasta: {result['period']['to']}")
    print(f"  Total trades: {result['period']['trades_count']}")
    
    print(f"\n💰 CAPITAL:")
    print(f"  Inicial: ${result['capital']['initial']:,.2f}")
    print(f"  Actual: ${result['capital']['current']:,.2f}")
    print(f"  P&L Total: ${result['capital']['pl_total_usd']:+,.2f} ({result['capital']['pl_total_percent']:+.2f}%)")
    
    print(f"\n📈 POSICIONES:")
    print(f"  Abiertas: {result['positions']['open_count']}")
    print(f"  Cerradas: {result['positions']['closed_count']}")
    print(f"  Total Ops: {result['stats']['total_ops']}")
    
    print(f"\n📋 DETALLE ABIERTAS:")
    for pos in result['positions']['open_detail']:
        print(f"  {pos['symbol']:10s} | {pos['qty']:10.6f} shares | ${pos['cost_basis']:10.2f} | {pos['entries']} entrada(s)")
    
    print(f"\n🎯 MÉTRICAS:")
    print(f"  Wins: {result['stats']['wins']}")
    print(f"  Losses: {result['stats']['losses']}")
    print(f"  Win Rate: {result['stats']['win_rate']:.2f}%")
    print(f"  Profit Factor: {result['stats']['profit_factor']:.2f}")
    
    print(f"\n💵 P&L:")
    print(f"  Realizado: ${result['stats']['pl_realized_usd']:+,.2f} ({result['stats']['pl_realized_percent']:+.2f}%)")
    print(f"  No Realizado: ${result['stats']['pl_unrealized_usd']:+,.2f}")
    
    return result

def test_real_data_30_days():
    """Prueba con datos reales de últimos 30 días"""
    print("\n" + "="*70)
    print("TEST REAL: Últimos 30 días - Datos de API en vivo")
    print("="*70)
    
    manager = JournalManager(capital_initial=5000.0)
    result = manager.get_combined_journal(days=30)
    
    print(f"\n📊 PERÍODO:")
    print(f"  Días: {result['period']['days']}")
    print(f"  Desde: {result['period']['from']}")
    print(f"  Hasta: {result['period']['to']}")
    print(f"  Total trades: {result['period']['trades_count']}")
    
    print(f"\n💰 CAPITAL:")
    print(f"  Inicial: ${result['capital']['initial']:,.2f}")
    print(f"  Actual: ${result['capital']['current']:,.2f}")
    print(f"  P&L Total: ${result['capital']['pl_total_usd']:+,.2f} ({result['capital']['pl_total_percent']:+.2f}%)")
    
    print(f"\n📈 POSICIONES:")
    print(f"  Abiertas: {result['positions']['open_count']}")
    print(f"  Cerradas: {result['positions']['closed_count']}")
    print(f"  Total Ops: {result['stats']['total_ops']}")
    
    print(f"\n📋 DETALLE ABIERTAS:")
    for pos in result['positions']['open_detail']:
        print(f"  {pos['symbol']:10s} | {pos['qty']:10.6f} shares | ${pos['cost_basis']:10.2f} | {pos['entries']} entrada(s)")
    
    print(f"\n🎯 MÉTRICAS:")
    print(f"  Wins: {result['stats']['wins']}")
    print(f"  Losses: {result['stats']['losses']}")
    print(f"  Win Rate: {result['stats']['win_rate']:.2f}%")
    print(f"  Profit Factor: {result['stats']['profit_factor']:.2f}")
    
    print(f"\n💵 P&L:")
    print(f"  Realizado: ${result['stats']['pl_realized_usd']:+,.2f} ({result['stats']['pl_realized_percent']:+.2f}%)")
    print(f"  No Realizado: ${result['stats']['pl_unrealized_usd']:+,.2f}")
    
    return result

if __name__ == "__main__":
    print("\n" + "="*70)
    print("VALIDACIÓN CON DATOS REALES DE TUS BROKERS")
    print("="*70)
    
    # Test 7 días
    result_7d = test_real_data_7_days()
    
    # Test 30 días
    result_30d = test_real_data_30_days()
    
    print("\n" + "="*70)
    print("COMPARACIÓN 7d vs 30d")
    print("="*70)
    print(f"Trades 7d:  {result_7d['period']['trades_count']}")
    print(f"Trades 30d: {result_30d['period']['trades_count']}")
    print(f"Abiertas 7d:  {result_7d['positions']['open_count']}")
    print(f"Abiertas 30d: {result_30d['positions']['open_count']}")
    print(f"Cerradas 7d:  {result_7d['positions']['closed_count']}")
    print(f"Cerradas 30d: {result_30d['positions']['closed_count']}")
    
    print("\n✅ TESTS CON DATOS REALES COMPLETADOS")
