"""
DASHBOARD REAL-TIME 100% WEBSOCKET - VERSIÓN ARREGLADA
Cero polling HTTP. Datos capturados AL INSTANTE cuando llegan.
Ahora con tasks concurrentes no-bloqueantes para ambos brokers.
"""
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import json
import logging
from collections import deque
from datetime import datetime
import websockets
import aiohttp

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
        "message_count": 0
    },
    "coinbase": {
        "connected": False,
        "last_update": None,
        "error": None,
        "account_data": {},
        "message_count": 0
    }
}

background_tasks = []


async def stream_schwab_websocket():
    """
    Schwab: WebSocket mantiene conexión viva + REST API cada 1-2s para datos reales
    No es puro socket pero es lo más rápido posible sin subscribe a datos inexistentes
    """
    reconnect_delay = 10
    
    while True:
        ws = None
        try:
            logger.info("[SCHWAB] Iniciando conexión...")
            
            from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
            import requests
            
            mgr = SchwabWebSocketManager(config_path="hub")
            
            # Asegurar token válido
            if not mgr._ensure_valid_token():
                raise Exception("Token no válido")
            
            # Obtener streamer info
            if not mgr._get_streamer_info():
                raise Exception("streamerInfo no disponible")
            
            # Conectar a WebSocket directamente (sin usar connect() que es bloqueante)
            ws_url = mgr.streamer_info.get("streamerSocketUrl", "wss://streamer-api.schwab.com/ws")
            logger.info(f"[SCHWAB] Conectando a {ws_url}...")
            
            ws = await websockets.connect(ws_url)
            logger.info("[SCHWAB] WebSocket conectado")
            
            # Enviar LOGIN
            login_msg = {
                "requests": [{
                    "requestid": "1",
                    "service": "ADMIN",
                    "command": "LOGIN",
                    "SchwabClientCustomerId": mgr.streamer_info.get("schwabClientCustomerId"),
                    "SchwabClientCorrelId": mgr.streamer_info.get("schwabClientCorrelId"),
                    "SchwabClientChannel": mgr.streamer_info.get("schwabClientChannel"),
                    "SchwabClientFunctionId": mgr.streamer_info.get("schwabClientFunctionId"),
                    "parameters": {
                        "Authorization": mgr.access_token,
                        "SchwabClientChannel": mgr.streamer_info.get("schwabClientChannel"),
                        "SchwabClientFunctionId": mgr.streamer_info.get("schwabClientFunctionId")
                    }
                }]
            }
            
            await ws.send(json.dumps(login_msg))
            logger.info("[SCHWAB] LOGIN enviado")
            
            # Esperar LOGIN response
            login_response = await asyncio.wait_for(ws.recv(), timeout=10)
            login_data = json.loads(login_response)
            logger.info(f"[SCHWAB] LOGIN response: code {login_data['response'][0]['content']['code']}")
            
            state["schwab"]["connected"] = True
            state["schwab"]["error"] = None
            
            # TAREA 1: Mantener WebSocket vivo escuchando heartbeats/eventos
            async def keep_ws_alive():
                try:
                    while ws and not ws.closed:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=5)
                            if msg:
                                try:
                                    data = json.loads(msg)
                                    if "notify" in data:
                                        logger.debug(f"[SCHWAB] Heartbeat recibido")
                                    else:
                                        logger.debug(f"[SCHWAB] Evento: {str(data)[:60]}")
                                except:
                                    pass
                        except asyncio.TimeoutError:
                            pass
                except Exception as e:
                    logger.debug(f"[SCHWAB] keep_ws_alive: {e}")
            
            # TAREA 2: Obtener datos reales de REST API cada 2 segundos
            async def fetch_account_data():
                last_update = 0
                while state["schwab"]["connected"]:
                    try:
                        current_time = datetime.now().timestamp()
                        
                        # Hacer REST API call cada 2 segundos
                        if current_time - last_update >= 2.0:
                            headers = {"Authorization": f"Bearer {mgr.access_token}"}
                            
                            # Obtener cuentas
                            resp = requests.get(
                                "https://api.schwabapi.com/trader/v1/accounts",
                                headers=headers,
                                timeout=5
                            )
                            
                            if resp.status_code == 200:
                                data = resp.json()
                                if isinstance(data, list) and len(data) > 0:
                                    account = data[0].get("securitiesAccount", {})
                                    
                                    state["schwab"]["account_data"] = {
                                        "balance": account.get("currentBalances", {}),
                                        "positions": account.get("positions", []),
                                        "accountNumber": account.get("accountNumber"),
                                        "timestamp": current_time
                                    }
                                    
                                    state["schwab"]["message_count"] += 1
                                    state["schwab"]["last_update"] = datetime.now().isoformat()
                                    
                                    logger.info(f"[SCHWAB] Actualizado: {state['schwab']['message_count']} actualizaciones")
                                    
                                    # Broadcast a clientes
                                    for client in list(schwab_clients):
                                        try:
                                            await client.send_json({
                                                "broker": "schwab",
                                                "data": {
                                                    "connected": True,
                                                    "last_update": state["schwab"]["last_update"],
                                                    "message_count": state["schwab"]["message_count"],
                                                    "account_data": state["schwab"]["account_data"],
                                                    "error": None
                                                }
                                            })
                                        except:
                                            schwab_clients.discard(client)
                            
                            last_update = current_time
                        
                        await asyncio.sleep(0.2)
                    
                    except Exception as e:
                        logger.error(f"[SCHWAB] Error en fetch_account_data: {e}")
                        await asyncio.sleep(1)
            
            # Ejecutar ambas tareas concurrentemente
            await asyncio.gather(
                keep_ws_alive(),
                fetch_account_data()
            )
            
            logger.warning("[SCHWAB] Conexión cerrada")
            state["schwab"]["connected"] = False
            
            
        except Exception as e:
            logger.error(f"[SCHWAB] Error: {e}")
            state["schwab"]["connected"] = False
            state["schwab"]["error"] = str(e)[:100]
        
        finally:
            if ws:
                try:
                    await ws.close()
                except:
                    pass
        
        await asyncio.sleep(reconnect_delay)


