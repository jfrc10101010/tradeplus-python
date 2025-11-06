"""
DASHBOARD REAL-TIME 100% WEBSOCKET
Cero polling HTTP. Datos capturados AL INSTANTE cuando llegan.
Schwab: wss://streamer-api.schwab.com/ws
Coinbase: wss://advanced-trade-ws.coinbase.com
"""
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from collections import deque
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Clientes WebSocket conectados
schwab_clients = set()
coinbase_clients = set()

# Estado compartido - SOLO datos capturados VIVOS del WebSocket
state = {
    "schwab": {
        "connected": False,
        "last_update": None,
        "error": None,
        "account_data": {},
        "recent_data": deque(maxlen=100)  # Últimos 100 mensajes
    },
    "coinbase": {
        "connected": False,
        "last_update": None,
        "error": None,
        "account_data": {},
        "recent_data": deque(maxlen=100)  # Últimos 100 mensajes
    }
}

background_tasks = []


async def stream_schwab_websocket():
    """
    Streaming DIRECTO del WebSocket de Schwab
    Sin polling. Captura datos AL INSTANTE.
    """
    reconnect_delay = 5
    
    while True:
        try:
            logger.info("[SCHWAB] Iniciando conexión WebSocket...")
            
            from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
            
            mgr = SchwabWebSocketManager(config_path="hub")
            
            # Conectar (esto incluye renovación automática de token)
            if not await mgr.connect():
                logger.error("[SCHWAB] Falló al conectar")
                state["schwab"]["connected"] = False
                state["schwab"]["error"] = "Connection failed"
                await asyncio.sleep(reconnect_delay)
                continue
            
            state["schwab"]["connected"] = True
            state["schwab"]["error"] = None
            logger.info("[SCHWAB] WebSocket conectado y autenticado")
            
            # Enviar ACCOUNT_EQUITY subscription para capturar datos
            try:
                subscription_msg = {
                    "requests": [{
                        "requestid": "2",
                        "service": "ACCOUNT_EQUITY",
                        "command": "SUBS",
                        "SchwabClientCorrelId": str(__import__('uuid').uuid4()),
                        "parameters": {
                            "accountIds": [mgr.streamer_info.get("accountNumber", "")]
                        }
                    }]
                }
                await mgr.ws.send(json.dumps(subscription_msg))
                logger.info("[SCHWAB] Suscripción ACCOUNT_EQUITY enviada")
            except Exception as e:
                logger.error(f"[SCHWAB] Error en suscripción: {e}")
            
            # BUCLE INFINITO: capturar mensajes conforme llegan
            while mgr.ws and not mgr.ws.closed:
                try:
                    msg = await asyncio.wait_for(mgr.ws.recv(), timeout=30)
                    
                    if msg:
                        try:
                            data = json.loads(msg)
                            
                            # Guardar timestamp
                            data['_timestamp'] = datetime.now().isoformat()
                            state["schwab"]["last_update"] = data['_timestamp']
                            
                            # Almacenar en histórico
                            state["schwab"]["recent_data"].append(data)
                            
                            # Extraer datos relevantes
                            if "response" in data:
                                state["schwab"]["account_data"]["response"] = data["response"]
                            if "data" in data:
                                state["schwab"]["account_data"]["data"] = data["data"]
                            if "snapshot" in data:
                                state["schwab"]["account_data"]["snapshot"] = data["snapshot"]
                            
                            logger.info(f"[SCHWAB] Datos recibidos: {type(data).__name__}")
                            
                            # Broadcast a clientes
                            for client in list(schwab_clients):
                                try:
                                    await client.send_json({
                                        "broker": "schwab",
                                        "data": {
                                            "connected": True,
                                            "last_update": state["schwab"]["last_update"],
                                            "account_data": state["schwab"]["account_data"],
                                            "error": None
                                        }
                                    })
                                except:
                                    schwab_clients.discard(client)
                        
                        except json.JSONDecodeError:
                            logger.debug(f"[SCHWAB] Mensaje no-JSON: {msg[:100]}")
                
                except asyncio.TimeoutError:
                    logger.warning("[SCHWAB] Timeout esperando datos")
                except Exception as e:
                    logger.error(f"[SCHWAB] Error en bucle: {e}")
                    break
            
            logger.warning("[SCHWAB] Conexión cerrada")
            state["schwab"]["connected"] = False
            
        except Exception as e:
            logger.error(f"[SCHWAB] Error: {e}")
            state["schwab"]["connected"] = False
            state["schwab"]["error"] = str(e)[:100]
        
        await asyncio.sleep(reconnect_delay)


