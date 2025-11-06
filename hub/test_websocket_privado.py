#!/usr/bin/env python3
import sys
import time
sys.path.insert(0, 'hub')

from managers.coinbase_jwt_manager import CoinbaseJWTManager
from connectors.coinbase_connector import CoinbaseConnector

print("\n" + "="*60)
print("PRUEBA FASE 1.5-VAL: WEBSOCKET PRIVADO COINBASE")
print("="*60 + "\n")

# Paso 1: Inicializar JWT Manager
print("PASO 1: Inicializar CoinbaseJWTManager")
print("-" * 60)
jwt_manager = CoinbaseJWTManager()
jwt = jwt_manager.get_current_jwt()
print(f"✅ JWT generado: {jwt[:30]}...")
print(f"✅ Válido por: 120 segundos\n")

# Paso 2: Conectar al WebSocket PRIVADO
print("PASO 2: Conectar al WebSocket PRIVADO")
print("-" * 60)
connector = CoinbaseConnector(jwt_manager)
connected = connector.connect()

if connected:
    print("✅ CONECTADO AL WEBSOCKET PRIVADO\n")
    
    # Paso 3: Esperar datos PRIVADOS
    print("PASO 3: Recibiendo datos PRIVADOS (esperar 10 segundos)...")
    print("-" * 60)
    time.sleep(10)
    
    # Paso 4: Analizar datos recibidos
    print("\nPASO 4: Análisis de datos recibidos")
    print("-" * 60)
    
    private_data = connector.get_private_data()
    messages_count = len(connector.message_queue)
    
    print(f"✅ Total de mensajes recibidos: {messages_count}")
    print(f"✅ Datos PRIVADOS recibidos: {len(private_data)}")
    
    if len(private_data) > 0:
        print("\n🔔 DATOS PRIVADOS CONFIRMADOS:")
        for i, data in enumerate(private_data, 1):
            print(f"\n   Evento {i}:")
            print(f"   - Tipo: {data.get('type')}")
            print(f"   - Producto: {data.get('product_id', 'N/A')}")
            if 'price' in data:
                print(f"   - Precio: {data.get('price')}")
            if 'side' in data:
                print(f"   - Lado: {data.get('side')}")
            if 'order_id' in data:
                print(f"   - Orden ID: {data.get('order_id')[:16]}...")
    else:
        print("\n⚠️ ADVERTENCIA: No se recibieron datos PRIVADOS")
        print("   Verificar que:")
        print("   - Tienes órdenes activas o historial reciente")
        print("   - JWT está autenticado correctamente")
        print("   - WebSocket es el PRIVADO, no público")
    
    # Paso 5: Desconectar
    print("\nPASO 5: Desconectar")
    print("-" * 60)
    connector.disconnect()
    time.sleep(1)
    print("✅ Desconectado\n")
    
else:
    print("❌ NO SE PUDO CONECTAR\n")

print("="*60)
print("FIN DE LA PRUEBA")
print("="*60 + "\n")
