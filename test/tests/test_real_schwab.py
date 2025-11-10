"""
TEST REAL - Schwab WebSocket Privado con Datos en Tiempo Real

Conecta a tu cuenta Schwab y recibe datos REALES de tu portafolio.
Token se renueva automáticamente si expira.
"""

import asyncio
import json
from hub.managers.schwab_websocket_manager import SchwabWebSocketManager

async def main():
    manager = SchwabWebSocketManager(config_path=".")
    
    try:
        print("\n" + "="*80)
        print("CONECTANDO A SCHWAB WEBSOCKET (DATOS PRIVADOS REALES)")
        print("="*80 + "\n")
        
        # Conectar (la conexión se mantiene abierta en background)
        # El connect() ejecuta _receive_loop() internamente
        print("� Conectando...")
        success = await asyncio.wait_for(manager.connect(), timeout=60)
        
        if success:
            print("\n✅ CONECTADO Y AUTENTICADO\n")
    
    except asyncio.TimeoutError:
        print("❌ Timeout conectando")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
