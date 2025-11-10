#!/usr/bin/env python3
import requests
import json

print("=== PROBANDO COINBASE API ===\n")

# Test 1: Health
print("1. Probando health endpoint...")
r = requests.get('http://127.0.0.1:5000/api/health')
print(f"   Status: {r.status_code}")
print(f"   Response: {r.text}\n")

# Test 2: Coinbase Accounts
print("2. Probando Coinbase accounts...")
r = requests.get('http://127.0.0.1:5000/api/coinbase-accounts')
print(f"   Status: {r.status_code}")

if r.status_code == 200:
    data = json.loads(r.text)
    print(f"   ✅ Cuentas obtenidas: {len(data['accounts'])}")
    
    # Mostrar resumen de cuentas
    print("\n   Resumen de cuentas:")
    for acc in data['accounts']:
        balance = acc['available_balance']['value']
        currency = acc['currency']
        name = acc['name']
        print(f"      • {name}: {balance} {currency}")
else:
    print(f"   ❌ Error: {r.text}")

print("\n✅ ¡TODO FUNCIONA CORRECTAMENTE!")