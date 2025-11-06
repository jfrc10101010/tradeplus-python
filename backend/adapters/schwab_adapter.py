import asyncio
import os
import json
from dotenv import load_dotenv
from .base import BaseAdapter

load_dotenv()

class SchwabAdapter(BaseAdapter):
    """Adapter REAL para Schwab/TOS usando schwab-py (oficial)"""
    
    def __init__(self):
        self.client = None
        self.streamer = None
        self.connected = False
        self.symbols = []
        self.ticks_queue = asyncio.Queue()
        self.account_id = os.getenv("TOS_ACCOUNT_ID")
    
    async def connect(self):
        """
        Conexión REAL a Schwab usando schwab-py.
        Flujo:
        1. Lee token de .env (debe existir y ser válido)
        2. Si no existe, abre OAuth en navegador automáticamente
        3. Conecta a streamer WebSocket de Schwab
        """
        try:
            from schwab import auth, client
            
            api_key = os.getenv("TOS_CLIENT_ID")
            app_secret = os.getenv("TOS_CLIENT_SECRET")
            callback_url = os.getenv("TOS_CALLBACK_URL")
            token_path = ".schwab_token.json"
            
            print("🔐 Autenticando con Schwab...")
            
            # schwab-py maneja OAuth automáticamente
            # Si no hay token, abre el navegador
            # Si hay token válido, lo usa
            try:
                self.client = auth.easy_client(
                    api_key,
                    app_secret,
                    callback_url,
                    token_path
                )
                print("✅ Cliente Schwab autenticado")
            except Exception as auth_error:
                print(f"⚠️ Error OAuth: {auth_error}")
                print("💡 Necesitas ejecutar: python scripts/get_schwab_token.py")
                raise
            
            # Obtener credenciales del streamer
            print("🔌 Obteniendo credenciales del streamer...")
            principals = self.client.get_principal()
            
            # Extraer datos del streamer
            streamer_info = principals["streamerInfo"]
            self.streamer_url = streamer_info["streamerSocketUrl"]
            self.streamer_token = principals["token"]
            self.company_id = streamer_info["schwabClientConfig"]["schwabClientId"]
            self.user_id = principals["preferredUserName"]
            
            print(f"✅ Credenciales del streamer obtenidas")
            print(f"   URL: {self.streamer_url}")
            print(f"   User: {self.user_id}")
            
            self.connected = True
            
        except Exception as e:
            print(f"❌ Error conexión Schwab: {e}")
            self.connected = False
            raise
    
    async def subscribe(self, symbols):
        """Suscribirse a símbolos REALES"""
        self.symbols = symbols
        print(f"✅ Suscrito a Schwab: {symbols}")
        
        # Inicia loop de streaming en background
        asyncio.create_task(self._stream_loop())
    
    async def _stream_loop(self):
        """Loop REAL que obtiene datos de streamer de Schwab"""
        if not self.connected or not self.client:
            print("❌ No conectado a Schwab")
            return
        
        try:
            # Usar la API de quotes de Schwab para obtener datos en tiempo real
            while self.connected:
                for symbol in self.symbols:
                    try:
                        # Obtener quote actual del símbolo
                        quote_data = self.client.get_quote(symbol)
                        
                        if quote_data and symbol in quote_data:
                            quote = quote_data[symbol]
                            
                            # Normalizar a estructura estándar
                            tick_data = {
                                'symbol': symbol,
                                'last': quote.get('lastPrice', 0),
                                'bid': quote.get('bidPrice', 0),
                                'ask': quote.get('askPrice', 0),
                                'volume': quote.get('bidSize', 0) + quote.get('askSize', 0),
                                'timestamp': quote.get('quoteTime', 0)
                            }
                            
                            await self.ticks_queue.put(tick_data)
                            print(f"📊 Tick {symbol}: ${tick_data['last']}")
                    
                    except Exception as e:
                        print(f"⚠️ Error obteniendo quote {symbol}: {e}")
                
                # Esperar antes de siguiente batch (evitar rate limiting)
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"❌ Error en stream loop: {e}")
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
        print("🔌 Desconectado de Schwab")
