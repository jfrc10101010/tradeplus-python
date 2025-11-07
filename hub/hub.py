"""
Hub Central - Orquestador de WebSockets privados de Coinbase + Schwab
Recibe ticks REALES, calcula filtros, emite vía WebSocket a UI
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importar managers
from hub.managers.coinbase_websocket_manager import CoinbaseWebSocketManager
from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
from hub.journal.journal_manager import JournalManager


# =====================================================
# FILTROS TÉCNICOS - Se calculan UNA sola vez
# =====================================================

class TechnicalFilters:
    """Calcula RSI, EMA, Fibonacci - UNA SOLA VEZ por tick"""
    
    @staticmethod
    def calculate_rsi(prices: list, period: int = 14) -> Optional[float]:
        """Calcula RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        seed = deltas[:period]
        up = sum(d for d in seed if d > 0) / period
        down = sum(-d for d in seed if d < 0) / period
        
        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs >= 0 else 0
        return rsi
    
    @staticmethod
    def calculate_ema(prices: list, period: int = 20) -> Optional[float]:
        """Calcula EMA (Exponential Moving Average)"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = price * multiplier + ema * (1 - multiplier)
        
        return ema
    
    @staticmethod
    def calculate_fibonacci_pivot(high: float, low: float, close: float) -> Dict[str, float]:
        """Calcula niveles de Fibonacci"""
        p = (high + low + close) / 3
        
        return {
            'pivot': p,
            'r1': p + (high - low) * 0.382,
            'r2': p + (high - low) * 0.618,
            's1': p - (high - low) * 0.382,
            's2': p - (high - low) * 0.618,
        }


# =====================================================
# HUB CENTRAL - Orquestador
# =====================================================

class HubCentral:
    """Orquestador central que recibe ticks de ambos brokers"""
    
    def __init__(self, config_path: str = "."):
        """
        Inicializa Hub Central
        
        Args:
            config_path: ruta a carpeta de configuración (JWT, tokens)
        """
        self.config_path = Path(config_path)
        
        # Logger - se inicializa primero
        self.logger = self._setup_logger()
        
        # Managers de WebSocket
        self.coinbase_manager = CoinbaseWebSocketManager(
            config_path=config_path,
            product_ids=["BTC-USD", "ETH-USD"]
        )
        self.schwab_manager = SchwabWebSocketManager(
            config_path=str(self.config_path)
        )
        
        # Journal Manager (con managers de tokens)
        try:
            self.journal_manager = JournalManager(
                self.schwab_manager.token_manager,
                None,  # Coinbase JWT será creado internamente por JournalManager
                config_path=config_path
            )
        except Exception as e:
            self.logger.warning(f"⚠️ Error inicializando JournalManager: {e}")
            self.journal_manager = None
        
        # Almacenamiento en memoria
        self.last_ticks = {}  # {symbol: {price, bid, ask, time, ...}}
        self.price_history = {}  # {symbol: [prices]}
        self.max_history_size = 100
        
        # Estadísticas
        self.total_ticks = 0
        self.start_time = time.time()
        
        # WebSocket clients conectados
        self.ws_clients = set()
        
        self.logger.info("✅ HubCentral inicializado")
    
    def _setup_logger(self):
        """Configura logger del hub"""
        logger = logging.getLogger("HubCentral")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    async def connect_all(self) -> bool:
        """
        Inicializa managers SIN ejecutar loops infinitos en lifespan
        Los managers se conectarán bajo demanda cuando se acceda a /ws/live
        
        Returns:
            True siempre (inicialización lista)
        """
        self.logger.info("🚀 Managers inicializados - listos para conexión bajo demanda")
        return True
    
    async def start_receiving(self):
        """
        Los managers ya están recibiendo en sus propios loops async.
        Este método es para mantener el hub activo y monitorear estadísticas.
        """
        self.logger.info("📡 Hub Central activo y recibiendo ticks...")
        
        try:
            # Loop de monitoreo - simplemente espera indefinidamente
            # Los managers siguen recibiendo en paralelo
            while True:
                await asyncio.sleep(10)
                
                # Cada 10s, log de estadísticas
                stats = self.get_stats()
                if stats['total_ticks'] % 10 == 0 and stats['total_ticks'] > 0:
                    self.logger.debug(
                        f"📊 Stats: {stats['total_ticks']} ticks, "
                        f"{stats['ticks_per_second']:.1f} tps, "
                        f"{stats['unique_symbols']} símbolos"
                    )
        
        except asyncio.CancelledError:
            self.logger.info("⏹️ Hub monitoring cancelado")
        except Exception as e:
            self.logger.error(f"❌ Error en monitoring: {e}")
    

    async def _coinbase_receiver(self):
        """DEPRECATED - Los managers reciben internamente"""
        pass
    
    async def _schwab_receiver(self):
        """DEPRECATED - Los managers reciben internamente"""
        pass
    
    async def _process_tick(self, symbol: str, tick: Dict[str, Any], source: str):
        """
        DEPRECATED - Lógica movida a los managers
        Se mantiene para referencia
        """
        pass
    
    def _calculate_filters_once(self, symbol: str) -> Dict[str, Any]:
        """DEPRECATED"""
        pass
    
    async def _broadcast(self, message: Dict[str, Any]):
        """Emite mensaje a todos los clientes WebSocket conectados"""
        if not self.ws_clients:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for client in self.ws_clients:
            try:
                await client.send_text(message_json)
            except Exception as e:
                self.logger.warning(f"⚠️ Error enviando a cliente: {e}")
                disconnected.add(client)
        
        # Limpiar desconectados
        self.ws_clients -= disconnected
    
    async def add_ws_client(self, websocket: WebSocket):
        """Registra nuevo cliente WebSocket"""
        self.ws_clients.add(websocket)
        self.logger.info(f"✅ Cliente conectado ({len(self.ws_clients)} total)")
    
    async def remove_ws_client(self, websocket: WebSocket):
        """Desregistra cliente WebSocket"""
        self.ws_clients.discard(websocket)
        self.logger.info(f"🔌 Cliente desconectado ({len(self.ws_clients)} total)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del hub"""
        elapsed = time.time() - self.start_time
        
        return {
            'uptime_seconds': elapsed,
            'total_ticks': self.total_ticks,
            'ticks_per_second': self.total_ticks / elapsed if elapsed > 0 else 0,
            'unique_symbols': len(self.last_ticks),
            'ws_clients_connected': len(self.ws_clients),
            'coinbase_connected': self.coinbase_manager.connected,
            'schwab_connected': self.schwab_manager.connected,
            'coinbase_ticks': self.coinbase_manager.ticks_received,
            'schwab_ticks': self.schwab_manager.ticks_received,
        }
    
    def is_connected(self) -> bool:
        """Retorna True si al menos un manager está conectado"""
        return self.coinbase_manager.connected or self.schwab_manager.connected
    
    def get_latest_ticks(self, limit: int = 10) -> list:
        """Retorna los últimos ticks (formato para streaming)"""
        ticks = []
        for symbol, tick in list(self.last_ticks.items())[:limit]:
            if 'source' not in tick:
                # Determinar fuente
                if any(x in symbol for x in ['BTC', 'ETH']):
                    tick['source'] = 'coinbase'
                else:
                    tick['source'] = 'schwab'
            ticks.append(tick)
        return ticks
    
    @property
    def managers(self) -> Dict[str, Dict[str, Any]]:
        """Retorna estado de los managers"""
        return {
            'coinbase': {
                'connected': self.coinbase_manager.connected,
                'ticks_received': self.coinbase_manager.ticks_received
            },
            'schwab': {
                'connected': self.schwab_manager.connected,
                'ticks_received': self.schwab_manager.ticks_received
            }
        }
    
    async def close_all(self):
        """Cierra todos los managers"""
        self.logger.info("⏹️ Cerrando HubCentral...")
        
        await self.coinbase_manager.close()
        await self.schwab_manager.close()
        
        self.logger.info("✅ HubCentral cerrado")