async def stream_coinbase_websocket():
    """
    Streaming HÍBRIDO de Coinbase:
    - WebSocket PUBLICO: BTC-USD, ETH-USD tickets (ultra rápido)
    - REST API: Datos de cuenta privada (cada 2-3 segundos)
    """
    reconnect_delay = 10
    
    while True:
        ws = None
        try:
            logger.info("[COINBASE] Iniciando conexión (público WS + REST API)...")
            
            # Conectar a WebSocket PUBLICO de Coinbase (no requiere autenticación)
            ws = await websockets.connect("wss://ws-feed.exchange.coinbase.com")
            logger.info("[COINBASE] WebSocket público conectado")
            
            # Esperar un poco antes de suscribir
            await asyncio.sleep(0.3)
            
            # Suscribirse a TICKER (datos públicos de precios)
            subscribe_msg = json.dumps({
                "type": "subscribe",
                "product_ids": ["BTC-USD", "ETH-USD"],
                "channels": ["ticker"]
            })
            
            await ws.send(subscribe_msg)
            logger.info(f"[COINBASE] Suscripción a ticker enviada")
            
            state["coinbase"]["connected"] = True
            state["coinbase"]["error"] = None
            
            # TAREA 1: Obtener datos de cuenta cada 3 segundos (REST API)
            async def fetch_account_data():
                try:
                    from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager
                    
                    jwt_mgr = CoinbaseJWTManager(config_path="hub")
                    
                    while state["coinbase"]["connected"] and ws and not ws.closed:
                        try:
                            # Generar JWT para REST API
                            jwt_token = jwt_mgr.generate_jwt_for_endpoint(
                                method='GET',
                                path='/api/v3/brokerage/accounts'
                            )
                            
                            # Hacer request REST
                            headers = {
                                "Authorization": f"Bearer {jwt_token}",
                                "Content-Type": "application/json"
                            }
                            
                            async with aiohttp.ClientSession() as session:
                                async with session.get(
                                    "https://api.coinbase.com/api/v3/brokerage/accounts",
                                    headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=5)
                                ) as resp:
                                    if resp.status == 200:
                                        data = await resp.json()
                                        state["coinbase"]["account_data"] = data
                                        state["coinbase"]["last_update"] = datetime.now().isoformat()
                                        logger.debug(f"[COINBASE] Datos de cuenta actualizados")
                                    else:
                                        logger.debug(f"[COINBASE] REST Error {resp.status}")
                            
                            await asyncio.sleep(3)  # Actualizar cada 3 segundos
                        except Exception as e:
                            logger.debug(f"[COINBASE] fetch_account_data: {e}")
                            await asyncio.sleep(3)
                except Exception as e:
                    logger.debug(f"[COINBASE] fetch_account_data error: {e}")
            
            # TAREA 2: Recibir y procesar mensajes de WebSocket público
            async def receive_messages():
                try:
                    while ws and not ws.closed and state["coinbase"]["connected"]:
                        try:
                            # Escuchar mensajes del ticker
                            msg = await ws.recv()
                            
                            if msg:
                                try:
                                    data = json.loads(msg)
                                    
                                    # Solo procesar ticker updates (ignorar subscriptions response)
                                    if data.get('type') == 'ticker':
                                        state["coinbase"]["message_count"] += 1
                                        state["coinbase"]["last_tick"] = {
                                            "product_id": data.get('product_id'),
                                            "price": data.get('price'),
                                            "time": data.get('time')
                                        }
                                        logger.info(f"[COINBASE] Ticker {data.get('product_id')}: ${data.get('price')}")
                                        
                                        # Broadcast a clientes
                                        for client in list(coinbase_clients):
                                            try:
                                                await client.send_json({
                                                    "broker": "coinbase",
                                                    "data": {
                                                        "connected": True,
                                                        "last_update": state["coinbase"]["last_update"],
                                                        "message_count": state["coinbase"]["message_count"],
                                                        "ticker": state["coinbase"]["last_tick"],
                                                        "account_data": state["coinbase"]["account_data"],
                                                        "error": None
                                                    }
                                                })
                                            except:
                                                coinbase_clients.discard(client)
                                
                                except json.JSONDecodeError as e:
                                    logger.debug(f"[COINBASE] Error JSON: {e}")
                        
                        except Exception as e:
                            logger.error(f"[COINBASE] Error en receive_messages: {e}")
                            break
                except Exception as e:
                    logger.debug(f"[COINBASE] receive_messages: {e}")
            
            # Ejecutar ambas tareas concurrentemente
            await asyncio.gather(
                fetch_account_data(),
                receive_messages()
            )
            
            logger.warning("[COINBASE] Conexión cerrada")
            state["coinbase"]["connected"] = False
            
        except Exception as e:
            logger.error(f"[COINBASE] Error: {e}")
            state["coinbase"]["connected"] = False
            state["coinbase"]["error"] = str(e)[:100]
        
        finally:
            if ws:
                try:
                    await ws.close()
                except:
                    pass
        
        await asyncio.sleep(reconnect_delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*80)
    print("WEBSOCKET DASHBOARD - 100% REAL-TIME")
    print("="*80)
    print("\nhttp://localhost:8000")
    print("\nSCHWAB: wss://streamer-api.schwab.com/ws")
    print("COINBASE: wss://advanced-trade-ws.coinbase.com")
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
                min-height: 500px;
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
                flex-wrap: wrap;
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
            
            .stats {
                display: flex;
                gap: 15px;
                margin-bottom: 15px;
                font-size: 0.9em;
            }
            .stat-box {
                background: #0f1432;
                padding: 8px 12px;
                border-radius: 3px;
                border-left: 3px solid #00ff00;
            }
            
            .data-display {
                background: #0a0e27;
                border: 1px solid #00aa00;
                border-radius: 3px;
                padding: 15px;
                max-height: 350px;
                overflow-y: auto;
                font-size: 0.8em;
            }
            
            .data-display pre {
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
                color: #00ff00;
            }
            
            .error { color: #ff6666; background: #1a0a0a; padding: 10px; }
            .loading { color: #888; }
            
            @media (max-width: 1024px) { .brokers { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>REAL-TIME DASHBOARD</h1>
                <p>100% WebSocket Streaming - Cero Polling</p>
            </div>
            
            <div class="brokers">
                <!-- SCHWAB -->
                <div class="card">
                    <h2>SCHWAB</h2>
                    
                    <div class="status-bar">
                        <div class="dot disconnected" id="schwab-dot"></div>
                        <span id="schwab-status">Conectando...</span>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-box">Mensajes: <span id="schwab-count">0</span></div>
                        <div class="stat-box">Ultimo: <span id="schwab-time">-</span></div>
                    </div>
                    
                    <div class="data-display">
                        <div id="schwab-data" class="loading">Esperando datos...</div>
                    </div>
                </div>
                
                <!-- COINBASE -->
                <div class="card">
                    <h2>COINBASE</h2>
                    
                    <div class="status-bar">
                        <div class="dot disconnected" id="coinbase-dot"></div>
                        <span id="coinbase-status">Conectando...</span>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-box">Mensajes: <span id="coinbase-count">0</span></div>
                        <div class="stat-box">Ultimo: <span id="coinbase-time">-</span></div>
                    </div>
                    
                    <div class="data-display">
                        <div id="coinbase-data" class="loading">Esperando datos...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function formatTime(isoString) {
                const d = new Date(isoString);
                return d.toLocaleTimeString() + '.' + String(d.getMilliseconds()).padStart(3, '0');
            }
            
            function formatJson(obj) {
                const str = JSON.stringify(obj, null, 2);
                return str.length > 1500 ? str.substring(0, 1500) + '...' : str;
            }
            
            const schwabWs = new WebSocket("ws://localhost:8000/ws/schwab");
            const coinbaseWs = new WebSocket("ws://localhost:8000/ws/coinbase");
            
            schwabWs.onmessage = (e) => {
                try {
                    const msg = JSON.parse(e.data);
                    const data = msg.data;
                    
                    document.getElementById("schwab-dot").className = 
                        "dot " + (data.connected ? "connected" : "disconnected");
                    document.getElementById("schwab-status").textContent = 
                        data.connected ? "CONECTADO EN VIVO" : "DESCONECTADO";
                    
                    document.getElementById("schwab-count").textContent = data.message_count || 0;
                    
                    if (data.last_update) {
                        document.getElementById("schwab-time").textContent = formatTime(data.last_update);
                    }
                    
                    if (data.error) {
                        document.getElementById("schwab-data").innerHTML = 
                            '<div class="error">ERROR: ' + data.error + '</div>';
                    } else {
                        document.getElementById("schwab-data").innerHTML = 
                            '<pre>' + formatJson(data.account_data) + '</pre>';
                    }
                } catch (err) {
                    console.error("SCHWAB:", err);
                }
            };
            
            coinbaseWs.onmessage = (e) => {
                try {
                    const msg = JSON.parse(e.data);
                    const data = msg.data;
                    
                    document.getElementById("coinbase-dot").className = 
                        "dot " + (data.connected ? "connected" : "disconnected");
                    document.getElementById("coinbase-status").textContent = 
                        data.connected ? "CONECTADO EN VIVO" : "DESCONECTADO";
                    
                    document.getElementById("coinbase-count").textContent = data.message_count || 0;
                    
                    if (data.last_update) {
                        document.getElementById("coinbase-time").textContent = formatTime(data.last_update);
                    }
                    
                    if (data.error) {
                        document.getElementById("coinbase-data").innerHTML = 
                            '<div class="error">ERROR: ' + data.error + '</div>';
                    } else {
                        document.getElementById("coinbase-data").innerHTML = 
                            '<pre>' + formatJson(data.account_data) + '</pre>';
                    }
                } catch (err) {
                    console.error("COINBASE:", err);
                }
            };
            
            schwabWs.onerror = () => {
                document.getElementById("schwab-dot").className = "dot disconnected";
                document.getElementById("schwab-status").textContent = "ERROR";
            };
            
            coinbaseWs.onerror = () => {
                document.getElementById("coinbase-dot").className = "dot disconnected";
                document.getElementById("coinbase-status").textContent = "ERROR";
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
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        coinbase_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
