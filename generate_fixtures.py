"""
Script para generar fixtures con datos reales de Schwab y Coinbase
"""
import sys
import json
import os

# Agregar hub al path
sys.path.insert(0, 'hub')

def generate_schwab_fixture():
    """Genera schwab_sample.json con datos reales"""
    try:
        print("📍 Generando schwab_sample.json...")
        from journal.schwab_adapter import SchwabAdapter
        
        adapter = SchwabAdapter()
        trades = adapter.get_transactions(days=30)
        
        output_path = 'test/fixtures/schwab_sample.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(trades, f, indent=2, default=str)
        
        print(f"✅ Schwab: {len(trades)} trades guardados en {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error Schwab: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_coinbase_fixture():
    """Genera coinbase_sample.json con datos reales"""
    try:
        print("\n📍 Generando coinbase_sample.json...")
        from journal.coinbase_adapter import CoinbaseAdapter
        
        adapter = CoinbaseAdapter()
        trades = adapter.get_fills(days=30)
        
        output_path = 'test/fixtures/coinbase_sample.json'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(trades, f, indent=2, default=str)
        
        print(f"✅ Coinbase: {len(trades)} trades guardados en {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error Coinbase: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Generador de Fixtures - Datos Reales de Brokers          ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    schwab_ok = generate_schwab_fixture()
    coinbase_ok = generate_coinbase_fixture()
    
    print("\n" + "="*60)
    print("RESUMEN:")
    print(f"  Schwab:   {'✅' if schwab_ok else '❌'}")
    print(f"  Coinbase: {'✅' if coinbase_ok else '❌'}")
    print("="*60)
