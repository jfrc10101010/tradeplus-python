"""
FASE 1.5-VAL PRIVADO: WebSocket USER endpoint con JWT
URL CORRECTA: wss://advanced-trade-ws-user.coinbase.com
"""

import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from collections import deque

sys.path.insert(0, str(Path(__file__).parent))

from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager

print("\n" + "="*80)
print("FASE 1.5-VAL PRIVADO: WEBSOCKET USER ENDPOINT")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# CARGAR JWT
print("Generando JWT...")
jwt_manager = CoinbaseJWTManager()
jwt_token = jwt_manager.generate_jwt()
print(f"JWT: {jwt_token[:30]}...")
print()

try:
    import websocket
except ImportError:
    print("ERROR: websocket-client no disponible")
    sys.exit(1)

messages = deque(maxlen=50)
private_events = []
connection_success = False
error_received = None

def on_open(ws):
    global connection_success
    print("WebSocket abierto")
    
    # Suscribirse al canal "user" (PRIVADO) en endpoint de USUARIO
    subscribe_msg = {
        "type": "subscribe",
        "channel": "user",
        "product_ids": ["BTC-USD", "ETH-USD"],
        "jwt": jwt_token
    }
    
    ws.send(json.dumps(subscribe_msg))
    print("Suscripcion al canal 'user' enviada con JWT")
    print()

def on_message(ws, msg):
    global connection_success, error_received
    
    try:
        data = json.loads(msg)
        msg_type = data.get('type', '?')
        messages.append(data)
        
        if msg_type == 'heartbeat':
            print(f"  Heartbeat recibido")
        elif msg_type == 'subscribe_done':
            connection_success = True
            print(f"  SUBSCRIPCION CONFIRMADA - Canal user activo")
            print()
        elif msg_type == 'error':
            error_received = data.get('reason', 'Unknown')
            print(f"  ERROR: {error_received}")
            ws.close()
        elif msg_type == 'done':
            order_id = data.get('order_id', '?')
            product = data.get('product_id', '?')
            side = data.get('side', '?')
            price = data.get('price', '?')
            
            private_events.append({
                'type': 'done',
                'order_id': order_id,
                'product_id': product,
                'side': side,
                'price': price,
                'full_data': data
            })
            
            print(f"  ORDEN PRIVADA (done): {product} {side} @ {price}")
        elif msg_type == 'open':
            order_id = data.get('order_id', '?')
            product = data.get('product_id', '?')
            side = data.get('side', '?')
            price = data.get('price', '?')
            
            private_events.append({
                'type': 'open',
                'order_id': order_id,
                'product_id': product,
                'side': side,
                'price': price,
                'full_data': data
            })
            
            print(f"  ORDEN PRIVADA (open): {product} {side} @ {price}")
        elif msg_type == 'match':
            trade_id = data.get('trade_id', '?')
            product = data.get('product_id', '?')
            side = data.get('side', '?')
            price = data.get('price', '?')
            
            private_events.append({
                'type': 'match',
                'trade_id': trade_id,
                'product_id': product,
                'side': side,
                'price': price,
                'full_data': data
            })
            
            print(f"  MATCH PRIVADO: {product} {side} @ {price}")
        else:
            print(f"  {msg_type}")
    except Exception as e:
        print(f"  Error: {e}")

def on_error(ws, error):
    print(f"  ERROR WebSocket: {error}")

def on_close(ws, code, msg):
    print(f"  Cerrado")

print("Conectando a wss://advanced-trade-ws-user.coinbase.com")
print("Canal: user (PRIVADO)")
print()

try:
    ws = websocket.WebSocketApp(
        "wss://advanced-trade-ws-user.coinbase.com",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    wst = threading.Thread(target=lambda: ws.run_forever(sslopt={"cert_reqs": 0}))
    wst.daemon = True
    wst.start()
    
    print("Esperando datos (10 segundos)...")
    print()
    time.sleep(10)
    
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# ANALIZAR
print()
print("="*80)
print("RESULTADO")
print("="*80)
print()

print(f"Mensajes: {len(messages)}")
print(f"Eventos privados: {len(private_events)}")
print()

if connection_success:
    print("EXITO: Canal 'user' confirmado")
    if private_events:
        print(f"EXITO: {len(private_events)} eventos privados recibidos")
        for i, e in enumerate(private_events[:3], 1):
            print(f"  {i}. {e['type'].upper()}: {e.get('product_id')} {e.get('side')} @ {e.get('price')}")
    else:
        print("INFO: Sin eventos privados (normal si no hay ordenes activas)")
else:
    print("ERROR: Suscripcion no confirmada")
    if error_received:
        print(f"Razon: {error_received}")

# GUARDAR
evidencia = {
    "timestamp": datetime.now().isoformat(),
    "endpoint": "wss://advanced-trade-ws-user.coinbase.com",
    "channel": "user",
    "connection_success": connection_success,
    "error": error_received,
    "messages_total": len(messages),
    "private_events": len(private_events),
    "private_events_sample": [{
        'type': e.get('type'),
        'product_id': e.get('product_id'),
        'side': e.get('side'),
        'price': e.get('price')
    } for e in private_events[:3]]
}

with open("validacion_fase_1_5_privado_final.json", 'w', encoding='utf-8') as f:
    json.dump(evidencia, f, indent=2, default=str)

print()
print("Archivo: validacion_fase_1_5_privado_final.json")

if ws:
    ws.close()

print()
print("="*80)
if connection_success and not error_received:
    if private_events:
        print("FASE 1.5-VAL PRIVADO: COMPLETADA - EVENTOS PRIVADOS RECIBIDOS")
    else:
        print("FASE 1.5-VAL PRIVADO: VALIDADA - CANAL USER ACTIVO")
else:
    print("FASE 1.5-VAL PRIVADO: INCONCLUSA")
print("="*80)
print()
