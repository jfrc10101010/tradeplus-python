"""
CoinbaseWebSocketManager - Conexión WebSocket PRIVADA/AUTENTICADA a Coinbase
Usa JWT real del archivo coinbase_current_jwt.json
Conecta a wss://advanced-trade-ws.coinbase.com (NO público, privado autenticado)
"""
import asyncio
import json
import logging
import time
from pathlib import Path
from datetime import datetime
import websockets
from typing import Optional, Dict, Any


class CoinbaseWebSocketManager:
    """Gestor de WebSocket privado/autenticado de Coinbase con JWT real"""
    
    # URL del WebSocket privado de Coinbase (NO es public, es authenticated)
    WEBSOCKET_URL = "wss://advanced-trade-ws.coinbase.com"
    
    def __init__(self, config_path: str = "hub", product_ids: list = None):
        """
        Inicializa conexión WebSocket privada
        
        Args:
            config_path: ruta a carpeta con JWT (default: 'hub')
            product_ids: lista de productos a suscribirse (default: ['BTC-USD', 'ETH-USD'])
        """
        self.config_path = Path(config_path)
        # Buscar JWT en raíz o en config_path
        self.jwt_file = Path("coinbase_current_jwt.json") if Path("coinbase_current_jwt.json").exists() else self.config_path / "coinbase_current_jwt.json"
        self.product_ids = product_ids or ["BTC-USD", "ETH-USD"]
        
        self.websocket = None
        self.current_jwt = None
        self.connected = False
        self.ticks_received = 0
        self.start_time = None
        
        # Logger
        self.logger = self._setup_logger()
        self.logger.info(f"✅ CoinbaseWebSocketManager inicializado (productos: {self.product_ids})")
    
    def _setup_logger(self):
        """Configura logger para WebSocket"""
        logger = logging.getLogger("CoinbaseWebSocket")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_jwt(self) -> Optional[str]:
        """
        Carga JWT REAL del archivo coinbase_current_jwt.json
        Si está expirado o no existe, genera uno nuevo
        
        Returns:
            JWT token string o None si no se puede generar
        """
        try:
            jwt_token = None
            expires_at = None
            
            # Intentar cargar del archivo
            if self.jwt_file.exists():
                with open(self.jwt_file, 'r') as f:
                    data = json.load(f)
                
                jwt_token = data.get('jwt')
                expires_at = data.get('expires_at')
                
                # Verificar que JWT no expiró
                if expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires_dt:
                        self.logger.warning(f"⚠️ JWT expiró a: {expires_at}")
                        jwt_token = None
            
            # Si JWT es válido, retornar
            if jwt_token and expires_at:
                self.logger.info(f"✅ JWT cargado (expira: {expires_at})")
                return jwt_token
            
            # Si no tenemos JWT válido, generar uno nuevo
            self.logger.info("🔄 Generando nuevo JWT...")
            try:
                from .coinbase_jwt_manager import CoinbaseJWTManager
                jwt_mgr = CoinbaseJWTManager(config_path=str(self.config_path))
                new_jwt = jwt_mgr.get_current_jwt()
                self.logger.info(f"✅ JWT generado exitosamente: {new_jwt[:20]}...")
                return new_jwt
            except Exception as e:
                self.logger.error(f"❌ Error generando JWT: {e}")
                return None
        
        except Exception as e:
            self.logger.error(f"❌ Error en _load_jwt: {e}")
            return None
    
    async def connect(self) -> bool:
        """
        Conecta a WebSocket privado de Coinbase con JWT real
        
        Returns:
            True si conexión exitosa, False si falló
        """
        try:
            # Cargar JWT del archivo
            self.current_jwt = self._load_jwt()
            if not self.current_jwt:
                self.logger.error("❌ No hay JWT válido disponible")
                return False
            
            self.logger.info(f"📡 Conectando a {self.WEBSOCKET_URL}...")
            
            # Conectar a WebSocket
            self.websocket = await websockets.connect(self.WEBSOCKET_URL)
            self.connected = True
            self.start_time = time.time()
            
            self.logger.info("✅ Conexión WebSocket establecida")
            
            # Enviar mensaje de suscripción CON JWT
            subscribe_msg = self._build_subscribe_message()
            await self.websocket.send(subscribe_msg)
            self.logger.info("📤 Mensaje de suscripción enviado")
            
            # Receiver loop - espera mensajes (ejecuta indefinidamente)
            await self._receive_loop(self.websocket)
            return True
        
        except asyncio.CancelledError:
            self.logger.info("⏹️ Conexión cancelada")
            self.connected = False
            return False
        except Exception as e:
            self.logger.error(f"❌ Error en conexión WebSocket: {e}")
            self.connected = False
            return False
    
    def _build_subscribe_message(self) -> str:
        """
        Construye mensaje JSON de suscripción con JWT autenticación
        
        Returns:
            JSON string para enviar a WebSocket
        """
        message = {
            "type": "subscribe",
            "product_ids": self.product_ids,
            "channel": "ticker",  # Canal de ticks en tiempo real
            "jwt": self.current_jwt  # JWT en el payload
        }
        
        return json.dumps(message)
    
    async def _receive_loop(self, ws):
        """
        Loop receptor que escucha mensajes del WebSocket
        
        Args:
            ws: conexión websocket
        """
        try:
            async for message in ws:
                try:
                    data = json.loads(message)
                    self.ticks_received += 1
                    
                    # Log cada tipo de mensaje recibido
                    msg_type = data.get('type', 'unknown')
                    
                    if msg_type == 'subscriptions':
                        self.logger.info(f"✅ Suscripciones confirmadas: {data.get('channels', [])}")
                    
                    elif msg_type == 'ticker':
                        # Tick de precio REAL
                        product = data.get('product_id', 'unknown')
                        price = data.get('price', 'N/A')
                        time_val = data.get('time', 'N/A')
                        self.logger.info(f"📊 TICK REAL {product}: ${price} [{time_val}]")
                        
                    elif msg_type in ['done', 'match', 'open', 'change']:
                        # Otros eventos privados de la cuenta
                        self.logger.debug(f"📋 Evento {msg_type}: {data}")
                    
                    else:
                        self.logger.debug(f"🔔 Mensaje: {data}")
                
                except json.JSONDecodeError:
                    self.logger.warning(f"⚠️ No se pudo parsear mensaje: {message}")
                except Exception as msg_error:
                    self.logger.error(f"❌ Error procesando mensaje: {msg_error}")
        
        except asyncio.CancelledError:
            self.logger.info("⏹️ Receive loop cancelado")
        except Exception as e:
            self.logger.error(f"❌ Error en receive loop: {e}")
    
    async def get_next_tick(self, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """
        Obtiene siguiente tick REAL del WebSocket
        
        Args:
            timeout: segundos máximo para esperar
        
        Returns:
            Dict con datos del tick o None si timeout
        """
        if not self.websocket or not self.connected:
            self.logger.error("❌ WebSocket no conectado")
            return None
        
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            data = json.loads(message)
            
            if data.get('type') == 'ticker':
                return {
                    'product_id': data.get('product_id'),
                    'price': float(data.get('price', 0)),
                    'time': data.get('time'),
                    'side': data.get('side'),  # 'buy' o 'sell'
                    'best_bid': float(data.get('best_bid', 0)) if data.get('best_bid') else None,
                    'best_ask': float(data.get('best_ask', 0)) if data.get('best_ask') else None,
                }
            
            return None
        
        except asyncio.TimeoutError:
            self.logger.warning(f"⏱️ Timeout esperando tick ({timeout}s)")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo tick: {e}")
            return None
    
    async def close(self):
        """Cierra conexión WebSocket"""
        try:
            if self.websocket:
                await self.websocket.close()
            self.connected = False
            self.logger.info("✅ Conexión WebSocket cerrada")
        except Exception as e:
            self.logger.error(f"❌ Error cerrando WebSocket: {e}")
            self.connected = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de la conexión"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            'connected': self.connected,
            'ticks_received': self.ticks_received,
            'elapsed_seconds': elapsed,
            'ticks_per_second': self.ticks_received / elapsed if elapsed > 0 else 0,
            'products': self.product_ids,
            'websocket_url': self.WEBSOCKET_URL,
        }


# =====================================================
# TEST: Ejecutar conexión real con datos reales
# =====================================================

async def test_coinbase_websocket_real():
    """
    TEST REAL - Conecta a WebSocket privado de Coinbase
    Requiere: coinbase_current_jwt.json con JWT válido
    """
    print("\n" + "="*60)
    print("🧪 TEST COINBASE WEBSOCKET PRIVADO CON JWT REAL")
    print("="*60 + "\n")
    
    manager = CoinbaseWebSocketManager(
        config_path=".",  # Busca coinbase_current_jwt.json en directorio actual
        product_ids=["BTC-USD", "ETH-USD"]
    )
    
    try:
        # Conectar (esto ejecuta el receive loop)
        connect_task = asyncio.create_task(manager.connect())
        
        # Esperar 10 segundos de ticks REALES
        await asyncio.sleep(10)
        
        # Mostrar estadísticas
        stats = manager.get_stats()
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS:")
        print("="*60)
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrumpido por usuario")
    
    finally:
        await manager.close()
        print("\n✅ Test completado\n")


if __name__ == "__main__":
    asyncio.run(test_coinbase_websocket_real())
