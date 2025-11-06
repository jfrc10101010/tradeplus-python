"""
WebSocket Dashboard - Schwab + Coinbase en PARALELO (SIN CONFLICTOS)
Datos privados en tiempo real de ambos brokers simultáneamente
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
        "balance": None,
        "positions": [],
        "error": None,
        "last_update": None
    },
    "coinbase": {
        "connected": False,
        "accounts": [],
        "error": None,
        "last_update": None
    }
}


# ============================================================================
# LIFESPAN MANAGER - Ejecutar tasks en background
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager para iniciar/detener background tasks"""
    # STARTUP
    print("\n" + "="*80)
    print("🚀 DASHBOARD INICIADO")
    print("="*80)
    print("\n✅ Abre: http://localhost:8000")
    print("📊 Schwab WebSocket actualiza cada 5 segundos")
    print("💰 Coinbase WebSocket actualiza cada 5 segundos")
    print("\n" + "="*80 + "\n")
    
    # Iniciar tasks en background
    task1 = asyncio.create_task(update_schwab_data())
    task2 = asyncio.create_task(update_coinbase_data())
    background_tasks.append(task1)
    background_tasks.append(task2)
    
    yield  # App run while here
    
    # SHUTDOWN
    for task in background_tasks:
        task.cancel()
    
    logger.info("✅ Dashboard cerrado")


# Crear app con lifespan
app = FastAPI(lifespan=lifespan)


