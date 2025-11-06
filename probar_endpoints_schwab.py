"""
FASE 1.4-VAL - Intentar endpoint alternativo /accountsummary
"""

import json
import requests
from pathlib import Path
from datetime import datetime

print("\n" + "="*80)
print("FASE 1.4-VAL: INTENTANDO ENDPOINT ALTERNATIVO")
print("="*80)

try:
    # Cargar token
    token_file = Path("hub/current_token.json")
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    access_token = token_data.get('access_token')
    print(f"✅ Token cargado: {access_token[:30]}...")
    print()
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Intentar múltiples endpoints
    endpoints = [
        ("https://api.schwabapi.com/trader/v1/accounts", "trader/v1/accounts"),
        ("https://api.schwabapi.com/trader/v1/accountsummary", "trader/v1/accountsummary"),
        ("https://api.schwabapi.com/v1/accounts/summary", "v1/accounts/summary"),
    ]
    
    for url, name in endpoints:
        print(f"Intentando: {name}")
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  ✅ ÉXITO: {resp.text[:100]}")
                break
            else:
                print(f"  Response: {resp.text[:60]}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

except Exception as e:
    print(f"Error: {e}")
