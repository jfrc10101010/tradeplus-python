"""
Gestor de tokens Schwab/TOS - renovación automática cada ~25 minutos
Renueva tokens OAuth2 válidos para la API de Schwab
"""
import os
import json
import time
import logging
import base64
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import requests


class SchwabTokenManager:
    """Renovación automática de tokens Schwab/TOS"""
    
    def __init__(self, config_path="hub"):
        """
        Inicializa gestor de tokens Schwab
        
        Args:
            config_path: ruta a la carpeta de configuración (por defecto 'hub')
        """
        self.config_path = Path(config_path)
        self.token_output_file = self.config_path / "current_token.json"
        self.env_file = self.config_path / ".env"
        self.oauth_url = "https://api.schwabapi.com/v1/oauth/token"
        
        # Cargar variables de entorno
        load_dotenv(self.env_file)
        
        # Inicializar logger
        self.logger = self._setup_logger()
        
        # Cargar credenciales
        self.client_id = None
        self.client_secret = None
        self.refresh_token_value = None
        self._load_credentials()
        
        # Estado del token actual
        self.current_token = None
        self.token_obtained_at = None
        self.token_expires_at = None
        self.token_expires_in = None
        
        self.logger.info("✅ SchwabTokenManager inicializado")
    
    def _setup_logger(self):
        """Configura logger con formato detallado"""
        logger = logging.getLogger("SchwabTokenManager")
        
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
        """Carga credenciales OAuth2 de Schwab desde .env"""
        try:
            self.client_id = os.getenv("TOS_CLIENT_ID")
            self.client_secret = os.getenv("TOS_CLIENT_SECRET")
            self.refresh_token_value = os.getenv("TOS_REFRESH_TOKEN")
            
            if not all([self.client_id, self.client_secret, self.refresh_token_value]):
                raise RuntimeError("❌ Faltan credenciales Schwab en .env")
            
            self.logger.info("✅ Credenciales Schwab cargadas desde .env")
            self.logger.debug(f"CLIENT_ID: {self.client_id[:30]}...")
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error cargando credenciales: {e}")
            raise
    
    def refresh_token(self):
        """
        Renueva token OAuth2 de Schwab
        
        Returns:
            bool: True si se renovó, False si hubo error
        """
        try:
            # Construir payload OAuth2
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token_value,
                "scope": "PlaceTrades AccountAccess MoveMoney"
            }
            
            # Construir header de autenticación Basic
            credentials = f"{self.client_id}:{self.client_secret}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {credentials_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            self.logger.info(f"🔄 Renovando token Schwab...")
            self.logger.debug(f"   Endpoint: {self.oauth_url}")
            
            # Hacer petición POST a Schwab OAuth
            response = requests.post(
                self.oauth_url,
                data=payload,
                headers=headers,
                timeout=10
            )
            
            # Verificar respuesta
            if response.status_code != 200:
                error_msg = response.text
                self.logger.error(f"❌ Error Schwab OAuth: {response.status_code}")
                self.logger.error(f"   Detalles: {error_msg}")
                return False
            
            # Parsear respuesta JSON
            token_data = response.json()
            
            # Validar datos requeridos
            if 'access_token' not in token_data:
                self.logger.error("❌ No access_token en respuesta Schwab")
                return False
            
            # Guardar token actual
            self.current_token = token_data.get('access_token')
            self.token_expires_in = token_data.get('expires_in', 1800)
            self.token_obtained_at = datetime.now()
            self.token_expires_at = datetime.now() + timedelta(seconds=self.token_expires_in)
            
            # Guardar en archivo
            self._save_token_to_file(token_data)
            
            self.logger.info(f"✅ Token renovado: {self.current_token[:20]}...")
            self.logger.info(f"   Válido por {self.token_expires_in} segundos ({self.token_expires_in/60:.0f} minutos)")
            self.logger.info(f"   Expira en: {self.token_expires_at}")
            
            return True
        
        except requests.exceptions.Timeout:
            self.logger.error("❌ Timeout conectando a Schwab OAuth")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error("❌ Error de conexión a Schwab OAuth")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error renovando token: {e}")
            return False
    
    def _save_token_to_file(self, token_data):
        """
        Guarda token actual en archivo JSON
        
        Args:
            token_data: diccionario con datos del token de Schwab
        """
        try:
            output_data = {
                "access_token": token_data.get('access_token'),
                "token_type": token_data.get('token_type', 'Bearer'),
                "expires_in": token_data.get('expires_in'),
                "scope": token_data.get('scope'),
                "refresh_token": token_data.get('refresh_token', self.refresh_token_value),
                "obtained_at": self.token_obtained_at.isoformat(),
                "expires_at": self.token_expires_at.isoformat()
            }
            
            with open(self.token_output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            self.logger.info(f"✅ Token guardado en {self.token_output_file}")
        
        except Exception as e:
            self.logger.error(f"❌ Error guardando token en archivo: {e}")
            raise
    
    def is_token_valid(self):
        """
        Verifica si token actual es válido
        
        Returns:
            bool: True si es válido, False si está vencido o próximo a expirar
        """
        try:
            if not self.token_expires_at:
                return False
            
            now = datetime.now()
            time_remaining = (self.token_expires_at - now).total_seconds()
            
            is_valid = time_remaining > 300  # Consideramos válido si quedan > 5 min
            
            if is_valid:
                self.logger.debug(f"✅ Token válido por {time_remaining:.0f} segundos ({time_remaining/60:.1f} min)")
            else:
                self.logger.warning(f"⚠️ Token vencido o próximo a expirar ({time_remaining:.0f}s)")
            
            return is_valid
        
        except Exception as e:
            self.logger.error(f"❌ Error verificando token: {e}")
            return False
    
    def get_current_token(self):
        """
        Obtiene token actual, renovando si es necesario
        
        Returns:
            str: Token OAuth2 válido
        """
        try:
            # Si no hay token, generar uno
            if not self.current_token or not self.token_expires_at:
                self.logger.info("🔄 Token no disponible - generando...")
                if not self.refresh_token():
                    raise RuntimeError("❌ No se pudo generar token")
            
            # Si el token está próximo a expirar, renovar
            if not self.is_token_valid():
                self.logger.info("🔄 Token próximo a expirar - renovando...")
                if not self.refresh_token():
                    raise RuntimeError("❌ No se pudo renovar token")
            
            if not self.current_token:
                raise RuntimeError("❌ No hay token disponible")
            
            self.logger.debug(f"📋 Token solicitado: {self.current_token[:20]}...")
            return self.current_token
        
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo token: {e}")
            raise
    
    def get_auth_header(self):
        """
        Obtiene header de autorización para requests
        
        Returns:
            dict: Header con formato Authorization: Bearer {token}
        """
        try:
            token = self.get_current_token()
            
            header = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            self.logger.debug("✅ Header de autorización generado")
            return header
        
        except Exception as e:
            self.logger.error(f"❌ Error generando header: {e}")
            raise
    
    async def start_background_refresh(self, interval_seconds=1500):
        """
        Inicia tarea de renovación en background (asyncio)
        Renueva token cada 25 minutos (1500 segundos)
        
        Args:
            interval_seconds: intervalo de renovación (por defecto 1500 seg = 25 min)
        """
        import asyncio
        
        self.logger.info(f"🔄 Iniciando renovación automática de token cada {interval_seconds}s ({interval_seconds/60:.0f} min)...")
        
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                self.refresh_token()
        
        except asyncio.CancelledError:
            self.logger.info("⚠️ Renovación automática de token cancelada")
        except Exception as e:
            self.logger.error(f"❌ Error en renovación automática: {e}")
            raise


# Función auxiliar para uso standalone
def test_schwab_manager():
    """Prueba el SchwabTokenManager (para debugging)"""
    try:
        manager = SchwabTokenManager(config_path="hub")
        
        # Renovar token
        success = manager.refresh_token()
        if success:
            print(f"\n✅ Token renovado exitosamente:")
            print(f"   Token: {manager.current_token[:30]}...")
            print(f"   Válido: {manager.is_token_valid()}")
            print(f"   Expira en: {manager.token_expires_at}")
            return True
        else:
            print(f"\n❌ Error renovando token")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_schwab_manager()
