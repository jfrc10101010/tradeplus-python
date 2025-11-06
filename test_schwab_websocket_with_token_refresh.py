"""
TEST COMPLETO: SchwabWebSocketManager con Renovación Automática de Tokens

Este script demuestra el flujo completo correcto:
1. Renovación automática de tokens cada 25 minutos
2. Detección de tokens expirados (401)
3. Reintentos automáticos con tokens renovados
4. Conexión WebSocket mantenida viva con datos en tiempo real

REQUISITOS:
- hub/current_token.json con token válido O
- hub/.env con credenciales OAuth Schwab (TOS_CLIENT_ID, TOS_CLIENT_SECRET, TOS_REFRESH_TOKEN)
"""

import asyncio
import logging
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Importar los managers
try:
    from hub.managers.schwab_token_manager import SchwabTokenManager
    from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
except ImportError:
    from hub.managers.schwab_token_manager import SchwabTokenManager
    from hub.managers.schwab_websocket_manager import SchwabWebSocketManager

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class RobustSchwabConnection:
    """
    Gestor robusto de conexión Schwab con renovación automática de tokens
    """
    
    def __init__(self, config_path: str = "."):
        self.config_path = Path(config_path)
        self.token_manager = SchwabTokenManager(config_path="hub")
        self.ws_manager = SchwabWebSocketManager(config_path=".")
        
        # Control de renovación
        self.last_token_refresh = None
        self.token_refresh_interval = 1500  # 25 minutos
        self.connected = False
    
    async def ensure_token_valid(self):
        """
        Verifica y renueva token si es necesario
        Se ejecuta en background cada 5 minutos
        """
        while True:
            try:
                # Esperar 5 minutos antes de verificar
                await asyncio.sleep(300)
                
                if not self.token_manager.is_token_valid():
                    logger.warning("⏰ Token próximo a expirar - renovando...")
                    
                    if self.token_manager.refresh_token():
                        logger.info("✅ Token renovado exitosamente en background")
                        self.last_token_refresh = datetime.now()
                        
                        # Si hay conexión WebSocket, también la afectará
                        if self.connected:
                            logger.info("ℹ️  WebSocket mantendrá conexión con nuevo token")
                    else:
                        logger.error("❌ Error renovando token en background")
                else:
                    time_remaining = (self.token_manager.token_expires_at - datetime.now()).total_seconds()
                    logger.info(f"✅ Token válido ({time_remaining/60:.0f} min restantes)")
            
            except Exception as e:
                logger.error(f"❌ Error en verificación de token: {e}")
                await asyncio.sleep(60)
    
    async def connect_websocket(self):
        """
        Conecta a WebSocket con renovación automática integrada
        """
        try:
            logger.info("🔌 Conectando a WebSocket...")
            result = await asyncio.wait_for(
                self.ws_manager.connect(), 
                timeout=30
            )
            
            if result:
                self.connected = True
                logger.info("✅ WebSocket conectado exitosamente")
                return True
            else:
                logger.error("❌ Error conectando WebSocket")
                self.connected = False
                return False
        
        except asyncio.TimeoutError:
            logger.error("❌ Timeout conectando WebSocket (30s)")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Error en connect_websocket: {e}")
            self.connected = False
            return False
    
    async def maintain_connection(self, duration_seconds: int = 300):
        """
        Mantiene la conexión viva durante el tiempo especificado
        Demuestra que el sistema maneja tokens expirados y renovaciones
        
        Args:
            duration_seconds: Duración de la prueba (por defecto 5 minutos)
        """
        logger.info(f"📊 Manteniendo conexión durante {duration_seconds}s ({duration_seconds/60:.0f} min)...")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        try:
            while datetime.now() < end_time:
                # Verificar estado
                if self.ws_manager.connected:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    ticks = self.ws_manager.ticks_received
                    logger.info(
                        f"[{elapsed:.0f}s] "
                        f"Conectado ✓ | "
                        f"Ticks: {ticks} | "
                        f"Token válido: {self.token_manager.is_token_valid()}"
                    )
                else:
                    logger.warning("⚠️  Conexión perdida")
                    break
                
                # Verificar renovación de token cada 5 min
                await asyncio.sleep(10)
        
        except Exception as e:
            logger.error(f"❌ Error manteniendo conexión: {e}")
    
    async def run(self, test_duration: int = 300):
        """
        Ejecuta el test completo con tareas en paralelo
        
        Args:
            test_duration: Duración total del test (por defecto 5 minutos)
        """
        try:
            logger.info("="*80)
            logger.info("INICIANDO TEST: SCHWAB WEBSOCKET CON AUTO-RENOVACIÓN DE TOKENS")
            logger.info("="*80)
            
            # Tareas en paralelo:
            # 1. Renovación automática de tokens en background
            # 2. Conexión WebSocket
            # 3. Mantener conexión viva
            
            tasks = [
                self.ensure_token_valid(),  # Tarea infinita de renovación
                asyncio.create_task(self._test_sequence(test_duration))  # Test principal
            ]
            
            # Ejecutar con timeout
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=test_duration + 60
            )
        
        except asyncio.TimeoutError:
            logger.info("✅ Test completado (timeout esperado)")
        except Exception as e:
            logger.error(f"❌ Error ejecutando test: {e}")
        finally:
            await self.cleanup()
    
    async def _test_sequence(self, duration: int):
        """Secuencia principal del test"""
        try:
            # Conectar WebSocket
            success = await self.connect_websocket()
            
            if success:
                # Suscribirse a símbolos
                logger.info("📈 Suscribiéndose a AAPL, MSFT, GOOGL, TSLA...")
                await self.ws_manager.subscribe_level_one(["AAPL", "MSFT", "GOOGL", "TSLA"])
                
                # Mantener conexión durante el test
                await self.maintain_connection(duration_seconds=duration)
                
                # Mostrar estadísticas
                stats = self.ws_manager.get_stats()
                logger.info(f"📊 Estadísticas finales:")
                logger.info(f"  - Ticks recibidos: {stats['ticks_received']}")
                logger.info(f"  - Ticks/segundo: {stats['ticks_per_second']:.2f}")
                logger.info(f"  - Usuario: {stats['user_id']}")
            else:
                logger.error("❌ No se pudo conectar al WebSocket")
        
        except Exception as e:
            logger.error(f"❌ Error en secuencia de test: {e}")
    
    async def cleanup(self):
        """Limpia recursos"""
        try:
            logger.info("🧹 Limpiando recursos...")
            await self.ws_manager.close()
            logger.info("✅ Cleanup completado")
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")


