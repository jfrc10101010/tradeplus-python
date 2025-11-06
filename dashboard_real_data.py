"""
WEBSOCKET DASHBOARD - DATOS PRIVADOS REALES
Muestra balance real, posiciones, trades, wallets
"""
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clientes conectados
schwab_clients = set()
coinbase_clients = set()

# Estado compartido con datos REALES
state = {
    "schwab": {
        "connected": False,
        "balance": None,
        "positions": [],
        "error": None,
        "trades": []
    },
    "coinbase": {
        "connected": False,
        "accounts": [],
        "error": None,
        "total_balance": 0
    }
}

background_tasks = []


async def stream_schwab_real_data():
    """Captura datos REALES de Schwab WebSocket"""
    while True:
        try:
            from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
            import requests
            
            logger.info("[SCHWAB] Conectando...")
            mgr = SchwabWebSocketManager(config_path="hub")
            
            # Obtener info de cuenta vía REST API (datos reales)
            token = mgr.token_manager.get_current_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            resp = requests.get(
                "https://api.schwabapi.com/trader/v1/accounts",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if "securitiesAccount" in data:
                    acct = data["securitiesAccount"]
                    
                    # Extraer balance REAL
                    state["schwab"]["balance"] = {
                        "cash": acct.get("currentBalances", {}).get("cashBalance", 0),
                        "buying_power": acct.get("currentBalances", {}).get("buyingPower", 0),
                        "liquidation_value": acct.get("currentBalances", {}).get("liquidationValue", 0),
                        "account_number": acct.get("accountNumber", "N/A")
                    }
                    
                    # Extraer posiciones REALES (hasta 10)
                    positions = acct.get("positions", [])
                    state["schwab"]["positions"] = [
                        {
                            "symbol": pos.get("instrument", {}).get("symbol", "N/A"),
                            "quantity": pos.get("longQuantity", 0) + pos.get("shortQuantity", 0),
                            "average_price": pos.get("averagePrice", 0),
                            "market_value": pos.get("marketValue", 0),
                            "gain_loss": pos.get("marketValue", 0) - (pos.get("averagePrice", 0) * (pos.get("longQuantity", 0) + pos.get("shortQuantity", 0)))
                        }
                        for pos in positions[:10]
                    ]
                    
                    state["schwab"]["connected"] = True
                    state["schwab"]["error"] = None
                    logger.info(f"[SCHWAB] Balance: ${state['schwab']['balance']['liquidation_value']:,.2f}")
            else:
                state["schwab"]["error"] = f"HTTP {resp.status_code}"
                state["schwab"]["connected"] = False
            
            # Broadcast
            for client in list(schwab_clients):
                try:
                    await client.send_json({
                        "broker": "schwab",
                        "data": state["schwab"]
                    })
                except:
                    schwab_clients.discard(client)
            
            await asyncio.sleep(5)
        
        except Exception as e:
            state["schwab"]["error"] = str(e)[:100]
            state["schwab"]["connected"] = False
            logger.error(f"[SCHWAB] Error: {e}")
            await asyncio.sleep(5)


async def stream_coinbase_real_data():
    """Captura datos REALES de Coinbase"""
    while True:
        try:
            from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager
            import requests
            
            logger.info("[COINBASE] Conectando...")
            jwt_mgr = CoinbaseJWTManager(config_path="hub")
            jwt = jwt_mgr.get_current_jwt()
            
            headers = {
                "Authorization": f"Bearer {jwt}",
                "Content-Type": "application/json"
            }
            
            # Obtener cuentas/wallets REALES
            resp = requests.get(
                "https://api.coinbase.com/api/v3/brokerage/accounts",
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                accounts = data.get("accounts", [])
                
                # Procesar cuentas
                state["coinbase"]["accounts"] = [
                    {
                        "currency": acc.get("currency", "N/A"),
                        "balance": float(acc.get("available_balance", {}).get("value", 0)),
                        "hold": float(acc.get("hold", {}).get("value", 0)) if acc.get("hold") else 0,
                        "available": float(acc.get("available_balance", {}).get("value", 0))
                    }
                    for acc in accounts if float(acc.get("available_balance", {}).get("value", 0)) > 0
                ]
                
                # Total balance
                state["coinbase"]["total_balance"] = sum(
                    acc["balance"] for acc in state["coinbase"]["accounts"]
                )
                
                state["coinbase"]["connected"] = True
                state["coinbase"]["error"] = None
                logger.info(f"[COINBASE] Total: ${state['coinbase']['total_balance']:.2f} USD")
            else:
                state["coinbase"]["error"] = f"HTTP {resp.status_code}"
                state["coinbase"]["connected"] = False
            
            # Broadcast
            for client in list(coinbase_clients):
                try:
                    await client.send_json({
                        "broker": "coinbase",
                        "data": state["coinbase"]
                    })
                except:
                    coinbase_clients.discard(client)
            
            await asyncio.sleep(5)
        
        except Exception as e:
            state["coinbase"]["error"] = str(e)[:100]
            state["coinbase"]["connected"] = False
            logger.error(f"[COINBASE] Error: {e}")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*80)
    print("WEBSOCKET DASHBOARD - DATOS PRIVADOS REALES")
    print("="*80)
    print("\nhttp://localhost:8000")
    print("\nSCHWAB: Balance + Posiciones Abiertas")
    print("COINBASE: Wallets + Saldos")
    print("\n" + "="*80 + "\n")
    
    task1 = asyncio.create_task(stream_schwab_real_data())
    task2 = asyncio.create_task(stream_coinbase_real_data())
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
        <title>Dashboard - Datos Privados Reales</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Courier New', monospace;
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
            .header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .brokers { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .card {
                background: #1a1f3a;
                border: 2px solid #00ff00;
                padding: 20px;
                border-radius: 5px;
            }
            .card h2 { margin-bottom: 15px; font-size: 1.8em; }
            .status { display: flex; gap: 10px; margin-bottom: 20px; }
            .dot { width: 12px; height: 12px; border-radius: 50%; }
            .connected { background: #00ff00; }
            .disconnected { background: #ff0000; }
            .section { margin: 20px 0; }
            .section-title { 
                border-bottom: 1px solid #00ff00;
                padding-bottom: 5px;
                margin-bottom: 10px;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.9em;
            }
            th, td { 
                padding: 8px;
                text-align: right;
                border-bottom: 1px solid #00ff00;
            }
            th { background: #0a0e27; }
            tr:hover { background: #0f1432; }
            .positive { color: #00ff00; }
            .negative { color: #ff0000; }
            .error { color: #ff6666; background: #1a0a0a; padding: 10px; }
            .loading { color: #888; }
            .big-number { font-size: 1.5em; font-weight: bold; }
            @media (max-width: 1024px) { .brokers { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>DASHBOARD - DATOS PRIVADOS REALES</h1>
                <p>Schwab & Coinbase WebSocket Streaming</p>
            </div>
            
            <div class="brokers">
                <!-- SCHWAB -->
                <div class="card">
                    <h2>SCHWAB</h2>
                    <div class="status">
                        <div class="dot disconnected" id="schwab-dot"></div>
                        <span id="schwab-status">Conectando...</span>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">BALANCE</div>
                        <div id="schwab-balance">Cargando...</div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">POSICIONES ABIERTAS</div>
                        <div id="schwab-positions">Cargando...</div>
                    </div>
                    
                    <div id="schwab-error" style="display:none;" class="error"></div>
                </div>
                
                <!-- COINBASE -->
                <div class="card">
                    <h2>COINBASE</h2>
                    <div class="status">
                        <div class="dot disconnected" id="coinbase-dot"></div>
                        <span id="coinbase-status">Conectando...</span>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">BALANCE TOTAL</div>
                        <div id="coinbase-total" class="big-number">$0.00</div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">WALLETS</div>
                        <div id="coinbase-accounts">Cargando...</div>
                    </div>
                    
                    <div id="coinbase-error" style="display:none;" class="error"></div>
                </div>
            </div>
        </div>
        
        <script>
            const schwabWs = new WebSocket("ws://localhost:8000/ws/schwab");
            const coinbaseWs = new WebSocket("ws://localhost:8000/ws/coinbase");
            
            schwabWs.onmessage = (e) => {
                const msg = JSON.parse(e.data);
                const data = msg.data;
                
                document.getElementById("schwab-dot").className = "dot " + (data.connected ? "connected" : "disconnected");
                document.getElementById("schwab-status").textContent = data.connected ? "CONECTADO" : "DESCONECTADO";
                
                if (data.error) {
                    document.getElementById("schwab-error").style.display = "block";
                    document.getElementById("schwab-error").textContent = "ERROR: " + data.error;
                    return;
                }
                
                document.getElementById("schwab-error").style.display = "none";
                
                // Balance
                if (data.balance) {
                    const b = data.balance;
                    document.getElementById("schwab-balance").innerHTML = `
                        <table>
                            <tr><td>Saldo Liquidacion:</td><td class="positive big-number">$${b.liquidation_value.toLocaleString('en-US', {maximumFractionDigits: 2})}</td></tr>
                            <tr><td>Cash:</td><td>$${b.cash.toLocaleString('en-US', {maximumFractionDigits: 2})}</td></tr>
                            <tr><td>Poder de Compra:</td><td>$${b.buying_power.toLocaleString('en-US', {maximumFractionDigits: 2})}</td></tr>
                            <tr><td>Cuenta:</td><td>${b.account_number}</td></tr>
                        </table>
                    `;
                }
                
                // Posiciones
                if (data.positions && data.positions.length > 0) {
                    let html = "<table><tr><th>SIMBOLO</th><th>CANTIDAD</th><th>PRECIO</th><th>VALOR</th><th>GANANCIA</th></tr>";
                    data.positions.forEach(pos => {
                        const gain = pos.gain_loss >= 0 ? "positive" : "negative";
                        html += `<tr>
                            <td>${pos.symbol}</td>
                            <td>${pos.quantity}</td>
                            <td>$${pos.average_price.toFixed(2)}</td>
                            <td>$${pos.market_value.toLocaleString('en-US', {maximumFractionDigits: 2})}</td>
                            <td class="${gain}">$${pos.gain_loss.toLocaleString('en-US', {maximumFractionDigits: 2})}</td>
                        </tr>`;
                    });
                    html += "</table>";
                    document.getElementById("schwab-positions").innerHTML = html;
                } else {
                    document.getElementById("schwab-positions").innerHTML = "<span class='loading'>Sin posiciones abiertas</span>";
                }
            };
            
            coinbaseWs.onmessage = (e) => {
                const msg = JSON.parse(e.data);
                const data = msg.data;
                
                document.getElementById("coinbase-dot").className = "dot " + (data.connected ? "connected" : "disconnected");
                document.getElementById("coinbase-status").textContent = data.connected ? "CONECTADO" : "DESCONECTADO";
                
                if (data.error) {
                    document.getElementById("coinbase-error").style.display = "block";
                    document.getElementById("coinbase-error").textContent = "ERROR: " + data.error;
                    return;
                }
                
                document.getElementById("coinbase-error").style.display = "none";
                
                // Total
                document.getElementById("coinbase-total").textContent = "$" + data.total_balance.toLocaleString('en-US', {maximumFractionDigits: 2});
                
                // Cuentas
                if (data.accounts && data.accounts.length > 0) {
                    let html = "<table><tr><th>MONEDA</th><th>DISPONIBLE</th><th>EN ESPERA</th><th>TOTAL</th></tr>";
                    data.accounts.forEach(acc => {
                        html += `<tr>
                            <td>${acc.currency}</td>
                            <td class="positive">${acc.available.toFixed(8)}</td>
                            <td>${acc.hold.toFixed(8)}</td>
                            <td>${acc.balance.toFixed(8)}</td>
                        </tr>`;
                    });
                    html += "</table>";
                    document.getElementById("coinbase-accounts").innerHTML = html;
                } else {
                    document.getElementById("coinbase-accounts").innerHTML = "<span class='loading'>Sin fondos</span>";
                }
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
        coinbase_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