# =====================================================
# FASTAPI APP
# =====================================================

hub_instance: Optional[HubCentral] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan - inicializa HubCentral y mantiene app corriendo"""
    global hub_instance
    
    # Startup
    try:
        hub_instance = HubCentral(config_path=".")
        print("[INFO] HubCentral inicializado en lifespan")
    except Exception as e:
        print(f"[ERROR] Error en lifespan startup: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        yield
    finally:
        # Shutdown - aquí iría cleanup si fuera necesario
        pass


app = FastAPI(
    title="TradePlus Hub - WebSocket Privado",
    description="Orquestador de WebSockets privados/autenticados de Coinbase + Schwab",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# ENDPOINTS
# =====================================================

@app.get("/health")
async def health():
    """Health check"""
    if not hub_instance:
        return {"status": "not_initialized"}
    
    stats = hub_instance.get_stats()
    return {
        "status": "healthy",
        "stats": stats
    }


@app.get("/stats")
async def stats():
    """Estadísticas del hub"""
    if not hub_instance:
        return {"error": "Hub not initialized"}
    
    return hub_instance.get_stats()


@app.get("/ticks")
async def get_ticks():
    """Último tick de cada símbolo"""
    if not hub_instance:
        return {"error": "Hub not initialized"}
    
    return hub_instance.last_ticks


@app.websocket("/ws/journal")
async def websocket_journal(websocket: WebSocket):
    """
    WebSocket para Journal de Trades
    
    Cliente envía JSON:
        {
            "action": "get_journal",
            "broker": "schwab" o "coinbase",
            "days": 30
        }
    
    Servidor responde con:
        {
            "trades": [...],
            "stats": {...},
            "broker": broker,
            "days": days
        }
    """
    await websocket.accept()
    await hub_instance.add_ws_client(websocket)
    
    try:
        while True:
            # Recibir comando del cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action", "get_journal")
            broker = message.get("broker", "schwab").lower()
            days = message.get("days", 30)
            
            if action == "get_journal":
                if not hub_instance or not hub_instance.journal_manager:
                    await websocket.send_json({
                        "error": "Hub not initialized",
                        "trades": [],
                        "stats": {}
                    })
                    continue
                
                try:
                    trades = await hub_instance.journal_manager.get_journal(broker, days)
                    stats = hub_instance.journal_manager.calculate_stats(trades)
                    
                    await websocket.send_json({
                        "trades": trades,
                        "stats": stats,
                        "broker": broker,
                        "days": days
                    })
                except Exception as e:
                    await websocket.send_json({
                        "error": str(e),
                        "trades": [],
                        "stats": {}
                    })
            else:
                await websocket.send_json({
                    "error": f"Unknown action: {action}"
                })
    
    except WebSocketDisconnect:
        await hub_instance.remove_ws_client(websocket)
    except Exception as e:
        hub_instance.logger.error(f"WebSocket error: {e}")
        await hub_instance.remove_ws_client(websocket)


@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """WebSocket para recibir ticks en tiempo real"""
    await websocket.accept()
    
    try:
        # Registrar cliente
        await hub_instance.add_ws_client(websocket)
        
        # Mantener conexión abierta
        while True:
            # Escuchar mensajes del cliente (para commands futuros)
            data = await websocket.receive_text()
            
            # Por ahora, solo recibe. En futuro puede enviar commands
            if data == "stats":
                stats = hub_instance.get_stats()
                await websocket.send_json({
                    'type': 'stats',
                    'data': stats
                })
    
    except WebSocketDisconnect:
        await hub_instance.remove_ws_client(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await hub_instance.remove_ws_client(websocket)