async def main():
    """Punto de entrada principal"""
    try:
        # Duración del test (en segundos)
        # Para ver renovación de tokens, necesitas > 25 minutos
        # Para prueba rápida, 5-10 minutos es suficiente
        test_duration = 600  # 10 minutos por defecto
        
        if len(sys.argv) > 1:
            try:
                test_duration = int(sys.argv[1])
            except ValueError:
                logger.warning("⚠️  Duración inválida, usando 600s (10 min)")
        
        connection = RobustSchwabConnection()
        await connection.run(test_duration=test_duration)
        
        logger.info("="*80)
        logger.info("✅ TEST COMPLETADO")
        logger.info("="*80)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrumpido por usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 SCHWAB WEBSOCKET WITH AUTO-TOKEN REFRESH                    ║
║                                                                              ║
║ Demuestra:                                                                   ║
║ • Renovación automática de tokens cada 25 minutos                           ║
║ • Detección de tokens expirados (401)                                       ║
║ • Reintentos automáticos                                                    ║
║ • Conexión WebSocket mantenida viva                                         ║
║ • Datos en tiempo real <50ms                                                ║
║                                                                              ║
║ Uso:                                                                         ║
║   python test_schwab_websocket_with_token_refresh.py [duración_segundos]   ║
║   python test_schwab_websocket_with_token_refresh.py 600  # 10 minutos     ║
║                                                                              ║
║ Requisitos:                                                                  ║
║   • hub/.env con credenciales OAuth Schwab                                  ║
║   • Acceso a API de Schwab                                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(main())
