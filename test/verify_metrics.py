"""
╔═══════════════════════════════════════════════════════════════╗
║  T0: Verify Metrics - Validación de Cálculos de Métricas    ║
║  Win Rate, Profit Factor, P&L Realizado %                   ║
╚═══════════════════════════════════════════════════════════════╝

TEST: Verifica que las métricas se calculen correctamente
- Win Rate: solo cuenta operaciones CERRADAS
- Profit Factor: total wins / total losses
- P&L Realizado %: porcentaje sobre capital invertido en cerradas
- Losses: operaciones cerradas perdedoras

DATOS: schwab_sample.json + coinbase_sample.json
"""

import sys
import json
import os

# Agregar hub al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from journal.journal_manager_t0 import JournalManager


def load_fixtures():
    """Carga fixtures de test"""
    fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    with open(os.path.join(fixtures_dir, 'schwab_sample.json'), 'r', encoding='utf-8-sig') as f:
        schwab = json.load(f)
    
    with open(os.path.join(fixtures_dir, 'coinbase_sample.json'), 'r', encoding='utf-8-sig') as f:
        coinbase = json.load(f)
    
    return schwab + coinbase


def test_win_rate_calculation():
    """
    TEST 1: Win Rate solo cuenta operaciones CERRADAS
    
    schwab_sample.json tiene:
    - 1 operación cerrada: AMD (BUY @ 142.50, SELL @ 145.80) = WIN
    
    ESPERADO:
    - wins: 1
    - losses: 0
    - win_rate: 100% (1 de 1 cerradas)
    
    IMPORTANTE: Las 5 posiciones abiertas NO cuentan para win_rate
    """
    print("="*70)
    print("TEST 1: Win Rate (Solo Operaciones Cerradas)")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    result = manager.compute_metrics(trades, days=None)
    stats = result['stats']
    
    print(f"\n📊 MÉTRICAS:")
    print(f"  Wins:      {stats['wins']}")
    print(f"  Losses:    {stats['losses']}")
    print(f"  Win Rate:  {stats['win_rate']}%")
    
    errors = []
    
    if stats['wins'] != 1:
        errors.append(f"❌ wins esperado 1, obtenido {stats['wins']}")
    else:
        print(f"\n✅ Wins correcto: 1")
    
    if stats['losses'] != 0:
        errors.append(f"❌ losses esperado 0, obtenido {stats['losses']}")
    else:
        print(f"✅ Losses correcto: 0")
    
    if stats['win_rate'] != 100.0:
        errors.append(f"❌ win_rate esperado 100.0%, obtenido {stats['win_rate']}%")
    else:
        print(f"✅ Win Rate correcto: 100.0%")
    
    return errors


def test_profit_factor():
    """
    TEST 2: Profit Factor = Total Wins / Total Losses
    
    Con solo 1 operación ganadora y 0 perdedoras:
    - Profit factor debería ser 0.0 (o infinito, según implementación)
    
    Si hubiera losses, ejemplo:
    - Wins: $500
    - Losses: $200
    - Profit Factor: 500 / 200 = 2.5
    """
    print("\n" + "="*70)
    print("TEST 2: Profit Factor")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    result = manager.compute_metrics(trades, days=None)
    stats = result['stats']
    
    print(f"\n📊 PROFIT FACTOR:")
    print(f"  Valor: {stats['profit_factor']}")
    
    errors = []
    
    # Con 0 losses, profit_factor = 0.0 (según implementación)
    if stats['losses'] == 0:
        if stats['profit_factor'] == 0.0:
            print(f"✅ Profit factor correcto (sin losses): 0.0")
        else:
            errors.append(f"⚠️ Profit factor con 0 losses: {stats['profit_factor']} (esperado 0.0)")
    
    return errors


def test_pl_realized_percent():
    """
    TEST 3: P&L Realizado % = (P&L / Capital Invertido en Cerradas) * 100
    
    AMD cerrada:
    - Capital invertido: $712.50
    - P&L realizado: $16.50
    - P&L %: (16.50 / 712.50) * 100 = 2.32%
    """
    print("\n" + "="*70)
    print("TEST 3: P&L Realizado Porcentaje")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    result = manager.compute_metrics(trades, days=None)
    stats = result['stats']
    
    print(f"\n📊 P&L REALIZADO:")
    print(f"  USD:        ${stats['pl_realized_usd']:.2f}")
    print(f"  Porcentaje: {stats['pl_realized_percent']:.2f}%")
    
    errors = []
    
    expected_usd = 16.50
    expected_percent = 2.32  # 16.50 / 712.50 * 100
    
    if abs(stats['pl_realized_usd'] - expected_usd) < 0.01:
        print(f"\n✅ P&L USD correcto: ${stats['pl_realized_usd']:.2f}")
    else:
        errors.append(f"❌ P&L USD esperado ${expected_usd:.2f}, obtenido ${stats['pl_realized_usd']:.2f}")
    
    if abs(stats['pl_realized_percent'] - expected_percent) < 0.1:
        print(f"✅ P&L % correcto: {stats['pl_realized_percent']:.2f}%")
    else:
        errors.append(f"❌ P&L % esperado {expected_percent:.2f}%, obtenido {stats['pl_realized_percent']:.2f}%")
    
    return errors


