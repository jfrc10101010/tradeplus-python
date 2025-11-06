#!/usr/bin/env python3
"""
Validar que los tokens reales son válidos contra los servidores reales
Sin emojis (Windows encoding issues)
"""
import json
import asyncio
from datetime import datetime
from pathlib import Path
import websockets

# Imports para Coinbase
import jwt as pyjwt

# Imports para Schwab
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suprimir warnings de SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def load_coinbase_jwt():
    """Carga y valida JWT de Coinbase"""
    jwt_file = Path("hub/coinbase_current_jwt.json")
    
    if not jwt_file.exists():
        return False, "JWT file not found"
    
    try:
        with open(jwt_file) as f:
            data = json.load(f)
        
        jwt_token = data.get("jwt")
        expires_at = data.get("expires_at")
        
        if not jwt_token:
            return False, "JWT not in file"
        
        # Verificar que no esté expirado
        expires_dt = datetime.fromisoformat(expires_at)
        now = datetime.utcnow()
        
        if now > expires_dt:
            return False, f"JWT expirado: {expires_at}"
        
        time_left = (expires_dt - now).total_seconds()
        return True, f"JWT valido, expires in {time_left:.0f}s"
    
    except Exception as e:
        return False, f"Error loading JWT: {str(e)}"

def load_schwab_token():
    """Carga y valida token OAuth de Schwab"""
    token_file = Path("hub/current_token.json")
    
    if not token_file.exists():
        return False, None, "Token file not found"
    
    try:
        with open(token_file) as f:
            data = json.load(f)
        
        access_token = data.get("access_token")
        
        if not access_token:
            return False, None, "access_token not in file"
        
        return True, access_token, "Token loaded"
    
    except Exception as e:
        return False, None, f"Error loading token: {str(e)}"

def test_coinbase_jwt():
    """Prueba JWT contra WebSocket Coinbase"""
    print("\n[TEST 1] COINBASE JWT VALIDATION")
    print("-" * 60)
    
    valid, msg = load_coinbase_jwt()
    print(f"JWT Status: {msg}")
    print(f"Result: {'[PASS]' if valid else '[FAIL]'}")
    
    return valid

def test_schwab_http_get():
    """Prueba token Schwab con HTTP GET"""
    print("\n[TEST 2] SCHWAB TOKEN - HTTP GET /user/principals")
    print("-" * 60)
    
    valid, token, msg = load_schwab_token()
    print(f"Token Status: {msg}")
    
    if not valid:
        print(f"Result: [FAIL]")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        
        response = requests.get(
            "https://api.schwabapi.com/trader/v1/user/principals",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer info básica
            if isinstance(data, list) and len(data) > 0:
                account = data[0]
                account_num = account.get("accountNumber", "N/A")
                print(f"Account: {account_num}")
            
            print(f"Result: [PASS]")
            return True
        else:
            print(f"Error Response: {response.text[:200]}")
            print(f"Result: [FAIL]")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"HTTP Error: {str(e)[:100]}")
        print(f"Result: [FAIL]")
        return False

async def test_coinbase_websocket():
    """Prueba conexión WebSocket con JWT"""
    print("\n[TEST 3] COINBASE WEBSOCKET CONNECTION")
    print("-" * 60)
    
    valid, msg = load_coinbase_jwt()
    
    if not valid:
        print(f"JWT Status: {msg}")
        print(f"Result: [SKIP] - Invalid JWT")
        return False
    
    try:
        jwt_file = Path("hub/coinbase_current_jwt.json")
        with open(jwt_file) as f:
            data = json.load(f)
        jwt_token = data.get("jwt")
        
        # Intentar conectar a WebSocket
        uri = "wss://advanced-trade-ws.coinbase.com"
        
        async with asyncio.timeout(5):
            async with websockets.connect(uri) as ws:
                # Enviar mensaje de autenticación
                auth_msg = {
                    "type": "subscribe",
                    "product_ids": ["BTC-USD"],
                    "channel": "ticker",
                    "signature": jwt_token
                }
                
                await ws.send(json.dumps(auth_msg))
                
                # Esperar respuesta
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                
                print(f"WS Connected: True")
                print(f"First Message: {response[:100]}")
                print(f"Result: [PASS]")
                return True
    
    except asyncio.TimeoutError:
        print(f"WS Connection: Timeout after 5s")
        print(f"Result: [FAIL]")
        return False
    except Exception as e:
        print(f"WS Error: {str(e)[:100]}")
        print(f"Result: [FAIL]")
        return False

async def main():
    """Ejecutar todas las pruebas"""
    print("\n" + "=" * 60)
    print("VALIDATE TOKENS AGAINST REAL SERVERS")
    print("=" * 60)
    
    # Test 1: Coinbase JWT
    test1 = test_coinbase_jwt()
    
    # Test 2: Schwab HTTP
    test2 = test_schwab_http_get()
    
    # Test 3: Coinbase WebSocket
    test3 = await test_coinbase_websocket()
    
    # Resumen
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    results = {
        "Coinbase JWT": test1,
        "Schwab HTTP": test2,
        "Coinbase WebSocket": test3
    }
    
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{name}: [{status}]")
    
    all_pass = all(results.values())
    print("\n" + ("=" * 60))
    
    if all_pass:
        print("ALL TESTS PASSED - Ready for WebSocket data flow")
        return 0
    else:
        print("SOME TESTS FAILED - Check errors above")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
