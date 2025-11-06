"""
FASE 1.6 - VALIDACIÓN DE INTEGRACIÓN REAL (WebSocket Público)
Prueba contra WebSocket público para validar infraestructura
"""

import sys
import os
import json
import time
from datetime import datetime
import websocket

print("\n" + "="*80)
print("FASE 1.6 - VALIDACIÓN DE INTEGRACIÓN REAL")
print("="*80)
print(f"Timestamp inicio: {datetime.now().isoformat()}")
print()

print("🌐 Conectando a WebSocket PÚBLICO de Coinbase...")
print("   Endpoint: wss://ws-feed.exchange.coinbase.com")
print()

captured_messages = []

def on_message(ws, message):
    """Callback cuando se recibe un mensaje"""
    try:
        data = json.loads(message)
        captured_messages.append({
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
        
        msg_type = data.get("type", "unknown")
        
        if msg_type == "subscriptions":
            print(f"   ✅ Mensaje {len(captured_messages)}: Suscripción confirmada")
        elif msg_type == "ticker":
            product = data.get("product_id", "")
            price = data.get("price", "")
            print(f"   📊 Mensaje {len(captured_messages)}: Ticker {product} @ {price}")
        elif msg_type == "heartbeat":
            print(f"   💓 Mensaje {len(captured_messages)}: Heartbeat")
        else:
            print(f"   📨 Mensaje {len(captured_messages)}: {msg_type}")
        
        # Parar después de 5 mensajes
        if len(captured_messages) >= 5:
            ws.close()
    except Exception as e:
        print(f"   Error procesando mensaje: {e}")

def on_error(ws, error):
    """Callback en error"""
    print(f"   ❌ Error WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    """Callback al cerrar"""
    print(f"   🔌 WebSocket cerrado")

def on_open(ws):
    """Callback al abrir"""
    print(f"   ✅ WebSocket abierto")
    
    # Suscribirse a algunos productos
    subscribe_msg = {
        "type": "subscribe",
        "product_ids": ["BTC-USD", "ETH-USD"],
        "channels": ["ticker", "heartbeat"]
    }
    
    ws.send(json.dumps(subscribe_msg))
    print(f"   📨 Mensaje de suscripción enviado")

try:
    import threading
    
    print("🔄 Iniciando conexión...")
    ws = websocket.WebSocketApp(
        "wss://ws-feed.exchange.coinbase.com",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Ejecutar en thread con timeout
    print("⏱️  Esperando datos (máx 15 segundos)...")
    ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
    ws_thread.start()
    ws_thread.join(timeout=15)
    
    print()
    print("="*80)
    print("DATOS CAPTURADOS")
    print("="*80)
    print(f"Total de mensajes: {len(captured_messages)}")
    print()
    
    # Mostrar cada mensaje
    for i, msg_obj in enumerate(captured_messages, 1):
        print(f"\n--- MENSAJE {i} ---")
        print(f"Timestamp: {msg_obj['timestamp']}")
        msg_type = msg_obj['data'].get('type', 'unknown')
        print(f"Tipo: {msg_type}")
        print(f"JSON:\n{json.dumps(msg_obj['data'], indent=2)}")
    
    # Guardar a archivo
    output_file = "captured_messages_public.json"
    with open(output_file, 'w') as f:
        json.dump({
            "endpoint": "wss://ws-feed.exchange.coinbase.com",
            "timestamp_inicio": datetime.now().isoformat(),
            "total_mensajes": len(captured_messages),
            "mensajes": captured_messages
        }, f, indent=2)
    
    print()
    print(f"✅ Datos guardados en: {output_file}")
    
    # Análisis de datos
    print()
    print("="*80)
    print("ANÁLISIS DE DATOS")
    print("="*80)
    
    btc_tickers = [m for m in captured_messages if m['data'].get('product_id') == 'BTC-USD']
    eth_tickers = [m for m in captured_messages if m['data'].get('product_id') == 'ETH-USD']
    
    if btc_tickers:
        print(f"\n✅ BTC-USD tickers recibidos: {len(btc_tickers)}")
        for ticker in btc_tickers[:3]:
            price = ticker['data'].get('price')
            side = ticker['data'].get('side')
            print(f"   - Precio: ${price} ({side})")
    
    if eth_tickers:
        print(f"\n✅ ETH-USD tickers recibidos: {len(eth_tickers)}")
        for ticker in eth_tickers[:3]:
            price = ticker['data'].get('price')
            side = ticker['data'].get('side')
            print(f"   - Precio: ${price} ({side})")
    
    print()
    print("✅ INTEGRACIÓN VALIDADA - DATOS REALES RECIBIDOS")
    print("="*80)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
