#!/usr/bin/env python3
import websocket
import json
import time
import sys
import traceback

sys.path.insert(0, 'hub')

from managers.coinbase_jwt_manager import CoinbaseJWTManager

print("="*70)
print("PRUEBA SIMPLE: WEBSOCKET PRIVADO COINBASE (CON DEBUG)")
print("="*70)

# Paso 1: Obtener JWT fresco
print("\n[1/4] Generando JWT...")
jwt_mgr = CoinbaseJWTManager()
jwt = jwt_mgr.get_current_jwt()
print(f"✅ JWT: {jwt[:30]}...")

# Paso 2: Definir callbacks
received_messages = []
error_detail = None

def on_open(ws):
    print("\n[2/4] WebSocket abierto ✅")
    
def on_message(ws, message):
    print(f"\n[3/4] Mensaje recibido:")
    try:
        data = json.loads(message)
        msg_type = data.get("type", "unknown")
        print(f"     Tipo: {msg_type}")
        print(f"     Contenido: {json.dumps(data, indent=2)}")
        received_messages.append(data)
        
        if len(received_messages) >= 3:
            print("\n✅ Recibimos 3 mensajes - Desconectando")
            ws.close()
    except Exception as e:
        print(f"Error parsando JSON: {e}")
        print(f"Mensaje raw: {message}")

def on_error(ws, error):
    global error_detail
    print(f"\n❌ Error WebSocket: {error}")
    error_detail = str(error)
    print(f"Tipo error: {type(error).__name__}")
    traceback.print_exc()
    
def on_close(ws, close_status_code, close_msg):
    print(f"\n[4/4] WebSocket cerrado")
    print(f"Status: {close_status_code}")
    print(f"Message: {close_msg}")

# Paso 3: Conectar
print("\n[Conectando a wss://advanced-trade-ws.coinbase.com...]")
try:
    ws = websocket.WebSocketApp(
        "wss://advanced-trade-ws.coinbase.com",
        header=[f"Authorization: Bearer {jwt}"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    ws.run_forever(ping_interval=30, ping_timeout=10)
except Exception as e:
    print(f"❌ Excepción al crear WebSocket: {e}")
    traceback.print_exc()


# Paso 4: Analizar
print("\n" + "="*70)
print("ANÁLISIS DE MENSAJES RECIBIDOS")
print("="*70)

if received_messages:
    print(f"✅ Total: {len(received_messages)} mensajes")
    for i, msg in enumerate(received_messages, 1):
        print(f"\n[Mensaje {i}]")
        print(f"Tipo: {msg.get('type')}")
        if 'product_id' in msg:
            print(f"Producto: {msg.get('product_id')}")
        if 'price' in msg:
            print(f"Precio: {msg.get('price')}")
        if 'sequence' in msg:
            print(f"Secuencia: {msg.get('sequence')}")
else:
    print("❌ NO se recibieron mensajes")
    print("\nDiagnóstico:")
    if error_detail:
        print(f"- Error capturado: {error_detail}")
    print("- JWT inválido O conectó a público en lugar de privado")
    print("- Timeout")

print("\n" + "="*70)
