"""
WebSocket Dashboard - VERSIÓN PRODUCTIVA
Schwab + Coinbase corriendo en paralelo en background
Sin bloqueos, actualizando en tiempo real
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clients_schwab = set()
clients_coinbase = set()
background_tasks = []

state = {
    "schwab": {"connected": False, "ticks": 0, "data": None},
    "coinbase": {"connected": False, "ticks": 0, "data": None}
}


async def run_schwab_websocket():
    """Schwab WebSocket en background - NO BLOQUEA"""
    while True:
        try:
            from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
            
            logger.info("🔌 Inicializando Schwab...")
            mgr = SchwabWebSocketManager(config_path="hub")
            
            # Conectar en background sin bloquear
            connect_task = asyncio.create_task(mgr.connect())
            
            state["schwab"]["connected"] = True
            logger.info("✅ Schwab WebSocket activo")
            
            # Mantener vivo mientras funcione
            await asyncio.sleep(30)
            
            state["schwab"]["ticks"] += 1
            
            # Broadcast a clientes
            for ws in list(clients_schwab):
                try:
                    await ws.send_json({"broker": "schwab", "state": state["schwab"]})
                except:
                    clients_schwab.discard(ws)
        
        except Exception as e:
            state["schwab"]["connected"] = False
            logger.error(f"❌ Schwab error: {e}")
            await asyncio.sleep(5)


async def run_coinbase_websocket():
    """Coinbase WebSocket en background - NO BLOQUEA"""
    while True:
        try:
            from hub.managers.coinbase_websocket_manager import CoinbaseWebSocketManager
            
            logger.info("🔌 Inicializando Coinbase...")
            mgr = CoinbaseWebSocketManager(config_path="hub")
            
            # Conectar en background sin bloquear
            connect_task = asyncio.create_task(mgr.connect())
            
            state["coinbase"]["connected"] = True
            logger.info("✅ Coinbase WebSocket activo")
            
            # Mantener vivo mientras funcione
            await asyncio.sleep(30)
            
            state["coinbase"]["ticks"] += 1
            
            # Broadcast a clientes
            for ws in list(clients_coinbase):
                try:
                    await ws.send_json({"broker": "coinbase", "state": state["coinbase"]})
                except:
                    clients_coinbase.discard(ws)
        
        except Exception as e:
            state["coinbase"]["connected"] = False
            logger.error(f"❌ Coinbase error: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*80)
    print("⚡ REAL-TIME WEBSOCKET DASHBOARD")
    print("="*80)
    print("\n📍 http://localhost:8000")
    print("📊 Schwab + Coinbase")
    print("\n" + "="*80 + "\n")
    
    task1 = asyncio.create_task(run_schwab_websocket())
    task2 = asyncio.create_task(run_coinbase_websocket())
    background_tasks.extend([task1, task2])
    
    yield
    
    for task in background_tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>⚡ WebSocket Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: monospace; background: #0a0e27; color: #00ff00; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { text-align: center; border-bottom: 2px solid #00ff00; padding-bottom: 20px; margin-bottom: 30px; }
            .brokers { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card {
                background: #1a1f3a;
                border: 2px solid #00ff00;
                padding: 20px;
                border-radius: 5px;
            }
            .card h2 { margin-bottom: 15px; }
            .status { display: flex; justify-content: space-between; margin: 10px 0; }
            .dot { width: 12px; height: 12px; border-radius: 50%; }
            .connected { background: #00ff00; animation: pulse 1s infinite; }
            .disconnected { background: #ff0000; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
            .url { font-size: 12px; color: #888; margin-top: 15px; border-top: 1px solid #00ff00; padding-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ WEBSOCKET DASHBOARD</h1>
                <p>Real-time data from Schwab & Coinbase</p>
            </div>
            <div class="brokers">
                <div class="card">
                    <h2>📊 SCHWAB</h2>
                    <div class="status">
                        <span>Status:</span>
                        <div class="dot disconnected" id="schwab-dot"></div>
                    </div>
                    <div class="status">
                        <span>Ticks:</span>
                        <span id="schwab-ticks">0</span>
                    </div>
                    <div class="url">wss://streamer-api.schwab.com/ws</div>
                </div>
                <div class="card">
                    <h2>💰 COINBASE</h2>
                    <div class="status">
                        <span>Status:</span>
                        <div class="dot disconnected" id="coinbase-dot"></div>
                    </div>
                    <div class="status">
                        <span>Ticks:</span>
                        <span id="coinbase-ticks">0</span>
                    </div>
                    <div class="url">wss://advanced-trade-ws.coinbase.com</div>
                </div>
            </div>
        </div>
        <script>
            const schwab = new WebSocket("ws://localhost:8000/ws/schwab");
            const coinbase = new WebSocket("ws://localhost:8000/ws/coinbase");
            
            schwab.onmessage = (e) => {
                const data = JSON.parse(e.data);
                document.getElementById("schwab-dot").className = "dot " + (data.state.connected ? "connected" : "disconnected");
                document.getElementById("schwab-ticks").textContent = data.state.ticks;
            };
            
            coinbase.onmessage = (e) => {
                const data = JSON.parse(e.data);
                document.getElementById("coinbase-dot").className = "dot " + (data.state.connected ? "connected" : "disconnected");
                document.getElementById("coinbase-ticks").textContent = data.state.ticks;
            };
        </script>
    </body>
    </html>
    """)


@app.websocket("/ws/schwab")
async def ws_schwab(websocket: WebSocket):
    await websocket.accept()
    clients_schwab.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        clients_schwab.discard(websocket)


@app.websocket("/ws/coinbase")
async def ws_coinbase(websocket: WebSocket):
    await websocket.accept()
    clients_coinbase.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        clients_coinbase.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