def test_unrealized_pl():
    """
    TEST 4: P&L No Realizado (requiere precios actuales)
    
    Sin precios actuales, debería usar costo promedio:
    - Unrealized = 0 o (current_price - avg_cost) * qty
    
    Con precios actuales simulados:
    - HOOD: 15 shares @ $35.61 avg, current $40 = +$65.85
    """
    print("\n" + "="*70)
    print("TEST 4: P&L No Realizado (con precios mock)")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    # Sin precios actuales
    result1 = manager.compute_metrics(trades, days=None, current_prices=None)
    print(f"\n📊 SIN precios actuales:")
    print(f"  P&L No Realizado: ${result1['stats']['pl_unrealized_usd']:.2f}")
    
    # Con precios actuales simulados
    current_prices = {
        'HOOD': 40.0,      # Comprado @ avg 35.61
        'NU': 16.0,        # Comprado @ avg 15.275
        'NVDA': 750.0,     # Comprado @ 720.50
        'COIN': 260.0,     # Comprado @ 245.75
        'BTC-USD': 102000.0  # Comprado @ 100823.16
    }
    
    result2 = manager.compute_metrics(trades, days=None, current_prices=current_prices)
    print(f"\n📊 CON precios actuales:")
    print(f"  P&L No Realizado: ${result2['stats']['pl_unrealized_usd']:.2f}")
    
    errors = []
    
    # Validar que CON precios, unrealized > 0
    if result2['stats']['pl_unrealized_usd'] > 0:
        print(f"\n✅ P&L no realizado calculado con precios actuales")
    else:
        errors.append(f"⚠️ P&L no realizado debería ser > 0 con precios actuales")
    
    # Mostrar detalle por posición
    print(f"\n📋 DETALLE POSICIONES ABIERTAS:")
    for pos in result2['positions']['open_detail']:
        print(f"  {pos['symbol']:8s} | {pos['qty']:8.4f} @ ${pos['avg_cost']:8.2f} → ${pos['current_price']:8.2f} | P&L: ${pos['unrealized_pl']:+8.2f}")
    
    return errors


def test_combined_metrics():
    """
    TEST 5: Métricas Combinadas - Resumen Completo
    """
    print("\n" + "="*70)
    print("TEST 5: Resumen Completo de Métricas")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    result = manager.compute_metrics(trades, days=None)
    
    print(f"\n📊 CAPITAL:")
    print(f"  Inicial:  ${result['capital']['initial']:,.2f}")
    print(f"  Actual:   ${result['capital']['current']:,.2f}")
    print(f"  P&L Total: ${result['capital']['pl_total_usd']:+,.2f} ({result['capital']['pl_total_percent']:+.2f}%)")
    
    print(f"\n📊 POSICIONES:")
    print(f"  Abiertas:  {result['positions']['open_count']}")
    print(f"  Cerradas:  {result['positions']['closed_count']}")
    print(f"  Total Ops: {result['stats']['total_ops']}")
    
    print(f"\n📊 PERFORMANCE:")
    print(f"  Wins:          {result['stats']['wins']}")
    print(f"  Losses:        {result['stats']['losses']}")
    print(f"  Win Rate:      {result['stats']['win_rate']:.2f}%")
    print(f"  Profit Factor: {result['stats']['profit_factor']:.2f}")
    
    print(f"\n📊 P&L:")
    print(f"  Realizado:     ${result['stats']['pl_realized_usd']:+,.2f} ({result['stats']['pl_realized_percent']:+.2f}%)")
    print(f"  No Realizado:  ${result['stats']['pl_unrealized_usd']:+,.2f}")
    print(f"  Avg por Trade: ${result['stats']['avg_pl_per_trade']:+,.2f}")
    
    errors = []
    
    # Validaciones básicas
    if result['stats']['total_ops'] == result['positions']['open_count'] + result['positions']['closed_count']:
        print(f"\n✅ total_ops = open_count + closed_count")
    else:
        errors.append(f"❌ total_ops inconsistente")
    
    return errors


def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("=" * 70)
    print(" " * 15 + "T0: VERIFY METRICS - TESTS")
    print("=" * 70)
    
    all_errors = []
    
    # TEST 1
    errors1 = test_win_rate_calculation()
    all_errors.extend(errors1)
    
    # TEST 2
    errors2 = test_profit_factor()
    all_errors.extend(errors2)
    
    # TEST 3
    errors3 = test_pl_realized_percent()
    all_errors.extend(errors3)
    
    # TEST 4
    errors4 = test_unrealized_pl()
    all_errors.extend(errors4)
    
    # TEST 5
    errors5 = test_combined_metrics()
    all_errors.extend(errors5)
    
    # RESUMEN
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    
    if not all_errors:
        print("✅ TODOS LOS TESTS PASARON")
        print("\n✨ Win Rate calculado correctamente (solo cerradas)")
        print("✨ Profit Factor implementado")
        print("✨ P&L Realizado con porcentaje sobre capital invertido")
        print("✨ P&L No Realizado funcional con precios actuales")
        return 0
    else:
        print(f"❌ {len(all_errors)} ERRORES DETECTADOS:")
        for error in all_errors:
            print(f"  {error}")
        return 1


if __name__ == "__main__":
    exit(main())
