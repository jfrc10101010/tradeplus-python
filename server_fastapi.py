"""
╔═══════════════════════════════════════════════════════════════╗
║     TRADEPLUS V5.1 - FastAPI Backend con WebSocket          ║
║     Arquitectura correcta: Python permanente + WS push      ║
║     Puerto: 8080 | PM2: "tradeplus-fastapi"                 ║
╚═══════════════════════════════════════════════════════════════╝

MEJORAS vs server.js:
- ✅ Sin subprocess: Backend permanente
- ✅ Cache pre-calculado: Respuesta <50ms
- ✅ WebSocket push: Updates automáticos cada 5s
- ✅ CORS habilitado para desarrollo
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Importar journal manager
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'hub')))
from journal.journal_manager import JournalManager

# ========================================================================
# FASTAPI APP
# ========================================================================

app = FastAPI(
    title="TradePlus API",
    version="5.1.0",
    description="Multi-broker trading journal with real-time WebSocket updates"
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# CACHE GLOBAL
# ========================================================================

class JournalCache:
    """Cache global actualizado en background"""
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {
            'all_7': None,
            'all_30': None,
            'all_90': None,
            'schwab_7': None,
            'schwab_30': None,
            'schwab_90': None,
            'coinbase_7': None,
            'coinbase_30': None,
            'coinbase_90': None,
        }
        self.last_update = None
        self.manager = JournalManager(capital_initial=5000.0)
        self.updating = False
        
    async def update_all(self):
        """Actualizar todo el cache"""
        if self.updating:
            logger.warning("⚠️ Update already in progress, skipping")
            return
            
        self.updating = True
        try:
            logger.info("🔄 Actualizando cache...")
            start = datetime.now()
            
            # Actualizar cada período en paralelo
            tasks = []
            for days in [7, 30, 90]:
                tasks.append(self._update_period(days))
            
            await asyncio.gather(*tasks)
            
            self.last_update = datetime.now()
            elapsed = (datetime.now() - start).total_seconds()
            logger.info(f"✅ Cache actualizado en {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando cache: {e}")
        finally:
            self.updating = False
    
    async def _update_period(self, days: int):
        """Actualizar un período específico"""
        try:
            # Ejecutar en thread pool para no bloquear event loop
            loop = asyncio.get_event_loop()
            
            # Combinado (all)
            all_data = await loop.run_in_executor(
                None, 
                lambda: self.manager.get_combined_journal(days=days)
            )
            self.cache[f'all_{days}'] = all_data
            
            # Schwab
            schwab_data = await loop.run_in_executor(
                None,
                lambda: self.manager.get_trades_by_broker('schwab', days=days)
            )
            self.cache[f'schwab_{days}'] = schwab_data
            
            # Coinbase
            coinbase_data = await loop.run_in_executor(
                None,
                lambda: self.manager.get_trades_by_broker('coinbase', days=days)
            )
            self.cache[f'coinbase_{days}'] = coinbase_data
            
            logger.info(f"  ✓ Período {days}d actualizado")
            
        except Exception as e:
            logger.error(f"❌ Error en período {days}d: {e}")
    
    def get(self, broker: str, days: int) -> Optional[Dict]:
        """Obtener datos del cache"""
        key = f'{broker}_{days}'
        return self.cache.get(key)

# Instancia global del cache
cache = JournalCache()

# ========================================================================
# BACKGROUND TASKS
# ========================================================================

async def update_cache_loop():
    """Loop infinito que actualiza cache cada 30s"""
    logger.info("🚀 Background cache updater iniciado")
    
    # Primera actualización inmediata
    await cache.update_all()
    
    while True:
        try:
            await asyncio.sleep(30)  # Esperar 30 segundos
            await cache.update_all()
        except Exception as e:
            logger.error(f"❌ Error en update loop: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Iniciar background tasks al arrancar"""
    logger.info("=" * 80)
    logger.info("🚀 TradePlus FastAPI Server iniciando...")
    logger.info("=" * 80)
    
    # Crear task para actualizar cache
    asyncio.create_task(update_cache_loop())
    
    logger.info("✅ Server listo")

