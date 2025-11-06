"""
FASE 1.3-VAL - VALIDACIÓN REAL CON JWT
Usar JWT de CoinbaseJWTManager para acceder a balance REAL de Coinbase
"""

import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path

print("\n" + "="*80)
print("FASE 1.3-VAL: VALIDACIÓN REAL CON JWT")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

try:
    # 1. Leer JWT del archivo
    print("📋 Leyendo JWT guardado...")
    jwt_file = Path("hub/coinbase_current_jwt.json")
    
    if not jwt_file.exists():
        print(f"   ❌ Archivo no encontrado: {jwt_file}")
        sys.exit(1)
    
    with open(jwt_file, 'r') as f:
        jwt_data = json.load(f)
    
    jwt_token = jwt_data.get('jwt')
    if not jwt_token:
        print("   ❌ JWT no encontrado en archivo")
        sys.exit(1)
    
    print(f"   ✅ JWT cargado: {jwt_token[:30]}...")
    print(f"   Válido hasta: {jwt_data.get('expires_at')}")
    print()
    
    # 2. Hacer HTTP GET a Coinbase
    print("🌐 Llamando API REST de Coinbase...")
    print("   Endpoint: https://api.coinbase.com/api/v3/brokerage/accounts")
    print()
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        "https://api.coinbase.com/api/v3/brokerage/accounts",
        headers=headers,
        timeout=10
    )
    
    print(f"📊 Respuesta HTTP: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ 200 OK - Autenticación exitosa")
        print()
        
        data = response.json()
        
        # 3. Mostrar cuentas
        print("💰 CUENTAS DE COINBASE ENCONTRADAS:")
        print()
        
        accounts = data.get('accounts', [])
        if accounts:
            for i, account in enumerate(accounts[:5], 1):  # Mostrar primeras 5
                account_id = account.get('uuid', '')
                currency = account.get('currency', '')
                balance = account.get('available_balance', {})
                amount = balance.get('amount', '0')
                
                print(f"   Cuenta {i}:")
                print(f"      ID: {account_id[:16]}...")
                print(f"      Moneda: {currency}")
                print(f"      Balance: {amount} {currency}")
                print()
        
        # 4. Guardar evidencia
        evidencia = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": "https://api.coinbase.com/api/v3/brokerage/accounts",
            "http_status": response.status_code,
            "jwt_used": jwt_token[:30] + "...",
            "jwt_valid_until": jwt_data.get('expires_at'),
            "accounts_found": len(accounts),
            "first_accounts": accounts[:3] if accounts else []
        }
        
        with open("validacion_fase_1_3_data.json", 'w') as f:
            json.dump(evidencia, f, indent=2)
        
        print("✅ Validación exitosa - Datos guardados en validacion_fase_1_3_data.json")
        print()
        print("="*80)
        print("✅ FASE 1.3-VAL: JWT FUNCIONA - ACCESO AUTENTICADO A COINBASE CONFIRMADO")
        print("="*80)
        
        exit(0)
    
    else:
        print(f"   ❌ {response.status_code} - Autenticación fallida")
        print(f"   Respuesta: {response.text[:200]}")
        exit(1)

except requests.exceptions.RequestException as e:
    print(f"❌ Error HTTP: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
