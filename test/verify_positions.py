"""
╔═══════════════════════════════════════════════════════════════╗
║  T0: Verify Positions - Validación de Conteo de Operaciones ║
║  Valida agrupación correcta por símbolo (no por trade)      ║
╚═══════════════════════════════════════════════════════════════╝

TEST: Verifica que el conteo de operaciones sea correcto
- Abiertas: posiciones con quantity > 0 (por símbolo)
- Cerradas: posiciones con quantity = 0 (todas vendidas)
- Total ops = abiertas + cerradas (NO suma de trades individuales)

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


def test_position_counting():
    """
    TEST 1: Conteo correcto de operaciones por símbolo
    
    schwab_sample.json tiene:
    - HOOD: 2 compras (5 + 10 shares) = 1 posición ABIERTA
    - NU: 2 compras (1 + 1 shares) = 1 posición ABIERTA
    - AMD: 1 compra + 1 venta (5 - 5 = 0) = 1 posición CERRADA
    - NVDA: 1 compra (2 shares) = 1 posición ABIERTA
    - COIN: 1 compra (3 shares) = 1 posición ABIERTA
    
    coinbase_sample.json tiene:
    - BTC-USD: 1 compra (0.00492942) = 1 posición ABIERTA
    
    ESPERADO:
    - open_count: 5 (HOOD, NU, NVDA, COIN, BTC-USD)
    - closed_count: 1 (AMD)
    - total_ops: 6
    """
    print("="*70)
    print("TEST 1: Conteo de Operaciones por Símbolo (FIFO)")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    result = manager.compute_metrics(trades, days=None)
    
    positions = result['positions']
    stats = result['stats']
    
    print(f"\n📊 RESULTADOS:")
    print(f"  Posiciones Abiertas:  {positions['open_count']}")
    print(f"  Posiciones Cerradas:  {positions['closed_count']}")
    print(f"  Total Operaciones:    {stats['total_ops']}")
    
    print(f"\n📋 DETALLE POSICIONES ABIERTAS:")
    for pos in positions['open_detail']:
        print(f"  {pos['symbol']:8s} | Qty: {pos['qty']:10.6f} | Costo: ${pos['cost_basis']:8.2f} | Entradas: {pos['entries']}")
    
    # ASSERTIONS
    errors = []
    
    if positions['open_count'] != 5:
        errors.append(f"❌ open_count esperado 5, obtenido {positions['open_count']}")
    else:
        print(f"\n✅ open_count correcto: 5")
    
    if positions['closed_count'] != 1:
        errors.append(f"❌ closed_count esperado 1, obtenido {positions['closed_count']}")
    else:
        print(f"✅ closed_count correcto: 1")
    
    if stats['total_ops'] != 6:
        errors.append(f"❌ total_ops esperado 6, obtenido {stats['total_ops']}")
    else:
        print(f"✅ total_ops correcto: 6")
    
    # Verificar que HOOD tiene 2 entradas
    hood_pos = next((p for p in positions['open_detail'] if p['symbol'] == 'HOOD'), None)
    if hood_pos and hood_pos['entries'] == 2:
        print(f"✅ HOOD tiene 2 entradas (correcto)")
    else:
        errors.append(f"❌ HOOD debería tener 2 entradas")
    
    # Verificar que NU tiene 2 entradas
    nu_pos = next((p for p in positions['open_detail'] if p['symbol'] == 'NU'), None)
    if nu_pos and nu_pos['entries'] == 2:
        print(f"✅ NU tiene 2 entradas (correcto)")
    else:
        errors.append(f"❌ NU debería tener 2 entradas")
    
    return errors


def test_position_quantities():
    """
    TEST 2: Cantidades correctas en posiciones abiertas
    
    ESPERADO:
    - HOOD: 15.0 shares (5 + 10)
    - NU: 2.0 shares (1 + 1)
    - NVDA: 2.0 shares
    - COIN: 3.0 shares
    - BTC-USD: 0.00492942 (del fixture)
    """
    print("\n" + "="*70)
    print("TEST 2: Cantidades Correctas en Posiciones Abiertas")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    result = manager.compute_metrics(trades, days=None)
    positions = result['positions']['open_detail']
    
    expected = {
        'HOOD': 15.0,
        'NU': 2.0,
        'NVDA': 2.0,
        'COIN': 3.0,
        'BTC-USD': 0.00492942
    }
    
    errors = []
    
    for symbol, expected_qty in expected.items():
        pos = next((p for p in positions if p['symbol'] == symbol), None)
        
        if pos:
            actual_qty = pos['qty']
            if abs(actual_qty - expected_qty) < 0.0001:
                print(f"✅ {symbol:8s} qty correcto: {actual_qty}")
            else:
                errors.append(f"❌ {symbol} qty esperado {expected_qty}, obtenido {actual_qty}")
        else:
            errors.append(f"❌ {symbol} no encontrado en posiciones abiertas")
    
    return errors


def test_closed_position_pl():
    """
    TEST 3: P&L de operación cerrada (AMD)
    
    schwab_sample.json:
    - AMD BUY:  5 shares @ $142.50 = $712.50
    - AMD SELL: 5 shares @ $145.80 = $729.00
    
    ESPERADO:
    - P&L realizado: $729.00 - $712.50 = $16.50
    - P&L %: 16.50 / 712.50 = 2.32%
    """
    print("\n" + "="*70)
    print("TEST 3: P&L de Operación Cerrada (AMD)")
    print("="*70)
    
    trades = load_fixtures()
    manager = JournalManager(capital_initial=5000.0)
    
    result = manager.compute_metrics(trades, days=None)
    stats = result['stats']
    
    pl_realized = stats['pl_realized_usd']
    
    print(f"\n📊 P&L REALIZADO:")
    print(f"  Total: ${pl_realized:.2f}")
    
    # AMD debe generar +$16.50
    # (729.00 - 712.50 = 16.50)
    expected_pl = 16.50
    
    errors = []
    
    if abs(pl_realized - expected_pl) < 0.01:
        print(f"✅ P&L realizado correcto: ${pl_realized:.2f}")
    else:
        errors.append(f"❌ P&L esperado ${expected_pl:.2f}, obtenido ${pl_realized:.2f}")
    
    return errors


def main():
    """Ejecuta todos los tests"""
    print("\n")
    print("=" * 70)
    print(" " * 15 + "T0: VERIFY POSITIONS - TESTS")
    print("=" * 70)
    
    all_errors = []
    
    # TEST 1
    errors1 = test_position_counting()
    all_errors.extend(errors1)
    
    # TEST 2
    errors2 = test_position_quantities()
    all_errors.extend(errors2)
    
    # TEST 3
    errors3 = test_closed_position_pl()
    all_errors.extend(errors3)
    
    # RESUMEN
    print("\n" + "="*70)
    print("RESUMEN FINAL")
    print("="*70)
    
    if not all_errors:
        print("✅ TODOS LOS TESTS PASARON")
        print("\n✨ Conteo de operaciones por símbolo es CORRECTO")
        print("✨ Agrupación FIFO funciona correctamente")
        return 0
    else:
        print(f"❌ {len(all_errors)} ERRORES DETECTADOS:")
        for error in all_errors:
            print(f"  {error}")
        return 1


if __name__ == "__main__":
    exit(main())
