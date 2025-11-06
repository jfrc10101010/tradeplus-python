"""
FASE 1.5-VAL: WebSocket CON AUTENTICACIÓN JWT CORRECTA
"""

import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from collections import deque
import base64
import hmac
import hashlib

sys.path.insert(0, str(Path(__file__).parent))

from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager

print("\n" + "="*80)
print("FASE 1.5-VAL: WEBSOCKET PRIVADO CON AUTENTICACIÓN JWT")
print("="*80)

try:
    import websocket
except ImportError:
    print("❌ websocket no disponible")
    sys.exit(1)

# Crear JWT
print("\n📋 Generando JWT...")
jwt_manager = CoinbaseJWTManager()
jwt = jwt_manager.generate_jwt()
print(f"   ✅ JWT: {jwt[:30]}...")

# Configurar suscripción CON JWT
messages = deque(maxlen=20)
success_event = threading.Event()
error_message = None

def on_open(ws):
    print("\n✅ WebSocket conectado")
    
    # Enviar SUBSCRIBE CON JWT
    msg = {
        "type": "subscribe",
        "product_ids": ["BTC-USD", "ETH-USD"],
        "channels": ["heartbeat", "ticker"],
        "signature": jwt  # El JWT va aquí para autenticación
    }
    ws.send(json.dumps(msg))
    print("   ✅ Suscripción CON JWT enviada")

def on_message(ws, msg):
    global error_message
    try:
        data = json.loads(msg)
        msg_type = data.get('type', '?')
        messages.append(data)
        
        print(f"   📨 {msg_type}", end='')
        
        if msg_type == 'error':
            error_message = data.get('reason', 'Unknown error')
            print(f" - {error_message}")
            ws.close()
        elif msg_type == 'subscribe_done':
            print(" ✅")
            success_event.set()
        elif msg_type == 'ticker':
            print(f" ({data.get('product_id')} @ ${data.get('price')})")
        else:
            print()
    except Exception as e:
        print(f"   ⚠️ Error: {e}")

def on_error(ws, error):
    print(f"   ❌ WebSocket Error: {error}")

def on_close(ws, code, msg):
    print(f"   🔌 Cerrado")

print("\nConectando a wss://advanced-trade-ws.coinbase.com...")

try:
    ws = websocket.WebSocketApp(
        "wss://advanced-trade-ws.coinbase.com",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    wst = threading.Thread(target=lambda: ws.run_forever(sslopt={"cert_reqs": 0}))
    wst.daemon = True
    wst.start()
    
    # Esperar confirmación
    if not success_event.wait(timeout=5):
        if error_message:
            print(f"\n❌ Error de suscripción: {error_message}")
        else:
            print("\n⚠️ Timeout esperando confirmación")
    
    print("\n📊 Capturando datos (5 segundos)...")
    time.sleep(5)
    
    print(f"\n✅ Mensajes recibidos: {len(messages)}")
    for i, m in enumerate(messages[:10], 1):
        t = m.get('type')
        if t == 'ticker':
            print(f"  {i}. TICKER: {m.get('product_id')} @ ${m.get('price')}")
        else:
            print(f"  {i}. {t}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    if ws:
        ws.close()
    print("\n✅ Fin")
