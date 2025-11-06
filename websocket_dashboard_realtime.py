"""
WebSocket Dashboard - Real-Time (WEBSOCKET VERDADERO)
Schwab: wss://streamer-api.schwab.com/ws
Coinbase: wss://advanced-trade-ws.coinbase.com
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conexiones WebSocket activas
schwab_clients = set()
coinbase_clients = set()

# Task handles
background_tasks = []

# Estado compartido
state = {
    "schwab": {
        "connected": False,
        "data": [],
        "error": None,
        "last_update": None,
        "ticks": 0
    },
    "coinbase": {
        "connected": False,
        "data": [],
        "error": None,
        "last_update": None,
        "ticks": 0
    }
}


async def stream_schwab_websocket():
    """Conectar WebSocket Schwab y streamear datos en tiempo real"""
    while True:
        try:
            from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
            
            logger.info("🔌 Inicializando Schwab WebSocket...")
            manager = SchwabWebSocketManager(config_path="hub")
            
            # Conectar
            await manager.connect()
            state["schwab"]["connected"] = True
            state["schwab"]["error"] = None
            logger.info("✅ Schwab WebSocket conectado")
            
            # Recibir datos mientras esté conectado
            while manager.connected:
                try:
                    # Obtener datos del queue del manager
                    if hasattr(manager, 'data_queue'):
                        while not manager.data_queue.empty():
                            data = manager.data_queue.get_nowait()
                            state["schwab"]["data"] = data
                            state["schwab"]["ticks"] += 1
                            state["schwab"]["last_update"] = asyncio.get_event_loop().time()
                            
                            # Broadcast a clientes
                            for client in list(schwab_clients):
                                try:
                                    await client.send_json({
                                        "type": "update",
                                        "broker": "schwab",
                                        "data": state["schwab"]
                                    })
                                except:
                                    schwab_clients.discard(client)
                    
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    logger.warning(f"⚠ Error en Schwab loop: {e}")
                    break
        
        except Exception as e:
            state["schwab"]["error"] = str(e)[:100]
            state["schwab"]["connected"] = False
            logger.error(f"❌ Error Schwab WebSocket: {e}")
            await asyncio.sleep(5)


async def stream_coinbase_websocket():
    """Conectar WebSocket Coinbase y streamear datos en tiempo real"""
    while True:
        try:
            from hub.managers.coinbase_websocket_manager import CoinbaseWebSocketManager
            
            logger.info("🔌 Inicializando Coinbase WebSocket...")
            manager = CoinbaseWebSocketManager(config_path="hub")
            
            # Conectar
            await manager.connect()
            state["coinbase"]["connected"] = True
            state["coinbase"]["error"] = None
            logger.info("✅ Coinbase WebSocket conectado")
            
            # Recibir datos mientras esté conectado
            while manager.connected:
                try:
                    # Obtener datos del queue del manager
                    if hasattr(manager, 'data_queue'):
                        while not manager.data_queue.empty():
                            data = manager.data_queue.get_nowait()
                            state["coinbase"]["data"] = data
                            state["coinbase"]["ticks"] += 1
                            state["coinbase"]["last_update"] = asyncio.get_event_loop().time()
                            
                            # Broadcast a clientes
                            for client in list(coinbase_clients):
                                try:
                                    await client.send_json({
                                        "type": "update",
                                        "broker": "coinbase",
                                        "data": state["coinbase"]
                                    })
                                except:
                                    coinbase_clients.discard(client)
                    
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    logger.warning(f"⚠ Error en Coinbase loop: {e}")
                    break
        
        except Exception as e:
            state["coinbase"]["error"] = str(e)[:100]
            state["coinbase"]["connected"] = False
            logger.error(f"❌ Error Coinbase WebSocket: {e}")
            await asyncio.sleep(5)


# ============================================================================
# LIFESPAN MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager para WebSocket real-time"""
    print("\n" + "="*80)
    print("🚀 DASHBOARD REAL-TIME (WEBSOCKET)")
    print("="*80)
    print("\n✅ Abre: http://localhost:8000")
    print("📊 Schwab: wss://streamer-api.schwab.com/ws (REAL-TIME)")
    print("💰 Coinbase: wss://advanced-trade-ws.coinbase.com (REAL-TIME)")
    print("\n" + "="*80 + "\n")
    
    # Iniciar tasks
    task1 = asyncio.create_task(stream_schwab_websocket())
    task2 = asyncio.create_task(stream_coinbase_websocket())
    background_tasks.append(task1)
    background_tasks.append(task2)
    
    yield
    
    # Cleanup
    for task in background_tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def get_page():
    """Página principal"""
    return HTMLResponse(html_content)


@app.websocket("/ws/schwab")
async def websocket_schwab(websocket: WebSocket):
    """WebSocket para Schwab"""
    await websocket.accept()
    schwab_clients.add(websocket)
    logger.info(f"✅ Cliente Schwab conectado ({len(schwab_clients)} total)")
    
    await websocket.send_json({
        "type": "init",
        "broker": "schwab",
        "data": state["schwab"]
    })
    
    try:
        while True:
            await websocket.receive_text()
    except:
        schwab_clients.discard(websocket)