async def stream_coinbase_websocket():
    """
    Streaming DIRECTO del WebSocket de Coinbase
    Sin polling. Captura datos AL INSTANTE.
    """
    reconnect_delay = 5
    
    while True:
        try:
            logger.info("[COINBASE] Iniciando conexión WebSocket...")
            
            from hub.managers.coinbase_websocket_manager import CoinbaseWebSocketManager
            
            mgr = CoinbaseWebSocketManager(config_path="hub")
            
            # Conectar (esto incluye renovación automática de JWT)
            if not await mgr.connect():
                logger.error("[COINBASE] Falló al conectar")
                state["coinbase"]["connected"] = False
                state["coinbase"]["error"] = "Connection failed"
                await asyncio.sleep(reconnect_delay)
                continue
            
            state["coinbase"]["connected"] = True
            state["coinbase"]["error"] = None
            logger.info("[COINBASE] WebSocket conectado y suscrito")
            
            # BUCLE INFINITO: capturar mensajes conforme llegan
            while mgr.ws and not mgr.ws.closed:
                try:
                    msg = await asyncio.wait_for(mgr.ws.recv(), timeout=30)
                    
                    if msg:
                        try:
                            data = json.loads(msg)
                            
                            # Guardar timestamp
                            data['_timestamp'] = datetime.now().isoformat()
                            state["coinbase"]["last_update"] = data['_timestamp']
                            
                            # Almacenar en histórico
                            state["coinbase"]["recent_data"].append(data)
                            
                            # Extraer datos según tipo
                            channel = data.get("channel", "")
                            
                            if "events" in data:
                                for event in data["events"]:
                                    if channel == "user":
                                        # Datos de usuario/cuenta
                                        state["coinbase"]["account_data"]["user_events"] = event
                            
                            if "updates" in data:
                                state["coinbase"]["account_data"]["updates"] = data["updates"]
                            
                            logger.info(f"[COINBASE] {channel}: {type(data).__name__}")
                            
                            # Broadcast a clientes
                            for client in list(coinbase_clients):
                                try:
                                    await client.send_json({
                                        "broker": "coinbase",
                                        "data": {
                                            "connected": True,
                                            "last_update": state["coinbase"]["last_update"],
                                            "account_data": state["coinbase"]["account_data"],
                                            "error": None
                                        }
                                    })
                                except:
                                    coinbase_clients.discard(client)
                        
                        except json.JSONDecodeError:
                            logger.debug(f"[COINBASE] Mensaje no-JSON: {msg[:100]}")
                
                except asyncio.TimeoutError:
                    logger.warning("[COINBASE] Timeout esperando datos")
                except Exception as e:
                    logger.error(f"[COINBASE] Error en bucle: {e}")
                    break
            
            logger.warning("[COINBASE] Conexión cerrada")
            state["coinbase"]["connected"] = False
            
        except Exception as e:
            logger.error(f"[COINBASE] Error: {e}")
            state["coinbase"]["connected"] = False
            state["coinbase"]["error"] = str(e)[:100]
        
        await asyncio.sleep(reconnect_delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*80)
    print("WEBSOCKET DASHBOARD - 100% REAL-TIME (SIN POLLING)")
    print("="*80)
    print("\nhttp://localhost:8000")
    print("\nSCHWAB: wss://streamer-api.schwab.com/ws (datos AL INSTANTE)")
    print("COINBASE: wss://advanced-trade-ws.coinbase.com (datos AL INSTANTE)")
    print("\n" + "="*80 + "\n")
    
    task1 = asyncio.create_task(stream_schwab_websocket())
    task2 = asyncio.create_task(stream_coinbase_websocket())
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
        <title>Real-Time Dashboard - 100% WebSocket</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Courier New', monospace;
                background: #0a0e27;
                color: #00ff00;
                padding: 20px;
                overflow-x: hidden;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            .header {
                text-align: center;
                border-bottom: 3px solid #00ff00;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .header h1 { font-size: 2.5em; margin-bottom: 5px; }
            .header p { color: #00aa00; }
            .brokers { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card {
                background: #1a1f3a;
                border: 2px solid #00ff00;
                padding: 20px;
                border-radius: 5px;
                position: relative;
            }
            .card h2 { margin-bottom: 15px; font-size: 1.8em; }
            
            .status-bar {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 20px;
                padding: 10px;
                background: #0f1432;
                border-radius: 3px;
            }
            .dot { 
                width: 14px; 
                height: 14px; 
                border-radius: 50%;
                box-shadow: 0 0 10px;
                animation: pulse 1s infinite;
            }
            .dot.connected { 
                background: #00ff00;
                box-shadow: 0 0 10px #00ff00;
            }
            .dot.disconnected { 
                background: #ff0000;
                animation: none;
            }
            @keyframes pulse { 
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .data-display {
                background: #0a0e27;
                border: 1px solid #00aa00;
                border-radius: 3px;
                padding: 15px;
                max-height: 400px;
                overflow-y: auto;
                font-size: 0.85em;
            }
            
            .data-display pre {
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
                color: #00ff00;
            }
            
            .timestamp {
                color: #00aa00;
                font-size: 0.8em;
                margin-bottom: 10px;
            }
            
            .error { color: #ff6666; }
            .loading { color: #888; }
            
            .message-counter {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #00aa00;
                color: #000;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 0.9em;
            }
            
            @media (max-width: 1024px) { .brokers { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>REAL-TIME DASHBOARD</h1>
                <p>100% WebSocket Streaming - Cero Polling</p>
                <p>Datos capturados AL INSTANTE conforme llegan</p>
            </div>
            
            <div class="brokers">
                <!-- SCHWAB -->
                <div class="card">
                    <div class="message-counter" id="schwab-count">0</div>
                    <h2>SCHWAB</h2>
                    
                    <div class="status-bar">
                        <div class="dot disconnected" id="schwab-dot"></div>
                        <span id="schwab-status">Conectando...</span>
                        <span class="timestamp" id="schwab-time"></span>
                    </div>
                    
                    <div class="data-display">
                        <div id="schwab-data" class="loading">Esperando datos...</div>
                    </div>
                </div>
                
                <!-- COINBASE -->
                <div class="card">
                    <div class="message-counter" id="coinbase-count">0</div>
                    <h2>COINBASE</h2>
                    
                    <div class="status-bar">
                        <div class="dot disconnected" id="coinbase-dot"></div>
                        <span id="coinbase-status">Conectando...</span>
                        <span class="timestamp" id="coinbase-time"></span>
                    </div>
                    
                    <div class="data-display">
                        <div id="coinbase-data" class="loading">Esperando datos...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let schwabCount = 0, coinbaseCount = 0;
            
            const schwabWs = new WebSocket("ws://localhost:8000/ws/schwab");
            const coinbaseWs = new WebSocket("ws://localhost:8000/ws/coinbase");
            
            function formatTime(isoString) {
                const d = new Date(isoString);
                return d.toLocaleTimeString() + '.' + d.getMilliseconds();
            }
            
            schwabWs.onmessage = (e) => {
                try {
                    const msg = JSON.parse(e.data);
                    const data = msg.data;
                    
                    schwabCount++;
                    document.getElementById("schwab-count").textContent = schwabCount;
                    
                    document.getElementById("schwab-dot").className = 
                        "dot " + (data.connected ? "connected" : "disconnected");
                    document.getElementById("schwab-status").textContent = 
                        data.connected ? "CONECTADO" : "DESCONECTADO";
                    
                    if (data.last_update) {
                        document.getElementById("schwab-time").textContent = 
                            formatTime(data.last_update);
                    }
                    
                    if (data.error) {
                        document.getElementById("schwab-data").innerHTML = 
                            '<span class="error">ERROR: ' + data.error + '</span>';
                    } else {
                        const display = JSON.stringify(data.account_data, null, 2);
                        document.getElementById("schwab-data").innerHTML = 
                            '<pre>' + display.substring(0, 2000) + '...</pre>';
                    }
                } catch (err) {
                    console.error("SCHWAB parse error:", err);
                }
            };
            
            coinbaseWs.onmessage = (e) => {
                try {
                    const msg = JSON.parse(e.data);
                    const data = msg.data;
                    
                    coinbaseCount++;
                    document.getElementById("coinbase-count").textContent = coinbaseCount;
                    
                    document.getElementById("coinbase-dot").className = 
                        "dot " + (data.connected ? "connected" : "disconnected");
                    document.getElementById("coinbase-status").textContent = 
                        data.connected ? "CONECTADO" : "DESCONECTADO";
                    
                    if (data.last_update) {
                        document.getElementById("coinbase-time").textContent = 
                            formatTime(data.last_update);
                    }
                    
                    if (data.error) {
                        document.getElementById("coinbase-data").innerHTML = 
                            '<span class="error">ERROR: ' + data.error + '</span>';
                    } else {
                        const display = JSON.stringify(data.account_data, null, 2);
                        document.getElementById("coinbase-data").innerHTML = 
                            '<pre>' + display.substring(0, 2000) + '...</pre>';
                    }
                } catch (err) {
                    console.error("COINBASE parse error:", err);
                }
            };
            
            schwabWs.onerror = () => {
                document.getElementById("schwab-dot").className = "dot disconnected";
                document.getElementById("schwab-status").textContent = "ERROR DE CONEXION";
            };
            
            coinbaseWs.onerror = () => {
                document.getElementById("coinbase-dot").className = "dot disconnected";
                document.getElementById("coinbase-status").textContent = "ERROR DE CONEXION";
            };
        </script>
    </body>
    </html>
    """)


@app.websocket("/ws/schwab")
async def ws_schwab(websocket: WebSocket):
    await websocket.accept()
    schwab_clients.add(websocket)
    try:
        await websocket.send_json({"broker": "schwab", "data": state["schwab"]})
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        schwab_clients.discard(websocket)


@app.websocket("/ws/coinbase")
async def ws_coinbase(websocket: WebSocket):
    await websocket.accept()
    coinbase_clients.add(websocket)
    try:
        await websocket.send_json({"broker": "coinbase", "data": state["coinbase"]})
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        coinbase_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
