from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import json
import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)
CORS(app)

print("=== SERVIDOR FLASK INICIADO ===")

# Leer credenciales del JSON
with open('apicoinbase1fullcdp_api_key.json', 'r') as f:
    cb_config = json.load(f)
    COINBASE_API_KEY = cb_config['name']
    COINBASE_PRIVATE_KEY = cb_config['privateKey']

print(f"✅ API Key Coinbase cargada: {COINBASE_API_KEY[:50]}...")

def generate_jwt():
    """Genera JWT para Coinbase - CORRECTO según docs oficiales"""
    import secrets
    
    key = serialization.load_pem_private_key(
        COINBASE_PRIVATE_KEY.encode(),
        password=None
    )
    
    timestamp = int(time.time())
    request_method = 'GET'
    request_host = 'api.coinbase.com'
    request_path = '/api/v3/brokerage/accounts'
    
    # ✅ CRÍTICO: uri debe incluir HOST + PATH
    uri = f"{request_method} {request_host}{request_path}"
    
    payload = {
        'sub': COINBASE_API_KEY,
        'iss': 'cdp',
        'nbf': timestamp,
        'exp': timestamp + 120,
        'uri': uri
    }
    
    headers = {
        'kid': COINBASE_API_KEY,
        'nonce': secrets.token_hex()  # ✅ Requerido por Coinbase
    }
    
    print(f"DEBUG JWT URI: {uri}")
    print(f"DEBUG Payload: {payload}")
    
    return jwt.encode(payload, key, algorithm='ES256', headers=headers)