@app.websocket("/ws/coinbase")
async def websocket_coinbase(websocket: WebSocket):
    """WebSocket para Coinbase"""
    await websocket.accept()
    coinbase_clients.add(websocket)
    logger.info(f"✅ Cliente Coinbase conectado ({len(coinbase_clients)} total)")
    
    await websocket.send_json({
        "type": "init",
        "broker": "coinbase",
        "data": state["coinbase"]
    })
    
    try:
        while True:
            await websocket.receive_text()
    except:
        coinbase_clients.discard(websocket)


html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Real-Time WebSocket Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Monaco', 'Courier', monospace;
            background: #0a0e27;
            color: #00ff00;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5em; color: #00ff00; }
        .header p { color: #888; }
        .brokers {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .broker-card {
            background: #1a1f3a;
            border: 2px solid #00ff00;
            border-radius: 5px;
            padding: 20px;
            font-family: 'Monaco', monospace;
            font-size: 12px;
        }
        .broker-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 10px;
        }
        .broker-header h2 {
            font-size: 1.5em;
            color: #00ff00;
        }
        .status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 1s infinite;
        }
        .status.connected { background: #00ff00; }
        .status.disconnected { background: #ff0000; animation: none; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        .stats {
            background: #0a0e27;
            border: 1px solid #00ff00;
            padding: 10px;
            margin-bottom: 15px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
        }
        .stat-label { color: #888; }
        .stat-value { color: #00ff00; font-weight: bold; }
        .data-display {
            background: #0a0e27;
            border: 1px solid #00ff00;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .error { color: #ff0000; }
        .loading { color: #888; }
        @media (max-width: 1024px) { .brokers { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ REAL-TIME WEBSOCKET DASHBOARD</h1>
            <p>Schwab + Coinbase | Live Stream | <500ms latency</p>
        </div>
        
        <div class="brokers">
            <!-- SCHWAB -->
            <div class="broker-card">
                <div class="broker-header">
                    <h2>📊 SCHWAB</h2>
                    <div class="status disconnected" id="schwab-status"></div>
                </div>
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value" id="schwab-status-text">WAITING</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Ticks:</span>
                        <span class="stat-value" id="schwab-ticks">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Last Update:</span>
                        <span class="stat-value" id="schwab-time">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">URL:</span>
                        <span class="stat-value">wss://streamer-api.schwab.com/ws</span>
                    </div>
                </div>
                <div class="data-display" id="schwab-data">
                    <span class="loading">Connecting to WebSocket...</span>
                </div>
            </div>
            
            <!-- COINBASE -->
            <div class="broker-card">
                <div class="broker-header">
                    <h2>💰 COINBASE</h2>
                    <div class="status disconnected" id="coinbase-status"></div>
                </div>
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value" id="coinbase-status-text">WAITING</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Ticks:</span>
                        <span class="stat-value" id="coinbase-ticks">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Last Update:</span>
                        <span class="stat-value" id="coinbase-time">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">URL:</span>
                        <span class="stat-value">wss://advanced-trade-ws.coinbase.com</span>
                    </div>
                </div>
                <div class="data-display" id="coinbase-data">
                    <span class="loading">Connecting to WebSocket...</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Schwab WebSocket
        const schwabWs = new WebSocket("ws://localhost:8000/ws/schwab");
        let schwabTicks = 0;
        let schwabLastUpdate = null;
        
        schwabWs.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            const data = msg.data;
            
            document.getElementById("schwab-status").className = "status " + (data.connected ? "connected" : "disconnected");
            document.getElementById("schwab-status-text").textContent = data.connected ? "CONNECTED" : "DISCONNECTED";
            document.getElementById("schwab-ticks").textContent = data.ticks;
            document.getElementById("schwab-time").textContent = new Date().toLocaleTimeString();
            
            if (data.error) {
                document.getElementById("schwab-data").innerHTML = `<span class="error">ERROR: ${data.error}</span>`;
            } else if (data.data && data.data.length > 0) {
                document.getElementById("schwab-data").textContent = JSON.stringify(data.data, null, 2).substring(0, 1000);
            }
        };
        
        // Coinbase WebSocket
        const coinbaseWs = new WebSocket("ws://localhost:8000/ws/coinbase");
        
        coinbaseWs.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            const data = msg.data;
            
            document.getElementById("coinbase-status").className = "status " + (data.connected ? "connected" : "disconnected");
            document.getElementById("coinbase-status-text").textContent = data.connected ? "CONNECTED" : "DISCONNECTED";
            document.getElementById("coinbase-ticks").textContent = data.ticks;
            document.getElementById("coinbase-time").textContent = new Date().toLocaleTimeString();
            
            if (data.error) {
                document.getElementById("coinbase-data").innerHTML = `<span class="error">ERROR: ${data.error}</span>`;
            } else if (data.data && data.data.length > 0) {
                document.getElementById("coinbase-data").textContent = JSON.stringify(data.data, null, 2).substring(0, 1000);
            }
        };
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
