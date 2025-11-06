from flask import Flask, jsonify
from flask_cors import CORS
import os
import jwt
import time
import requests
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Coinbase
COINBASE_API_KEY = "organizations/60f9fe57-7692-4afa-a915-eedba4b90027/apiKeys/f8a591c0-fccc-4eb6-9d3f-6e42f7ab2c6e"
COINBASE_PRIVATE_KEY = """-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIFFB9yqMSLEvsI6xNlpFNgJo5AIsDq8arOKDyHXEs6tjoAoGCCqGSM49
AwEHoUQDQgAEBVnuU0a5qi+4YzqDWFD0KHM0gPIpZVt3d4VAFRJ9WeVS46DKUBkH
d2hPPXNv+oUVWM5RENslFPG/GTCh6jH+Rw==
-----END EC PRIVATE KEY-----"""

def get_jwt_token():
    """Genera JWT para Coinbase"""
    try:
        key = serialization.load_pem_private_key(
            COINBASE_PRIVATE_KEY.encode(),
            password=None
        )
        payload = {
            'sub': COINBASE_API_KEY,
            'iss': 'cdp_service_sk',
            'nbf': int(time.time()),
            'exp': int(time.time()) + 120
        }
        return jwt.encode(payload, key, algorithm='ES256')
    except Exception as e:
        print(f"Error generando JWT: {e}")
        raise

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/coinbase-accounts', methods=['GET'])
def coinbase_accounts():
    """Obtiene cuentas de Coinbase - CORREGIDO"""
    try:
        token = get_jwt_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://api.coinbase.com/api/v3/brokerage/accounts',
            headers=headers,
            timeout=10
        )
        
        # ✅ CORRECCIÓN: Verifica status_code ANTES de .json()
        if response.status_code != 200:
            return jsonify({
                "error": f"Coinbase API error: {response.status_code}",
                "details": response.text,
                "status": "error"
            }), response.status_code
        
        # ✅ Ahora sí puedes hacer .json()
        data = response.json()
        
        return jsonify({
            "status": "success",
            "accounts": data.get('accounts', []),
            "raw": data
        })
        
    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout conectando a Coinbase", "status": "error"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error de conexión: {str(e)}", "status": "error"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/coinbase-token', methods=['GET'])
def coinbase_token():
    """Devuelve JWT válido para Coinbase"""
    try:
        token = get_jwt_token()
        return jsonify({"token": token, "expires_in": 120})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Iniciando server...")
    app.run(debug=False, port=5000, host='127.0.0.1')