import asyncio
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import deque
import websocket

try:
    from hub.adapters.base import BaseAdapter
    from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager
    from hub.core.models import Tick
except (ImportError, ModuleNotFoundError):
    from adapters.base import BaseAdapter
    from managers.coinbase_jwt_manager import CoinbaseJWTManager
    from core.models import Tick

class CoinbaseConnector(BaseAdapter):
    """
    Conector WebSocket PRIVADO de Coinbase con autenticación JWT.
    SOLO recibe canales privados: user, fills, done
    NO recibe datos públicos.
    """
    
    def __init__(self, jwt_manager: CoinbaseJWTManager, user_id: str = None):
        self.jwt_manager = jwt_manager
        self.user_id = user_id or "PERSONAL_USER"
        self.ws = None
        self.is_connected = False
        self.message_queue = deque(maxlen=1000)
        self.private_data_buffer = []
        
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        
        # Threads
        self.receive_thread = None
        self.process_thread = None
        self.stop_event = threading.Event()

    def connect(self) -> bool:
        """Conecta al WebSocket PRIVADO de Coinbase con JWT"""
        try:
            self.logger.info("🔐 Inicializando conexión PRIVADA a Coinbase WebSocket")
            
            # Obtener JWT válido
            jwt_token = self.jwt_manager.get_current_jwt()
            self.logger.info(f"✅ JWT obtenido: {jwt_token[:20]}...")
            
            # Crear mensaje de autenticación PRIVADA
            auth_message = {
                "type": "subscribe",
                "channels": [
                    {
                        "name": "user",
                        "product_ids": ["*"]
                    },
                    {
                        "name": "fills",
                        "product_ids": ["*"]
                    },
                    {
                        "name": "done",
                        "product_ids": ["*"]
                    }
                ]
            }
            
            # Conectar
            self.logger.info("📡 Conectando a wss://advanced-trade-ws.coinbase.com")
            self.ws = websocket.WebSocketApp(
                "wss://advanced-trade-ws.coinbase.com",
                on_open=lambda ws: self._on_open(ws, jwt_token, auth_message),
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                header=[f"Authorization: Bearer {jwt_token}"]
            )
            
            # Threads
            self.stop_event.clear()
            self.receive_thread = threading.Thread(
                target=self.ws.run_forever,
                kwargs={"ping_interval": 30, "ping_timeout": 10}
            )
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Esperar a que conecte
            time.sleep(2)
            
            if self.is_connected:
                self.logger.info("✅ CONEXIÓN PRIVADA ESTABLECIDA")
                return True
            else:
                self.logger.error("❌ No se pudo establecer conexión")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error en conexión: {str(e)}")
            return False

    def _on_open(self, ws, jwt_token, auth_message):
        """Callback cuando WebSocket se abre"""
        try:
            self.logger.info("🔓 WebSocket abierto")
            
            # Enviar autenticación
            ws.send(json.dumps(auth_message))
            self.logger.info("🔐 Mensaje de autenticación PRIVADA enviado")
            self.logger.info(f"   Canales: user, fills, done (TODOS PRIVADOS)")
            
            self.is_connected = True
            
        except Exception as e:
            self.logger.error(f"Error al abrir: {str(e)}")

    def _on_message(self, ws, message):
        """Callback cuando se recibe mensaje del WebSocket"""
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")
            
            # Logging por tipo
            if msg_type == "heartbeat":
                self.logger.debug(f"💓 Heartbeat recibido (seq: {data.get('sequence')})")
                
            elif msg_type == "subscribe_done":
                self.logger.info(f"✅ Suscripción PRIVADA confirmada")
                self.logger.info(f"   Canales: {[ch.get('name') for ch in data.get('channels', [])]}")
                
            elif msg_type == "done":
                self.logger.warning(f"🔔 DATOS PRIVADOS - Orden completada:")
                self.logger.warning(f"   Producto: {data.get('product_id')}")
                self.logger.warning(f"   Lado: {data.get('side')}")
                self.logger.warning(f"   Precio: {data.get('price')}")
                self.logger.warning(f"   ID: {data.get('order_id')[:8]}...")
                self.private_data_buffer.append(data)
                
            elif msg_type == "match":
                self.logger.warning(f"🔔 DATOS PRIVADOS - Match ejecutado:")
                self.logger.warning(f"   Producto: {data.get('product_id')}")
                self.logger.warning(f"   Tamaño: {data.get('size')}")
                self.logger.warning(f"   Precio: {data.get('price')}")
                self.private_data_buffer.append(data)
                
            elif msg_type == "error":
                self.logger.error(f"❌ ERROR de Coinbase: {data.get('message')}")
                
            else:
                self.logger.debug(f"📨 Mensaje {msg_type} recibido")
            
            self.message_queue.append(data)
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {str(e)}")

    def _on_error(self, ws, error):
        """Callback cuando hay error"""
        self.logger.error(f"❌ Error WebSocket: {str(error)}")
        self.is_connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        """Callback cuando cierra"""
        self.logger.info("🔌 WebSocket cerrado")
        self.is_connected = False

    def disconnect(self):
        """Desconecta gracefully"""
        try:
            self.logger.info("Desconectando...")
            self.stop_event.set()
            if self.ws:
                self.ws.close()
            self.is_connected = False
            self.logger.info("✅ Desconectado")
        except Exception as e:
            self.logger.error(f"Error al desconectar: {str(e)}")

    def get_private_data(self) -> List[Dict[Any, Any]]:
        """Retorna datos PRIVADOS recibidos (órdenes, fills, etc)"""
        return self.private_data_buffer

    def on_data(self, message: dict) -> None:
        """Implementa método abstracto de BaseAdapter"""
        self._on_message(None, json.dumps(message))

    def is_connected_status(self) -> bool:
        """Implementa método abstracto de BaseAdapter"""
        return self.is_connected
    
    async def get_tick(self) -> Optional[Tick]:
        """Implementa método abstracto de BaseAdapter"""
        if self.message_queue:
            return self.message_queue.popleft()
        return None
    
    async def subscribe(self, symbols: List[str]) -> bool:
        """Implementa método abstracto de BaseAdapter"""
        return True
