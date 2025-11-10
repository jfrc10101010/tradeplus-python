"""
TEST REAL - Coinbase WebSocket Privado con Datos en Tiempo Real

Conecta a tu cuenta Coinbase y recibe datos REALES de tu portafolio.
Token se renueva automáticamente si expira.
"""

import asyncio
import json
from hub.managers.coinbase_websocket_manager import CoinbaseWebSocketManager

async def main():
    manager = CoinbaseWebSocketManager(config_path=".")
    
    try:
        print("\n" + "="*80)
        print("CONECTANDO A COINBASE WEBSOCKET (DATOS PRIVADOS REALES)")
        print("="*80 + "\n")
        
        # Conectar
        success = await manager.connect()
        
        if success:
            print("\n✅ CONECTADO EXITOSAMENTE\n")
            
            # Suscribirse a tus productos (MODIFICA ESTOS SÍMBOLOS)
            products = ["BTC-USD", "ETH-USD", "SOL-USD"]  # Cambia por tus criptos
            print(f"📈 Suscribiendo a: {products}\n")
            
            await manager.subscribe(products)
            
            # Recibir datos durante 2 minutos
            print("📊 RECIBIENDO DATOS EN TIEMPO REAL (120 segundos)...\n")
            await asyncio.sleep(120)
            
            stats = manager.get_stats()
            print(f"\n✅ COMPLETADO")
            print(f"   Mensajes recibidos: {stats.get('messages_received', 0)}")
        else:
            print("❌ Error conectando")
    
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
