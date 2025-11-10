"""
Test básico para verificar que ambos brokers funcionan correctamente
"""
import asyncio
import requests
from datetime import datetime

async def test_schwab():
    """Prueba conexión Schwab"""
    print("\n" + "="*60)
    print("🧪 TEST SCHWAB")
    print("="*60)
    
    try:
        from hub.managers.schwab_token_manager import SchwabTokenManager
        
        token_manager = SchwabTokenManager(config_path="hub")
        token = token_manager.get_current_token()
        
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = requests.get(
            "https://api.schwabapi.com/trader/v1/accounts",
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            print("✅ Conexión exitosa")
            data = resp.json()
            if "securitiesAccount" in data:
                acct = data["securitiesAccount"]
                balance = acct.get("currentBalances", {})
                print(f"   - Cash Balance: ${balance.get('cashBalance', 0):,.2f}")
                print(f"   - Buying Power: ${balance.get('buyingPower', 0):,.2f}")
                print(f"   - Positions: {len(acct.get('positions', []))}")
            return True
        else:
            print(f"❌ HTTP {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_coinbase():
    """Prueba conexión Coinbase"""
    print("\n" + "="*60)
    print("🧪 TEST COINBASE")
    print("="*60)
    
    try:
        from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager
        
        jwt_manager = CoinbaseJWTManager(config_path="hub")
        jwt_token = jwt_manager.get_current_jwt()
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
        
        resp = requests.get(
            "https://api.coinbase.com/api/v3/brokerage/accounts",
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            print("✅ Conexión exitosa")
            data = resp.json()
            accounts = data.get("accounts", [])
            print(f"   - Wallets: {len(accounts)}")
            if accounts:
                total_available = sum(float(acc.get("available", 0)) for acc in accounts)
                print(f"   - Total Available: {total_available:.8f}")
            return True
        else:
            print(f"❌ HTTP {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print(f"\n🚀 Prueba de Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    schwab_ok = await test_schwab()
    coinbase_ok = await test_coinbase()
    
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    print(f"✅ Schwab:   {'OK' if schwab_ok else 'FALLÓ'}")
    print(f"✅ Coinbase: {'OK' if coinbase_ok else 'FALLÓ'}")
    
    if schwab_ok and coinbase_ok:
        print("\n🎉 ¡AMBOS BROKERS FUNCIONANDO EN PARALELO!")
    else:
        print("\n⚠️  Revisar conexiones")

if __name__ == "__main__":
    asyncio.run(main())
