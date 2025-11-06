import asyncio
import websockets
import json
import logging
import requests
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importar el gestor de tokens
try:
    from .schwab_token_manager import SchwabTokenManager
except ImportError:
    from schwab_token_manager import SchwabTokenManager


class SchwabWebSocketManager:
    """
    SCHWAB WEBSOCKET MANAGER - CONEXIÓN PRIVADA/AUTENTICADA CORRECTA

    ARQUITECTURA FINAL VERIFICADA:
    1. HTTP GET /v1/accounts → obtener streamerInfo
    2. WebSocket connect a streamerInfo.streamerSocketUrl
    3. Enviar JSON LOGIN con FORMATO CORRECTO (parámetros fijos)
    4. Recibir datos privados en tiempo real <50ms
    """

    def __init__(self, config_path: str = "."):
        self.config_path = Path(config_path)
        self.token_file = self.config_path / "current_token.json"
        self.ws = None
        self.connected = False
        self.ticks_received = 0
        self.streamer_info: Dict[str, Any] = {}
        self.access_token: Optional[str] = None
        self.base_url = "https://api.schwabapi.com/trader"
        self.request_id = 1
        
        # Inicializar el gestor de tokens
        self.token_manager: Optional[SchwabTokenManager] = None
        self._init_token_manager()

    def _init_token_manager(self):
        """Inicializa el gestor de tokens Schwab"""
        try:
            self.token_manager = SchwabTokenManager(config_path=str(self.config_path))
            logger.info("✓ SchwabTokenManager inicializado correctamente")
        except Exception as e:
            logger.error(f"✗ Error inicializando SchwabTokenManager: {e}")
            self.token_manager = None

    def _ensure_valid_token(self) -> bool:
        """
        MÉTODO CRÍTICO: Verifica token y renueva si es necesario
        
        Se debe llamar ANTES de cada operación que use el token:
        - _get_streamer_info()
        - connect()
        - subscribe_*()
        
        Returns:
            bool: True si hay token válido, False si error
        """
        try:
            if not self.token_manager:
                logger.error("✗ SchwabTokenManager no inicializado")
                return False
            
            # Obtener token (renueva automáticamente si es necesario)
            token = self.token_manager.get_current_token()
            
            if token:
                self.access_token = token
                logger.info(f"✓ Token válido disponible: {token[:30]}...")
                return True
            else:
                logger.error("✗ No se pudo obtener token")
                return False
        
        except Exception as e:
            logger.error(f"✗ Error en _ensure_valid_token: {e}")
            return False

    def _load_token(self) -> bool:
        """
        Cargar token OAuth desde archivo (LEGACY)
        NOTA: Usar _ensure_valid_token() en su lugar para renovación automática
        """
        try:
            # Intentar primero obtener token válido desde el token manager
            if self._ensure_valid_token():
                return True
            
            # Fallback: cargar del archivo
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    if self.access_token:
                        logger.info(f"✓ Token cargado correctamente: {self.access_token[:30]}...")
                        return True
            logger.error(f"✗ Token NO encontrado en: {self.token_file}")
            return False
        except Exception as e:
            logger.error(f"✗ Error cargando token: {e}")
            return False

    def _get_streamer_info(self) -> bool:
        """
        PASO 1: HTTP GET a /v1/userPreference (ENDPOINT CORRECTO - OFICIAL SCHWAB)
        Obtiene streamerInfo con URL y credenciales del WebSocket
        
        CRÍTICO: Primero asegura que el token sea válido (con renovación automática)
        """
        try:
            # 1️⃣ PASO CRÍTICO: Asegurar token válido antes de hacer la petición
            if not self._ensure_valid_token():
                logger.error("✗ No se pudo obtener token válido")
                return False
            
            if not self.access_token:
                logger.error("✗ Token no disponible")
                return False

            # 2️⃣ Hacer la petición HTTP con el token renovado
            url = f"{self.base_url}/v1/userPreference"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }

            logger.info(f"→ GET {url}")
            response = requests.get(url, headers=headers, timeout=10)
            logger.info(f"← Status: {response.status_code}")

            # 3️⃣ Manejar diferentes códigos de estado
            if response.status_code == 401:
                # Token expirado - intentar renovar y reintentar
                logger.warning("⚠ Token expirado (401) - renovando...")
                if self.token_manager:
                    self.token_manager.refresh_token()
                    self.access_token = self.token_manager.current_token
                    
                    # Reintentar una sola vez
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.get(url, headers=headers, timeout=10)
                    logger.info(f"← Reintento - Status: {response.status_code}")
                else:
                    logger.error("✗ No hay token manager para renovar")
                    return False

            if response.status_code == 200:
                data = response.json()
                streamer_info_data = data.get("streamerInfo", [])
                
                # streamerInfo es una lista con 1 elemento
                if isinstance(streamer_info_data, list) and len(streamer_info_data) > 0:
                    self.streamer_info = streamer_info_data[0]
                elif isinstance(streamer_info_data, dict):
                    self.streamer_info = streamer_info_data
                else:
                    self.streamer_info = {}

                if self.streamer_info:
                    logger.info(f"✓ streamerInfo obtenido correctamente:")
                    logger.info(f"  └─ URL: {self.streamer_info.get('streamerSocketUrl')}")
                    logger.info(f"  └─ Customer ID: {self.streamer_info.get('schwabClientCustomerId')}")
                    logger.info(f"  └─ Channel: {self.streamer_info.get('schwabClientChannel')}")
                    logger.info(f"  └─ Function ID: {self.streamer_info.get('schwabClientFunctionId')}")
                    logger.info(f"  └─ Correlation ID: {self.streamer_info.get('schwabClientCorrelId')}")
                    return True
                else:
                    logger.error("✗ streamerInfo vacío en respuesta")
                    return False
            else:
                logger.error(f"✗ HTTP {response.status_code}: {response.text[:300]}")
                return False

        except Exception as e:
            logger.error(f"✗ Error en _get_streamer_info: {e}")
            return False

    async def connect(self) -> bool:
        """
        PASO 2-3: Conectar WebSocket + Enviar LOGIN JSON (FORMATO CORRECTO)
        
        Ahora con renovación automática de tokens integrada
        """
        try:
            # 1️⃣ Asegurar token válido (con renovación automática si es necesario)
            if not self._ensure_valid_token():
                logger.error("✗ Fallo: token no válido")
                return False

            # 2️⃣ Obtener streamer info (también con renovación automática)
            if not self._get_streamer_info():
                logger.error("✗ Fallo: streamer_info no obtenido")
                return False

            ws_url = self.streamer_info.get("streamerSocketUrl")
            if not ws_url:
                logger.error("✗ URL WebSocket no disponible")
                return False

            logger.info(f"→ Conectando a WebSocket: {ws_url}")

            async with websockets.connect(ws_url) as ws:
                self.ws = ws
                self.connected = True
                logger.info(f"✓ WebSocket conectado exitosamente")

                # PASO 3: Enviar JSON LOGIN CON FORMATO CORRECTO
                # Basado en formato oficial de Schwab Streamer
                login_msg = {
                    "requests": [
                        {
                            "requestid": str(self.request_id),
                            "service": "ADMIN",
                            "command": "LOGIN",
                            "SchwabClientCustomerId": self.streamer_info.get("schwabClientCustomerId", ""),
                            "SchwabClientCorrelId": self.streamer_info.get("schwabClientCorrelId", str(uuid.uuid4())),
                            "parameters": {
                                "Authorization": self.access_token,
                                "SchwabClientChannel": self.streamer_info.get("schwabClientChannel", "IO"),
                                "SchwabClientFunctionId": self.streamer_info.get("schwabClientFunctionId", "Tradeticket")
                            }
                        }
                    ]
                }

                logger.info(f"→ Enviando JSON LOGIN:")
                logger.info(json.dumps(login_msg, indent=2)[:300])

                await ws.send(json.dumps(login_msg))
                logger.info(f"✓ JSON LOGIN enviado")

                self.request_id += 1

                # Recibir respuesta LOGIN
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    resp_data = json.loads(response)
                    logger.info(f"✓ Respuesta LOGIN recibida:")
                    logger.info(json.dumps(resp_data, indent=2)[:300])

                    # Validar respuesta
                    if resp_data.get("response"):
                        resp_content = resp_data["response"][0].get("content", {})
                        if resp_content.get("code") == 0:
                            logger.info(f"✓ LOGIN EXITOSO - Conexión autenticada")
                        else:
                            logger.error(f"✗ LOGIN FALLÓ - Code: {resp_content.get('code')}, Msg: {resp_content.get('msg')}")
                            self.connected = False
                            return False

                except asyncio.TimeoutError:
                    logger.warning("⚠ Timeout esperando respuesta LOGIN")
                except Exception as e:
                    logger.error(f"✗ Error procesando respuesta LOGIN: {e}")
                    self.connected = False
                    return False

                # Iniciar recepción de datos
                await self._receive_loop()
                return True

        except Exception as e:
            logger.error(f"✗ Error en connect: {e}")
            self.connected = False
            return False

    async def _receive_loop(self):
        """Recibir ticks en tiempo real del WebSocket"""
        try:
            while self.connected and self.ws:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
                    data = json.loads(msg)

                    # Procesar diferentes tipos de mensajes
                    if "response" in data or "snapshot" in data or "data" in data:
                        self.ticks_received += 1
                        msg_str = json.dumps(data)[:150]
                        logger.info(f"[TICK REAL #{self.ticks_received}] {msg_str}...")

                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError as e:
                    logger.debug(f"Mensaje no JSON recibido: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠ Error procesando mensaje: {e}")
                    break
        except Exception as e:
            logger.error(f"✗ Error en _receive_loop: {e}")
        finally:
            self.connected = False
            logger.info("Loop de recepción finalizado")

    async def subscribe_level_one(self, symbols: list) -> bool:
        """Suscribirse a LEVELONE_EQUITIES (precios reales)"""
        try:
            if not self.ws or not self.connected:
                logger.error("✗ WebSocket no conectado")
                return False

            self.request_id += 1

            sub_msg = {
                "requests": [
                    {
                        "requestid": str(self.request_id),
                        "service": "LEVELONE_EQUITIES",
                        "command": "SUBS",
                        "parameters": {
                            "keys": ",".join(symbols),
                            "fields": "0,1,2,3,4,5,6,7,8,9,10"
                        }
                    }
                ]
            }

            await self.ws.send(json.dumps(sub_msg))
            logger.info(f"✓ Suscripción a {symbols} enviada")
            return True

        except Exception as e:
            logger.error(f"✗ Error en subscribe: {e}")
            return False

    async def close(self):
        """Cerrar conexión WebSocket"""
        try:
            self.connected = False
            if self.ws:
                await self.ws.close()
            logger.info("✓ WebSocket cerrado correctamente")
        except Exception as e:
            logger.error(f"✗ Error cerrando WebSocket: {e}")

    def get_stats(self):
        """Retorna estadísticas de conexión"""
        return {
            'connected': self.connected,
            'ticks_received': self.ticks_received,
            'ticks_per_second': self.ticks_received / 10.0 if self.ticks_received else 0,
            'user_id': self.streamer_info.get('schwabClientCustomerId', 'unknown')
        }


async def test_schwab_websocket():
    """Test completo con datos REALES - WebSocket privado autenticado"""
    manager = SchwabWebSocketManager(".")

    try:
        logger.info("="*80)
        logger.info("INICIANDO TEST SCHWAB WEBSOCKET PRIVADO CON AUTENTICACIÓN CORRECTA")
        logger.info("="*80)

        # Conectar con timeout 30 segundos
        result = await asyncio.wait_for(manager.connect(), timeout=30)

        if result:
            # Suscribirse a acciones populares
            logger.info("Suscribiéndose a acciones...")
            await manager.subscribe_level_one(["AAPL", "MSFT", "GOOGL", "TSLA"])

            # Recibir datos durante 20 segundos
            logger.info("Recibiendo datos en tiempo real (20 segundos)...")
            await asyncio.sleep(20)

            logger.info(f"✓ Test completado. Total ticks recibidos: {manager.ticks_received}")
        else:
            logger.error("Conexión falló")

    except asyncio.TimeoutError:
        logger.error("✗ Timeout en conexión (30 segundos)")
    except Exception as e:
        logger.error(f"✗ Error en test: {e}")
    finally:
        await manager.close()
        logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(test_schwab_websocket())
