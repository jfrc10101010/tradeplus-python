from flask import Flask, jsonify
from flask_cors import CORS
import json
import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization

app = Flask(__name__)
CORS(app)

print("=== SERVIDOR CARGADO CON MODIFICACIONES ===")

# Leer credenciales del JSON
with open('apicoinbase1fullcdp_api_key.json', 'r') as f:
    cb_config = json.load(f)
    COINBASE_API_KEY = cb_config['name']
    COINBASE_PRIVATE_KEY = cb_config['privateKey']

print(f"OK API Key: {COINBASE_API_KEY[:50]}...")

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
    return jsonify({"status": "ok"})

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
    app.run(debug=False, port=5000, host='0.0.0.0')