@app.route('/api/health', methods=['GET'])
def health():
    """Health check - verifica status del Hub en puerto 8000"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=2)
        return jsonify(response.json())
    except:
        return jsonify({
            "status": "unavailable",
            "hub": {
                "connected": False,
                "coinbase": False,
                "schwab": False
            }
        })

@app.route('/test', methods=['GET'])
def test_page():
    """Página en vivo mostrando ambos WebSockets funcionando en tiempo real"""
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TradePlus - WebSockets Live Demo</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Monaco', 'Courier New', monospace;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #00ff00;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                text-align: center;
                margin-bottom: 30px;
                text-shadow: 0 0 10px #00ff00;
            }
            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .card {
                background: rgba(0, 0, 0, 0.5);
                border: 2px solid #00ff00;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
            }
            .card h2 {
                font-size: 1.5em;
                margin-bottom: 15px;
                border-bottom: 2px solid #00ff00;
                padding-bottom: 10px;
            }
            .status {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding: 10px;
                background: rgba(0, 255, 0, 0.05);
                border-left: 3px solid #00ff00;
            }
            .status-label {
                font-weight: bold;
            }
            .status-value {
                font-weight: bold;
                color: #ffff00;
            }
            .status.connected .status-value {
                color: #00ff00;
            }
            .status.disconnected .status-value {
                color: #ff0000;
            }
            .ticks-container {
                max-height: 400px;
                overflow-y: auto;
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #00ff00;
                border-radius: 4px;
                padding: 10px;
            }
            .tick {
                padding: 8px;
                margin-bottom: 5px;
                background: rgba(0, 255, 0, 0.1);
                border-left: 3px solid #00ff00;
                border-radius: 2px;
                font-size: 0.9em;
                animation: slideIn 0.3s ease-out;
            }
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            .timestamp {
                color: #888;
                font-size: 0.8em;
            }
            .symbol {
                color: #ffff00;
                font-weight: bold;
            }
            .price {
                color: #00ff00;
                font-weight: bold;
            }
            .hub-status {
                grid-column: 1 / -1;
                text-align: center;
                padding: 20px;
                background: rgba(0, 255, 0, 0.1);
                border: 2px solid #00ff00;
                border-radius: 8px;
            }
            .hub-status.error {
                background: rgba(255, 0, 0, 0.1);
                border-color: #ff0000;
            }
            @media (max-width: 768px) {
                .grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 TradePlus - WebSockets en Vivo</h1>
            
            <div class="hub-status" id="hubStatus">
                ⏳ Conectando Hub...
            </div>
            
            <div class="grid">
                <!-- COINBASE -->
                <div class="card">
                    <h2>💰 Coinbase (BTC-USD, ETH-USD)</h2>
                    <div class="status" id="coinbaseStatus">
                        <span class="status-label">Estado:</span>
                        <span class="status-value">Desconectado</span>
                    </div>
                    <div class="status">
                        <span class="status-label">Ticks recibidos:</span>
                        <span class="status-value" id="coinbaseCount">0</span>
                    </div>
                    <div class="status">
                        <span class="status-label">Ticks/seg:</span>
                        <span class="status-value" id="coinbaseRate">0.0</span>
                    </div>
                    <h3 style="margin-top: 15px; margin-bottom: 10px;">Feed en vivo:</h3>
                    <div class="ticks-container" id="coinbaseTicks"></div>
                </div>
                
                <!-- SCHWAB -->
                <div class="card">
                    <h2>📈 Schwab (Equities)</h2>
                    <div class="status" id="schwabStatus">
                        <span class="status-label">Estado:</span>
                        <span class="status-value">Desconectado</span>
                    </div>
                    <div class="status">
                        <span class="status-label">Ticks recibidos:</span>
                        <span class="status-value" id="schwabCount">0</span>
                    </div>
                    <div class="status">
                        <span class="status-label">Ticks/seg:</span>
                        <span class="status-value" id="schwabRate">0.0</span>
                    </div>
                    <h3 style="margin-top: 15px; margin-bottom: 10px;">Feed en vivo:</h3>
                    <div class="ticks-container" id="schwabTicks"></div>
                </div>
            </div>
        </div>
        
        <script>
            let coinbaseTicks = 0;
            let schwabTicks = 0;
            let startTime = Date.now();
            let lastTicks = {};
            
            async function updateTicks() {
                try {
                    const response = await fetch('http://localhost:8000/ticks');
                    if (response.ok) {
                        const ticks = await response.json();
                        
                        for (const [symbol, tick] of Object.entries(ticks)) {
                            // Evitar duplicados
                            if (lastTicks[symbol] === JSON.stringify(tick)) continue;
                            lastTicks[symbol] = JSON.stringify(tick);
                            
                            const tickEl = document.createElement('div');
                            tickEl.className = 'tick';
                            const timestamp = new Date().toLocaleTimeString();
                            
                            if (symbol.includes('BTC') || symbol.includes('ETH')) {
                                coinbaseTicks++;
                                tickEl.innerHTML = `
                                    <span class="timestamp">[${timestamp}]</span>
                                    <span class="symbol">${symbol}</span> 
                                    Price: <span class="price">$${parseFloat(tick.price || 0).toFixed(2)}</span>
                                    (Side: ${tick.side || 'N/A'})
                                `;
                                const container = document.getElementById('coinbaseTicks');
                                container.insertBefore(tickEl, container.firstChild);
                                if (container.children.length > 50) {
                                    container.removeChild(container.lastChild);
                                }
                                document.getElementById('coinbaseCount').textContent = coinbaseTicks;
                            } else {
                                schwabTicks++;
                                tickEl.innerHTML = `
                                    <span class="timestamp">[${timestamp}]</span>
                                    <span class="symbol">${symbol}</span> 
                                    Price: <span class="price">$${parseFloat(tick.price || 0).toFixed(2)}</span>
                                    (Vol: ${tick.volume || 0})
                                `;
                                const container = document.getElementById('schwabTicks');
                                container.insertBefore(tickEl, container.firstChild);
                                if (container.children.length > 50) {
                                    container.removeChild(container.lastChild);
                                }
                                document.getElementById('schwabCount').textContent = schwabTicks;
                            }
                            
                            updateRates();
                        }
                    }
                } catch (e) {
                    console.log('Hub API no disponible aún...');
                }
            }
            
            function updateRates() {
                const elapsed = (Date.now() - startTime) / 1000;
                document.getElementById('coinbaseRate').textContent = (coinbaseTicks / elapsed).toFixed(2);
                document.getElementById('schwabRate').textContent = (schwabTicks / elapsed).toFixed(2);
            }
            
            async function updateStatus() {
                try {
                    const response = await fetch('/api/health');
                    const data = await response.json();
                    
                    const hubEl = document.getElementById('hubStatus');
                    const isConnected = data.hub && (data.hub.coinbase || data.hub.schwab);
                    
                    if (isConnected) {
                        hubEl.className = 'hub-status';
                        const services = [];
                        if (data.hub.coinbase) services.push('✅ Coinbase');
                        if (data.hub.schwab) services.push('✅ Schwab');
                        hubEl.textContent = `🟢 HUB CONECTADO - ${services.join(' | ')}`;
                    } else {
                        hubEl.className = 'hub-status error';
                        hubEl.textContent = '🔴 HUB DESCONECTADO';
                    }
                    
                    const coinbaseEl = document.getElementById('coinbaseStatus');
                    if (data.hub && data.hub.coinbase) {
                        coinbaseEl.className = 'status connected';
                        coinbaseEl.innerHTML = '<span class="status-label">Estado:</span><span class="status-value">✅ Conectado</span>';
                    } else {
                        coinbaseEl.className = 'status disconnected';
                        coinbaseEl.innerHTML = '<span class="status-label">Estado:</span><span class="status-value">❌ Desconectado</span>';
                    }
                    
                    const schwabEl = document.getElementById('schwabStatus');
                    if (data.hub && data.hub.schwab) {
                        schwabEl.className = 'status connected';
                        schwabEl.innerHTML = '<span class="status-label">Estado:</span><span class="status-value">✅ Conectado</span>';
                    } else {
                        schwabEl.className = 'status disconnected';
                        schwabEl.innerHTML = '<span class="status-label">Estado:</span><span class="status-value">❌ Desconectado</span>';
                    }
                    
                } catch (e) {
                    console.log('Status check error:', e);
                }
            }
            
            // Actualizar cada 500ms
            setInterval(updateTicks, 500);
            setInterval(updateStatus, 2000);
            updateStatus();
            updateTicks();
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/coinbase-accounts', methods=['GET'])
def coinbase_accounts():
    print("=== INICIANDO PETICIÓN COINBASE ===")
    print("Endpoint coinbase-accounts llamado!")
    try:
        print("Generando JWT...")
        token = generate_jwt()
        print(f"JWT generado: {token[:50]}...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        print("Enviando petición a Coinbase...")
        response = requests.get(
            'https://api.coinbase.com/api/v3/brokerage/accounts',
            headers=headers,
            timeout=10
        )
        print(f"Respuesta recibida: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "status": "success",
                "accounts": data.get('accounts', [])
            })
        else:
            print(f"Error details: {response.text}")
            return jsonify({
                "error": f"HTTP {response.status_code}",
                "details": response.text,
                "status": "error"
            }), response.status_code
    except Exception as e:
        print(f"Excepción: {str(e)}")
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    print("\n🚀 Servidor Flask iniciado en http://localhost:5000")
    print("📊 Dashboard disponible en http://localhost:5000/test")
    print("⚠️  Asegúrate de que el Hub FastAPI está corriendo en puerto 8000")
    print("    Ejecuta: python -m hub.main\n")
    app.run(debug=False, port=5000, host='0.0.0.0')