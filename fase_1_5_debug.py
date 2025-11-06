"""
FASE 1.5-VAL: Debug simple de WebSocket
"""

import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from collections import deque

sys.path.insert(0, str(Path(__file__).parent))

print("Iniciando...")

try:
    import websocket
    print("✅ websocket importado")
except ImportError:
    print("❌ websocket no está disponible")
    sys.exit(1)

try:
    from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager
    print("✅ CoinbaseJWTManager importado")
except ImportError as e:
    print(f"❌ Error importando manager: {e}")
    sys.exit(1)

# Crear manager y JWT
print("\nCreando JWT manager...")
jwt_manager = CoinbaseJWTManager()
jwt = jwt_manager.generate_jwt()
print(f"JWT: {jwt[:30]}...")

# Configurar WebSocket simple
messages = []

def on_open(ws):
    print("\n✅ WebSocket ABIERTO")
    msg = {
        "type": "subscribe",
        "product_ids": ["BTC-USD", "ETH-USD"],
        "channels": ["heartbeat", "ticker"]
    }
    ws.send(json.dumps(msg))
    print("✅ Suscripción enviada")

def on_message(ws, msg):
    print(f"📨 Mensaje recibido: {len(msg)} bytes")
    try:
        data = json.loads(msg)
        msg_type = data.get('type', '?')
        print(f"   Tipo: {msg_type}")
        messages.append(data)
        
        if msg_type == 'ticker':
            print(f"   {data.get('product_id')} @ ${data.get('price')}")
    except json.JSONDecodeError:
        print(f"   ⚠️ JSON inválido: {msg[:50]}")
    except Exception as e:
        print(f"   ⚠️ Error: {type(e).__name__}: {e}")

def on_error(ws, error):
    print(f"❌ ERROR: {error}")

def on_close(ws, code, msg):
    print(f"🔌 Cerrado: {code} {msg}")

print("\nConectando a Coinbase WebSocket...")

try:
    ws = websocket.WebSocketApp(
        "wss://advanced-trade-ws.coinbase.com",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    print("Iniciando conexión...")
    wst = threading.Thread(target=lambda: ws.run_forever(sslopt={"cert_reqs": 0}))
    wst.daemon = True
    wst.start()
    
    print("Esperando 10 segundos...")
    time.sleep(10)
    
    print(f"\n✅ Mensajes recibidos: {len(messages)}")
    for i, m in enumerate(messages[:5], 1):
        print(f"  {i}. {m.get('type')} - {str(m)[:60]}...")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

finally:
    if ws:
        ws.close()
    print("\n✅ Fin")
