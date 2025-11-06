"""
FASE 1.4-VAL - VALIDACIÓN REAL CON TOKEN OAUTH2
Usar Token de SchwabTokenManager para acceder a balance REAL de Schwab
"""

import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path

print("\n" + "="*80)
print("FASE 1.4-VAL: VALIDACIÓN REAL CON TOKEN OAUTH2")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

try:
    # 1. Leer Token del archivo
    print("📋 Leyendo Token guardado...")
    token_file = Path("hub/current_token.json")
    
    if not token_file.exists():
        print(f"   ❌ Archivo no encontrado: {token_file}")
        sys.exit(1)
    
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    access_token = token_data.get('access_token')
    if not access_token:
        print("   ❌ Token no encontrado en archivo")
        sys.exit(1)
    
    print(f"   ✅ Token cargado: {access_token[:30]}...")
    print(f"   Válido hasta: {token_data.get('expires_at')}")
    print()
    
    # 2. Hacer HTTP GET a Schwab
    print("🌐 Llamando API REST de Schwab...")
    print("   Endpoint: https://api.schwabapi.com/trader/v1/accounts")
    print()
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        "https://api.schwabapi.com/trader/v1/accounts",
        headers=headers,
        timeout=10
    )
    
    print(f"📊 Respuesta HTTP: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ 200 OK - Autenticación exitosa")
        print()
        
        accounts = response.json()  # Array de cuentas
        
        # 3. Mostrar cuentas
        print("💰 CUENTAS DE SCHWAB ENCONTRADAS:")
        print()
        
        if accounts:
            for i, account in enumerate(accounts[:2], 1):  # Mostrar primeras 2
                sec = account.get('securitiesAccount', {})
                account_number = sec.get('accountNumber', '')
                account_type = sec.get('type', '')
                
                # Balances están en initialBalances
                balances = sec.get('initialBalances', {})
                cash_available = balances.get('cashAvailableForTrading', 'N/A')
                cash_withdrawal = balances.get('cashAvailableForWithdrawal', 'N/A')
                liquidation = balances.get('liquidationValue', 'N/A')
                
                
                print(f"   Cuenta {i}:")
                print(f"      Número: {account_number[-4:]}...")
                print(f"      Tipo: {account_type}")
                print(f"      Cash para Trading: ${cash_available}")
                print(f"      Cash para Withdrawal: ${cash_withdrawal}")
                print(f"      Liquidation Value: ${liquidation}")
                print()
        
        # 4. Guardar evidencia
        evidencia = {
            "timestamp": datetime.now().isoformat(),
            "endpoint": "https://api.schwabapi.com/trader/v1/accounts",
            "http_status": response.status_code,
            "token_used": access_token[:30] + "...",
            "token_valid_until": token_data.get('expires_at'),
            "accounts_found": len(accounts),
            "first_account_sample": accounts[0] if accounts else None
        }
        
        with open("validacion_fase_1_4_data.json", 'w') as f:
            json.dump(evidencia, f, indent=2)
        
        print("✅ Validación exitosa - Datos guardados en validacion_fase_1_4_data.json")
        print()
        print("="*80)
        print("✅ FASE 1.4-VAL: TOKEN FUNCIONA - ACCESO AUTENTICADO A SCHWAB CONFIRMADO")
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
