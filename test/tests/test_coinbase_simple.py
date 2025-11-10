#!/usr/bin/env python3
"""
TEST COINBASE - Prueba simple y real
"""
import asyncio
import json
import websockets
from pathlib import Path

async def test():
    # Cargar JWT
    jwt_file = Path("coinbase_current_jwt.json")
    with open(jwt_file) as f:
        data = json.load(f)
        jwt = data['jwt']
    
    print(f"JWT: {jwt[:50]}...")
    
    # Conectar
    url = "wss://advanced-trade-ws.coinbase.com"
    print(f"Conectando a {url}...")
    
    async with websockets.connect(url) as ws:
        print("✅ Conectado")
        
        # Suscribir
        msg = {
            "type": "subscribe",
            "product_ids": ["BTC-USD"],
            "channel": "ticker",  # CAMBIO: ticker en lugar de user
            "jwt": jwt
        }
        await ws.send(json.dumps(msg))
        print(f"Enviado: {msg}")
        
        # Recibir 10 mensajes
        count = 0
        async for msg in ws:
            data = json.loads(msg)
            msg_type = data.get('type')
            
            if msg_type == 'ticker':
                count += 1
                print(f"\n[TICK #{count}] {data.get('product_id')} = ${data.get('price')}")
                if count >= 10:
                    break
            else:
                print(f"[{msg_type}] {data}")

if __name__ == '__main__':
    asyncio.run(test())
