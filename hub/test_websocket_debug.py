#!/usr/bin/env python3
import websocket
import json
import time
import sys
import threading

sys.path.insert(0, 'hub')

from managers.coinbase_jwt_manager import CoinbaseJWTManager

print("="*70)
print("PRUEBA WEBSOCKET: DEBUG COMPLETO")
print("="*70)

# Paso 1: JWT
print("\n[1/3] Generando JWT...")
jwt_mgr = CoinbaseJWTManager()
jwt = jwt_mgr.get_current_jwt()
print(f"✅ JWT válido: {jwt[:40]}...")

# Paso 2: Conectar
print("\n[2/3] Conectando a wss://advanced-trade-ws.coinbase.com")
received = []
connection_ok = False
error_msg = None

def on_open(ws):
    global connection_ok
    connection_ok = True
    print("✅ WebSocket abierto - esperando mensajes...")

def on_message(ws, msg):
    print(f"\n📨 MENSAJE RECIBIDO:")
    print(f"   Raw: {msg[:100]}")
    try:
        data = json.loads(msg)
        print(f"   Type: {data.get('type')}")
        print(f"   Data: {json.dumps(data, indent=2)}")
        received.append(data)
        if len(received) >= 1:
            ws.close()
    except:
        print(f"   (No JSON)")

def on_error(ws, err):
    global error_msg
    error_msg = str(err)
    print(f"❌ ERROR: {err}")

def on_close(ws, code, msg):
    print(f"🔌 Cerrado: {code} - {msg}")

# Crear WebSocket
ws = websocket.WebSocketApp(
    "wss://advanced-trade-ws.coinbase.com",
    header=[f"Authorization: Bearer {jwt}"],
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

# Ejecutar en thread
print("   Conectando...")
thread = threading.Thread(target=lambda: ws.run_forever(ping_interval=30))
thread.daemon = True
thread.start()

# Esperar 5 segundos
print("   Esperando 5 segundos...")
for i in range(5):
    time.sleep(1)
    if received:
        print(f"   ✅ Mensaje recibido en segundo {i+1}")
        break
    if not connection_ok and i > 2:
        print(f"   ⚠️  No conectado después de {i+1} segundos")

# Cerrar
print("\n[3/3] Analizando resultados...")
ws.close()
time.sleep(1)

print("\n" + "="*70)
if received:
    print(f"✅ ÉXITO: Recibimos {len(received)} mensaje(s)")
    msg = received[0]
    print(f"\nPrimer mensaje:")
    print(f"- Tipo: {msg.get('type')}")
    print(f"- Datos: {msg}")
else:
    print("❌ FALLO: No se recibieron mensajes")
    if error_msg:
        print(f"- Error: {error_msg}")
    if not connection_ok:
        print("- No conectó")
    print("- Posible: JWT inválido para privado")
print("="*70 + "\n")
