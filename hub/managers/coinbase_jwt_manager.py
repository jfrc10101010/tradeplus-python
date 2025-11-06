"""
Gestor de JWT de Coinbase - renovación automática cada ~100 segundos
Genera y renueva tokens JWT válidos para la API v3 de Coinbase
"""
import os
import json
import time
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import jwt as pyjwt


class CoinbaseJWTManager:
    """Genera y renueva tokens JWT para autenticación con Coinbase"""
    
    def __init__(self, config_path="hub"):
        """
        Inicializa gestor JWT
        
        Args:
            config_path: ruta a la carpeta de configuración (por defecto 'hub')
        """
        self.config_path = Path(config_path)
        self.jwt_output_file = self.config_path / "coinbase_current_jwt.json"
        self.api_key_file = self.config_path / "apicoinbase1fullcdp_api_key.json"
        self.env_file = self.config_path / ".env"
        
        # Cargar variables de entorno
        load_dotenv(self.env_file)
        
        # Inicializar logger
        self.logger = self._setup_logger()
        
        # Cargar credenciales
        self.api_key = None
        self.private_key = None
        self._load_credentials()
        
        # Estado del JWT actual
        self.current_jwt = None
        self.jwt_generated_at = None
        self.jwt_expires_at = None
        
        self.logger.info("✅ CoinbaseJWTManager inicializado")
    
    def _setup_logger(self):
        """Configura logger con formato detallado"""
        logger = logging.getLogger("CoinbaseJWTManager")
        
        # Evitar duplicados si ya existe
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def _load_credentials(self):
        """Carga credenciales desde archivos"""
        try:
            # Intentar desde JSON (prioridad)
            if self.api_key_file.exists():
                with open(self.api_key_file, 'r') as f:
                    config = json.load(f)
                    self.api_key = config.get('name')
                    self.private_key = config.get('privateKey')
                    self.logger.info(f"✅ Credenciales cargadas desde {self.api_key_file}")
                    self.logger.debug(f"API Key: {self.api_key[:50]}...")
                    return
        except Exception as e:
            self.logger.warning(f"⚠️ Error cargando JSON: {e}")
        
        # Fallback a .env
        try:
            self.api_key = os.getenv("COINBASE_API_KEY")
            self.private_key = os.getenv("COINBASE_PRIVATE_KEY")
            
            if self.api_key and self.private_key:
                self.logger.info("✅ Credenciales cargadas desde .env")
                self.logger.debug(f"API Key: {self.api_key[:50]}...")
                return
        except Exception as e:
            self.logger.error(f"❌ Error cargando .env: {e}")
        
        # Error si no se encontraron credenciales
        raise RuntimeError(
            f"❌ No se pudieron cargar credenciales. "
            f"Verificar {self.api_key_file} o {self.env_file}"
        )
    
    def generate_jwt(self):
        """
        Genera JWT válido para Coinbase API v3
        
        Returns:
            str: JWT válido (token)
        """
        try:
            if not self.private_key:
                raise RuntimeError("❌ Clave privada no cargada")
            
            # Cargar clave privada EC
            key = serialization.load_pem_private_key(
                self.private_key.encode(),
                password=None
            )
            
            # Timestamps
            now = int(time.time())
            expires_in = 120  # 2 minutos de validez
            
            # URI requerida por Coinbase (GET /api/v3/brokerage/accounts)
            request_method = 'GET'
            request_host = 'api.coinbase.com'
            request_path = '/api/v3/brokerage/accounts'
            uri = f"{request_method} {request_host}{request_path}"
            
            # Payload JWT
            payload = {
                'sub': self.api_key,
                'iss': 'cdp',
                'nbf': now,
                'exp': now + expires_in,
                'iat': now,
                'uri': uri
            }
            
            # Headers con kid y nonce requeridos
            headers = {
                'kid': self.api_key,
                'nonce': secrets.token_hex(),
                'alg': 'ES256',
                'typ': 'JWT'
            }
            
            # Generar JWT
            token = pyjwt.encode(
                payload,
                key,
                algorithm='ES256',
                headers=headers
            )
            
            # Guardar metadata
            self.current_jwt = token
            self.jwt_generated_at = datetime.now()
            self.jwt_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self.logger.info(f"✅ JWT generado: {token[:20]}...")
            self.logger.debug(f"   Válido por {expires_in} segundos")
            self.logger.debug(f"   Expira en: {self.jwt_expires_at}")
            
            return token
        
        except Exception as e:
            self.logger.error(f"❌ Error generando JWT: {e}")
            raise
    
    def refresh_jwt(self):
        """
        Renueva JWT si está próximo a expirar (> 60 segundos de antigüedad)
        
        Returns:
            bool: True si se renovó, False si sigue válido
        """
        try:
            # Primera ejecución - generar JWT
            if not self.current_jwt or not self.jwt_expires_at:
                self.logger.info("🔄 Primer JWT - generando...")
                token = self.generate_jwt()
                self._save_jwt_to_file(token)
                return True
            
            # Calcular tiempo restante
            now = datetime.now()
            time_remaining = (self.jwt_expires_at - now).total_seconds()
            
            # Si quedan menos de 60 segundos, renovar
            if time_remaining < 60:
                self.logger.info(f"🔄 JWT próximo a expirar ({time_remaining:.0f}s restantes) - renovando...")
                token = self.generate_jwt()
                self._save_jwt_to_file(token)
                return True
            else:
                self.logger.debug(f"✅ JWT aún válido por {time_remaining:.0f} segundos")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ Error renovando JWT: {e}")
            raise
    
    def _save_jwt_to_file(self, token):
        """
        Guarda JWT actual en archivo JSON
        
        Args:
            token: JWT string a guardar
        """
        try:
            jwt_data = {
                "jwt": token,
                "generated_at": self.jwt_generated_at.isoformat(),
                "expires_at": self.jwt_expires_at.isoformat(),
                "expires_in_seconds": int((self.jwt_expires_at - datetime.now()).total_seconds())
            }
            
            with open(self.jwt_output_file, 'w') as f:
                json.dump(jwt_data, f, indent=2)
            
            self.logger.info(f"✅ JWT guardado en {self.jwt_output_file}")
        
        except Exception as e:
            self.logger.error(f"❌ Error guardando JWT en archivo: {e}")
            raise
    
    def get_current_jwt(self):
        """
        Obtiene JWT actual, renovando si es necesario
        
        Returns:
            str: JWT válido
        """
        try:
            self.refresh_jwt()
            
            if not self.current_jwt:
                raise RuntimeError("❌ No hay JWT disponible")
            
            self.logger.debug(f"📋 JWT solicitado: {self.current_jwt[:20]}...")
            return self.current_jwt
        
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo JWT: {e}")
            raise
    
    def is_jwt_valid(self):
        """
        Verifica si JWT actual es válido
        
        Returns:
            bool: True si es válido, False si está vencido o próximo a expirar
        """
        try:
            if not self.jwt_expires_at:
                return False
            
            now = datetime.now()
            time_remaining = (self.jwt_expires_at - now).total_seconds()
            
            is_valid = time_remaining > 10  # Consideramos válido si quedan > 10 seg
            
            if is_valid:
                self.logger.debug(f"✅ JWT válido por {time_remaining:.0f} segundos")
            else:
                self.logger.warning(f"⚠️ JWT vencido o próximo a expirar ({time_remaining:.0f}s)")
            
            return is_valid
        
        except Exception as e:
            self.logger.error(f"❌ Error verificando JWT: {e}")
            return False
    
    async def start_background_refresh(self, interval_seconds=100):
        """
        Inicia tarea de renovación en background (asyncio)
        Renueva JWT cada 100 segundos automáticamente
        
        Args:
            interval_seconds: intervalo de renovación (por defecto 100 seg)
        """
        import asyncio
        
        self.logger.info(f"🔄 Iniciando renovación automática de JWT cada {interval_seconds}s...")
        
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                self.refresh_jwt()
        
        except asyncio.CancelledError:
            self.logger.info("⚠️ Renovación automática de JWT cancelada")
        except Exception as e:
            self.logger.error(f"❌ Error en renovación automática: {e}")
            raise


# Función auxiliar para uso standalone
def test_jwt_manager():
    """Prueba el CoinbaseJWTManager (para debugging)"""
    try:
        manager = CoinbaseJWTManager(config_path="hub")
        
        # Generar JWT
        jwt_token = manager.get_current_jwt()
        print(f"\n✅ JWT generado exitosamente:")
        print(f"   Token: {jwt_token[:30]}...")
        print(f"   Válido: {manager.is_jwt_valid()}")
        print(f"   Expira en: {manager.jwt_expires_at}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error en prueba: {e}")
        return False


if __name__ == "__main__":
    test_jwt_manager()
