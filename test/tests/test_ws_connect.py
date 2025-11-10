"""
TEST RÁPIDO: ¿Conecta a WebSocket Schwab y Coinbase?
"""
import asyncio
import sys

async def test_schwab_ws():
    try:
        from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
        mgr = SchwabWebSocketManager(config_path="hub")
        print("🔌 Schwab: Intentando conectar...")
        await asyncio.sleep(2)
        await mgr.connect()
        print(f"✅ Schwab: CONECTADO = {mgr.connected}")
        return mgr.connected
    except Exception as e:
        print(f"❌ Schwab: {str(e)[:100]}")
        return False

async def test_coinbase_ws():
    try:
        from hub.managers.coinbase_websocket_manager import CoinbaseWebSocketManager
        mgr = CoinbaseWebSocketManager(config_path="hub")
        print("🔌 Coinbase: Intentando conectar...")
        await asyncio.sleep(2)
        await mgr.connect()
        print(f"✅ Coinbase: CONECTADO = {mgr.connected}")
        return mgr.connected
    except Exception as e:
        print(f"❌ Coinbase: {str(e)[:100]}")
        return False

async def main():
    print("\n" + "="*60)
    print("TEST: ¿Conectan ambos WebSockets?")
    print("="*60 + "\n")
    
    schwab_ok = await test_schwab_ws()
    await asyncio.sleep(1)
    coinbase_ok = await test_coinbase_ws()
    
    print("\n" + "="*60)
    if schwab_ok and coinbase_ok:
        print("✅ AMBOS WEBSOCKETS FUNCIONAN")
    else:
        print(f"⚠️  Schwab: {schwab_ok} | Coinbase: {coinbase_ok}")
    print("="*60)

asyncio.run(main())
