"""
Debug completo de JWT de Coinbase
Prueba diferentes formatos de JWT y suscripción
"""
import asyncio
import json
import websockets
from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager


async def test_websocket_with_jwt():
    """Prueba diferentes formatos de JWT y suscripción"""
    
    jwt_mgr = CoinbaseJWTManager(config_path="hub")
    
    # Generar JWT
    jwt_websocket = jwt_mgr.generate_jwt_for_websocket()
    print(f"\n[OK] JWT WebSocket generado:")
    print(f"   {jwt_websocket[:60]}...")
    
    try:
        ws = await websockets.connect("wss://advanced-trade-ws.coinbase.com")
        print(f"\n[OK] Conectado a Coinbase WebSocket")
        
        # INTENTO 1: Suscripción directa con JWT en subscribe
        print(f"\n--- INTENTO 1: Suscripción básica con heartbeat ---")
        sub_msg_1 = json.dumps({
            "type": "subscribe",
            "channels": [
                {
                    "name": "heartbeat",
                    "product_ids": ["BTC-USD"]
                },
                {
                    "name": "user",
                    "product_ids": ["*"]
                }
            ],
            "jwt": jwt_websocket
        })
        
        print(f"Enviando: {sub_msg_1[:100]}...")
        await ws.send(sub_msg_1)
        
        # Recibir respuestas
        print(f"Esperando respuestas...")
        for i in range(5):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                data = json.loads(msg)
                print(f"  Respuesta {i+1}: {data.get('type', data.get('channel', 'UNKNOWN'))} | {data}")
            except asyncio.TimeoutError:
                print(f"  Respuesta {i+1}: TIMEOUT (sin respuesta)")
                break
        
        await ws.close()
        print(f"\n[OK] Test completado")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_websocket_with_jwt())