async def update_schwab_data():
    """Actualiza datos de Schwab cada 5 segundos"""
    while True:
        try:
            from hub.managers.schwab_token_manager import SchwabTokenManager
            import requests
            
            token_manager = SchwabTokenManager(config_path="hub")
            token = token_manager.get_current_token()
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # GET /v1/accounts
            resp = requests.get(
                "https://api.schwabapi.com/trader/v1/accounts",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                accounts_data = resp.json()
                
                if "securitiesAccount" in accounts_data:
                    acct = accounts_data["securitiesAccount"]
                    state["schwab"]["balance"] = {
                        "cash": acct.get("currentBalances", {}).get("cashBalance", 0),
                        "buying_power": acct.get("currentBalances", {}).get("buyingPower", 0),
                        "liquidation_value": acct.get("currentBalances", {}).get("liquidationValue", 0)
                    }
                    state["schwab"]["positions"] = acct.get("positions", [])[:5]  # Top 5
                
                state["schwab"]["connected"] = True
                state["schwab"]["error"] = None
            else:
                state["schwab"]["error"] = f"HTTP {resp.status_code}"
                state["schwab"]["connected"] = False
            
            state["schwab"]["last_update"] = asyncio.get_event_loop().time()
            
            # Broadcast
            for client in list(schwab_clients):
                try:
                    await client.send_json({
                        "type": "update",
                        "broker": "schwab",
                        "data": state["schwab"]
                    })
                except Exception as e:
                    logger.debug(f"Error enviando a cliente Schwab: {e}")
                    schwab_clients.discard(client)
        
        except Exception as e:
            state["schwab"]["error"] = str(e)[:100]
            state["schwab"]["connected"] = False
            logger.error(f"❌ Error Schwab: {e}")
        
        await asyncio.sleep(5)


async def update_coinbase_data():
    """Actualiza datos de Coinbase cada 5 segundos"""
    import importlib
    
    while True:
        try:
            import requests
            
            # Reimportar para evitar issues de módulo cacheado
            import sys
            if 'hub.managers.coinbase_jwt_manager' in sys.modules:
                del sys.modules['hub.managers.coinbase_jwt_manager']
            
            from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager
            
            # Crear instancia y obtener JWT
            try:
                jwt_manager = CoinbaseJWTManager(config_path="hub")
                jwt_token = jwt_manager.get_current_jwt()
            except AttributeError as ae:
                logger.error(f"❌ AttributeError en CoinbaseJWTManager: {ae}")
                state["coinbase"]["error"] = f"Manager error: {str(ae)[:50]}"
                state["coinbase"]["connected"] = False
                await asyncio.sleep(5)
                continue
            
            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }
            
            # GET /api/v3/brokerage/accounts
            resp = requests.get(
                "https://api.coinbase.com/api/v3/brokerage/accounts",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                state["coinbase"]["accounts"] = data.get("accounts", [])[:10]  # Top 10
                state["coinbase"]["connected"] = True
                state["coinbase"]["error"] = None
            else:
                state["coinbase"]["error"] = f"HTTP {resp.status_code}"
                state["coinbase"]["connected"] = False
            
            state["coinbase"]["last_update"] = asyncio.get_event_loop().time()
            
            # Broadcast
            for client in list(coinbase_clients):
                try:
                    await client.send_json({
                        "type": "update",
                        "broker": "coinbase",
                        "data": state["coinbase"]
                    })
                except Exception as e:
                    logger.debug(f"Error enviando a cliente Coinbase: {e}")
                    coinbase_clients.discard(client)
        
        except Exception as e:
            import traceback
            state["coinbase"]["error"] = str(e)[:100]
            state["coinbase"]["connected"] = False
            logger.error(f"❌ Error Coinbase: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
        
        await asyncio.sleep(5)


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
    
    # Enviar estado inicial
    await websocket.send_json({
        "type": "init",
        "broker": "schwab",
        "data": state["schwab"]
    })
    
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        logger.info(f"⚠️ Cliente Schwab desconectado: {e}")
        schwab_clients.discard(websocket)


@app.websocket("/ws/coinbase")
async def websocket_coinbase(websocket: WebSocket):
    """WebSocket para Coinbase"""
    await websocket.accept()
    coinbase_clients.add(websocket)
    logger.info(f"✅ Cliente Coinbase conectado ({len(coinbase_clients)} total)")
    
    # Enviar estado inicial
    await websocket.send_json({
        "type": "init",
        "broker": "coinbase",
        "data": state["coinbase"]
    })
    
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        logger.info(f"⚠️ Cliente Coinbase desconectado: {e}")
        coinbase_clients.discard(websocket)
    
    # Enviar estado inicial
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


# HTML + JavaScript para el dashboard
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Brokers - Real Time Private Data</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .brokers {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .broker-card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.3s;
        }
        
        .broker-card:hover {
            transform: translateY(-5px);
        }
        
        .broker-header {
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .broker-header h2 {
            font-size: 1.5em;
        }
        
        .status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status.connected {
            background: #4ade80;
        }
        
        .status.disconnected {
            background: #ef4444;
            animation: none;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .broker-content {
            padding: 20px;
        }
        
        .section {
            margin-bottom: 20px;
        }
        
        .section-title {
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 5px;
        }
        
        .balance-display {
            font-size: 1.8em;
            font-weight: bold;
            color: #764ba2;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        
        .table thead {
            background: #f5f5f5;
        }
        
        .table th, .table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .table th {
            font-weight: bold;
            color: #667eea;
        }
        
        .table tr:hover {
            background: #f9f9f9;
        }
        
        .value {
            font-family: 'Courier New', monospace;
            font-weight: 600;
        }
        
        .positive {
            color: #4ade80;
        }
        
        .negative {
            color: #ef4444;
        }
        
        .error-message {
            background: #fee2e2;
            color: #991b1b;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #999;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .empty-state {
            text-align: center;
            padding: 20px;
            color: #999;
            font-style: italic;
        }
        
        .timestamp {
            font-size: 0.85em;
            color: #999;
            margin-top: 10px;
        }
        
        @media (max-width: 768px) {
            .brokers {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 WebSocket Real-Time Dashboard</h1>
            <p>Private Data - Schwab & Coinbase</p>
        </div>
        
        <div class="brokers">
            <!-- SCHWAB -->
            <div class="broker-card">
                <div class="broker-header">
                    <h2>📊 Schwab</h2>
                    <div class="status disconnected" id="schwab-status"></div>
                </div>
                <div class="broker-content">
                    <div id="schwab-data">
                        <div class="loading">
                            <div class="spinner"></div>
                            <p>Connecting...</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- COINBASE -->
            <div class="broker-card">
                <div class="broker-header">
                    <h2>💰 Coinbase</h2>
                    <div class="status disconnected" id="coinbase-status"></div>
                </div>
                <div class="broker-content">
                    <div id="coinbase-data">
                        <div class="loading">
                            <div class="spinner"></div>
                            <p>Connecting...</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Conectar a WebSocket de Schwab
        const schwabWs = new WebSocket("ws://localhost:8000/ws/schwab");
        
        schwabWs.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            updateSchwabUI(msg.data);
        };
        
        schwabWs.onclose = () => {
            document.getElementById("schwab-status").className = "status disconnected";
        };
        
        // Conectar a WebSocket de Coinbase
        const coinbaseWs = new WebSocket("ws://localhost:8000/ws/coinbase");
        
        coinbaseWs.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            updateCoinbaseUI(msg.data);
        };
        
        coinbaseWs.onclose = () => {
            document.getElementById("coinbase-status").className = "status disconnected";
        };
        
        // Actualizar UI de Schwab
        function updateSchwabUI(data) {
            const container = document.getElementById("schwab-data");
            
            if (data.error) {
                container.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                document.getElementById("schwab-status").className = "status disconnected";
                return;
            }
            
            document.getElementById("schwab-status").className = "status connected";
            
            let html = "";
            
            // Balance
            if (data.balance) {
                html += `
                    <div class="section">
                        <div class="section-title">💵 Account Balance</div>
                        <div class="balance-display positive">
                            $${(data.balance.liquidationValue || 0).toFixed(2)}
                        </div>
                        <table class="table">
                            <tr>
                                <td>Cash</td>
                                <td class="value">$${(data.balance.cashBalance || 0).toFixed(2)}</td>
                            </tr>
                            <tr>
                                <td>Buying Power</td>
                                <td class="value">$${(data.balance.buyingPower || 0).toFixed(2)}</td>
                            </tr>
                            <tr>
                                <td>Day Trading Buying Power</td>
                                <td class="value">$${(data.balance.dayTradingBuyingPower || 0).toFixed(2)}</td>
                            </tr>
                        </table>
                    </div>
                `;
            }
            
            // Posiciones
            if (data.positions && data.positions.length > 0) {
                html += `
                    <div class="section">
                        <div class="section-title">📈 Open Positions (${data.positions.length})</div>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Qty</th>
                                    <th>Avg Price</th>
                                    <th>Market Value</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.positions.slice(0, 5).forEach(pos => {
                    const instrument = pos.instrument || {};
                    const qty = pos.longQuantity + pos.shortQuantity;
                    const value = pos.marketValue || 0;
                    const cls = value >= 0 ? "positive" : "negative";
                    
                    html += `
                        <tr>
                            <td>${instrument.symbol || 'N/A'}</td>
                            <td class="value">${qty}</td>
                            <td class="value">$${(pos.averagePrice || 0).toFixed(2)}</td>
                            <td class="value ${cls}">$${value.toFixed(2)}</td>
                        </tr>
                    `;
                });
                
                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            }
            
            if (!data.balance && (!data.positions || data.positions.length === 0)) {
                html = '<div class="empty-state">Aguardando datos...</div>';
            }
            
            html += `<div class="timestamp">Last update: ${new Date().toLocaleTimeString()}</div>`;
            container.innerHTML = html;
        }
        
        // Actualizar UI de Coinbase
        function updateCoinbaseUI(data) {
            const container = document.getElementById("coinbase-data");
            
            if (data.error) {
                container.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                document.getElementById("coinbase-status").className = "status disconnected";
                return;
            }
            
            document.getElementById("coinbase-status").className = "status connected";
            
            let html = "";
            
            // Cuentas/Wallets
            if (data.accounts && data.accounts.length > 0) {
                html += `
                    <div class="section">
                        <div class="section-title">💳 Wallets (${data.accounts.length})</div>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Currency</th>
                                    <th>Balance</th>
                                    <th>Hold</th>
                                    <th>Available</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.accounts.slice(0, 10).forEach(acc => {
                    const balance = parseFloat(acc.balance || 0);
                    const hold = parseFloat(acc.hold || 0);
                    const available = parseFloat(acc.available || 0);
                    const cls = available > 0 ? "positive" : "negative";
                    
                    html += `
                        <tr>
                            <td>${acc.currency || 'N/A'}</td>
                            <td class="value">${balance.toFixed(8)}</td>
                            <td class="value">${hold.toFixed(8)}</td>
                            <td class="value ${cls}">${available.toFixed(8)}</td>
                        </tr>
                    `;
                });
                
                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            }
            
            if (!data.accounts || data.accounts.length === 0) {
                html = '<div class="empty-state">Aguardando datos...</div>';
            }
            
            html += `<div class="timestamp">Actualizado: ${new Date().toLocaleTimeString()}</div>`;
            container.innerHTML = html || '<p style="color: #999;">Cargando datos...</p>';
        }
    </script>
</body>
</html>
"""



if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print("🚀 DASHBOARD EN VIVO - WEBSOCKET")
    print("="*80)
    print("\n✅ Abre: http://localhost:8000")
    print("\n📊 SCHWAB: Saldo, Posiciones Abiertas, Compra/Venta")
    print("💰 COINBASE: Wallets, Saldos, Disponible\n")
    print("="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

