"""
Test Coinbase WebSocket PUBLICO (sin autenticación)
Para verificar si el problema es la autenticación o la conexión
"""
import asyncio
import json
import websockets


async def test_public_websocket():
    """Prueba WebSocket público de Coinbase (sin JWT)"""
    
    try:
        print("\n=== COINBASE PUBLIC WEBSOCKET ===")
        print("Conectando a wss://ws-feed.exchange.coinbase.com...")
        
        # WebSocket PUBLICO (no requiere autenticación)
        ws = await websockets.connect("wss://ws-feed.exchange.coinbase.com")
        print("[OK] Conectado")
        
        # Suscribirse a ticker updates (público)
        sub_msg = json.dumps({
            "type": "subscribe",
            "product_ids": ["BTC-USD", "ETH-USD"],
            "channels": ["ticker"]
        })
        
        print(f"Enviando suscripción...")
        await ws.send(sub_msg)
        
        # Recibir respuestas
        print(f"Esperando respuestas...")
        for i in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(msg)
                msg_type = data.get('type', 'UNKNOWN')
                print(f"  Respuesta {i+1}: {msg_type} | {data}")
            except asyncio.TimeoutError:
                print(f"  Respuesta {i+1}: TIMEOUT")
                break
        
        await ws.close()
        print(f"\n[OK] Test completado")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_public_websocket())
