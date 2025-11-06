import asyncio
import os
import json
from dotenv import load_dotenv
from .base import BaseAdapter

load_dotenv()

class CoinbaseAdapter(BaseAdapter):
    """Adapter REAL para Coinbase usando WebSocket oficial (API pública)"""
    
    def __init__(self):
        self.ws = None
        self.connected = False
        self.symbols = []
        self.ticks_queue = asyncio.Queue()
        self.ws_url = os.getenv("COINBASE_WS_URL", "wss://ws-feed.exchange.coinbase.com")
    
    async def connect(self):
        """Conecta a Coinbase WebSocket (API pública, sin autenticación necesaria)"""
        try:
            import websockets
            import asyncio
            
            print(f"🔌 Conectando a Coinbase WebSocket: {self.ws_url}")
            
            self.ws = await websockets.connect(self.ws_url)
            self.connected = True
            print("✅ Conectado a Coinbase (REAL)")
            
            # Inicia loop de recepción en background
            asyncio.create_task(self._receive_loop())
        
        except Exception as e:
            print(f"❌ Error Coinbase: {e}")
            self.connected = False
            raise
    
    async def subscribe(self, symbols):
        """Suscribirse a productos de Coinbase (BTC-USD, ETH-USD, etc)"""
        self.symbols = symbols
        print(f"✅ Suscrito a Coinbase: {symbols}")
        
        if not self.ws or not self.connected:
            print("❌ WebSocket no conectado")
            return
        
        # Enviar subscribe message
        subscribe_msg = {
            "type": "subscribe",
            "channels": [
                {
                    "name": "ticker",
                    "product_ids": symbols
                }
            ]
        }
        
        await self.ws.send(json.dumps(subscribe_msg))
        print(f"📨 Mensaje de suscripción enviado a: {symbols}")
    
    async def _receive_loop(self):
        """Loop REAL que recibe mensajes del WebSocket de Coinbase"""
        try:
            while self.connected and self.ws:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Procesar solo mensajes de tipo "ticker" (precios)
                if data.get('type') == 'ticker':
                    tick_data = {
                        'product_id': data.get('product_id'),
                        'price': float(data.get('price', 0)),
                        'best_bid': float(data.get('best_bid', 0)),
                        'best_ask': float(data.get('best_ask', 0)),
                        'last_size': float(data.get('last_size', 0)),
                        'timestamp': data.get('time')
                    }
                    
                    await self.ticks_queue.put(tick_data)
                    print(f"📊 Tick {tick_data['product_id']}: ${tick_data['price']}")
        
        except Exception as e:
            print(f"❌ Error en receive loop: {e}")
            self.connected = False
    
    async def get_tick(self):
        """Obtener tick REAL de la cola"""
        try:
            return self.ticks_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    async def disconnect(self):
        """Desconectar"""
        self.connected = False
        if self.ws:
            await self.ws.close()
        print("🔌 Desconectado de Coinbase")
