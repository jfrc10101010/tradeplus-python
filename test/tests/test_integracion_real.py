"""
FASE 1.6 - VALIDACIÓN DE INTEGRACIÓN REAL
Ejecutar CoinbaseConnector contra servidor REAL de Coinbase
Capturar datos REALES recibidos
"""

import sys
import os
import json
import time
import asyncio
from datetime import datetime

# Agregar path
sys.path.insert(0, os.path.dirname(__file__))

from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager
from hub.connectors.coinbase_connector import CoinbaseConnector


async def main():
    """Ejecutar integración real con Coinbase"""
    
    print("\n" + "="*80)
    print("FASE 1.6 - VALIDACIÓN DE INTEGRACIÓN REAL")
    print("="*80)
    print(f"Timestamp inicio: {datetime.now().isoformat()}")
    print()
    
    # Crear manager JWT REAL
    print("📋 Inicializando CoinbaseJWTManager...")
    jwt_manager = CoinbaseJWTManager()
    jwt_token = jwt_manager.get_current_jwt()
    print(f"   ✅ JWT obtenido: {jwt_token[:50]}...")
    print(f"   ✅ JWT válido: {jwt_manager.is_jwt_valid()}")
    print()
    
    # Crear connector REAL
    print("🔌 Inicializando CoinbaseConnector...")
    connector = CoinbaseConnector(jwt_manager=jwt_manager)
    print(f"   ✅ Connector creado")
    print()
    
    # Lista para capturar mensajes
    captured_messages = []
    original_on_data = connector.on_data
    
    def capture_on_data(message):
        """Interceptar on_data para capturar mensajes"""
        if message:
            captured_messages.append({
                "timestamp": datetime.now().isoformat(),
                "data": message
            })
            if len(captured_messages) <= 10:
                print(f"   📨 Mensaje {len(captured_messages)} capturado: {message.get('type', 'unknown')}")
        original_on_data(message)
    
    connector.on_data = capture_on_data
    
    # Conectar
    print("🌐 Conectando a WebSocket privado de Coinbase...")
    print("   Endpoint: wss://advanced-trade-ws.coinbase.com")
    
    try:
        connected = await connector.connect()
        
        if not connected:
            print("   ❌ No se pudo conectar")
            return False
        
        print("   ✅ Conectado exitosamente")
        print()
        
        # Esperar y capturar datos
        print("⏱️  Esperando datos en tiempo real (10 segundos)...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            # Verificar si hay ticks en el buffer
            buffer_size = connector.get_buffer_size()
            if buffer_size > 0:
                print(f"   📊 {buffer_size} ticks en buffer")
            
            await asyncio.sleep(0.5)
        
        print()
        print("⏹️  Tiempo agotado - deteniendo captura")
        print()
        
        # Desconectar
        await connector.disconnect()
        
        # Mostrar resultados
        print("="*80)
        print("DATOS CAPTURADOS")
        print("="*80)
        print(f"Total de mensajes capturados: {len(captured_messages)}")
        print()
        
        # Mostrar cada mensaje
        for i, msg_obj in enumerate(captured_messages[:10], 1):
            print(f"\n--- MENSAJE {i} ---")
            print(f"Timestamp: {msg_obj['timestamp']}")
            print(f"Tipo: {msg_obj['data'].get('type', 'unknown')}")
            print(f"JSON:\n{json.dumps(msg_obj['data'], indent=2)}")
        
        # Guardar a archivo
        output_file = "captured_messages.json"
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp_inicio": datetime.now().isoformat(),
                "total_mensajes": len(captured_messages),
                "mensajes": captured_messages[:10]
            }, f, indent=2)
        
        print()
        print(f"✅ Mensajes guardados en: {output_file}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