# ========================================================================
# WEBSOCKET ENDPOINTS
# ========================================================================

class ConnectionManager:
    """Gestiona conexiones WebSocket activas"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 Cliente conectado. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"🔌 Cliente desconectado. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error enviando a cliente: {e}")
                dead_connections.append(connection)
        
        # Limpiar conexiones muertas
        for conn in dead_connections:
            self.active_connections.remove(conn)

manager = ConnectionManager()

@app.websocket("/ws/journal")
async def websocket_journal(websocket: WebSocket):
    """
    WebSocket principal - Envía updates automáticos
    
    Protocolo:
    - Cliente envía: {"broker": "all"|"schwab"|"coinbase", "days": 7|30|90}
    - Server responde: JSON con datos completos del journal
    - Server push: Cada 5s mientras el cache se actualice
    """
    await manager.connect(websocket)
    
    try:
        # Configuración inicial
        current_broker = 'all'
        current_days = 30
        
        # Enviar datos iniciales
        initial_data = cache.get(current_broker, current_days)
        if initial_data:
            await websocket.send_json({
                'type': 'initial',
                'data': initial_data,
                'broker': current_broker,
                'days': current_days
            })
        
        while True:
            # Esperar mensajes del cliente (cambios de filtro)
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
                
                # Cliente cambió filtro
                if 'broker' in message:
                    current_broker = message['broker']
                if 'days' in message:
                    current_days = int(message['days'])
                
                logger.info(f"📡 Cliente solicitó: {current_broker} / {current_days}d")
                
                # Enviar datos actualizados
                data = cache.get(current_broker, current_days)
                if data:
                    await websocket.send_json({
                        'type': 'update',
                        'data': data,
                        'broker': current_broker,
                        'days': current_days,
                        'cached_at': cache.last_update.isoformat() if cache.last_update else None
                    })
                
            except asyncio.TimeoutError:
                # Timeout - enviar update periódico
                data = cache.get(current_broker, current_days)
                if data:
                    await websocket.send_json({
                        'type': 'periodic',
                        'data': data,
                        'broker': current_broker,
                        'days': current_days,
                        'cached_at': cache.last_update.isoformat() if cache.last_update else None
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
        manager.disconnect(websocket)

# ========================================================================
# REST API ENDPOINTS (Compatibilidad con frontend antiguo)
# ========================================================================

@app.get("/api/journal")
async def get_journal(days: int = 30):
    """GET /api/journal?days=30 - Journal combinado"""
    logger.info(f"📊 GET /api/journal?days={days}")
    
    data = cache.get('all', days)
    if data:
        return JSONResponse(content=data)
    
    # Fallback: computar en el momento
    logger.warning(f"⚠️ Cache miss, computando {days}d...")
    try:
        result = cache.manager.get_combined_journal(days=days)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/journal/broker/{broker}")
async def get_journal_by_broker(broker: str, days: int = 7):
    """GET /api/journal/broker/schwab?days=7"""
    logger.info(f"📊 GET /api/journal/broker/{broker}?days={days}")
    
    data = cache.get(broker, days)
    if data:
        return JSONResponse(content=data)
    
    # Fallback
    logger.warning(f"⚠️ Cache miss, computando {broker} {days}d...")
    try:
        result = cache.manager.get_trades_by_broker(broker, days=days)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'ok',
        'version': '5.1.0',
        'cache_last_update': cache.last_update.isoformat() if cache.last_update else None,
        'cache_updating': cache.updating
    }

# ========================================================================
# STATIC FILES
# ========================================================================

# Servir archivos estáticos del directorio test/public
app.mount("/static", StaticFiles(directory="test/public"), name="static")

@app.get("/")
async def root():
    """Redirigir a /journal.html"""
    return FileResponse("test/public/journal.html")

@app.get("/journal")
@app.get("/journal.html")
async def journal_page():
    """Servir página principal"""
    return FileResponse("test/public/journal.html")

# ========================================================================
# MAIN
# ========================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server_fastapi:app",
        host="0.0.0.0",
        port=8080,
        reload=False,  # Disable reload en producción
        log_level="info"
    )
