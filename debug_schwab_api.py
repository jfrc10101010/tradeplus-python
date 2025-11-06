#!/usr/bin/env python3
"""Debug real - investigar exactamente qué devuelve Schwab API"""

import requests
import json
import warnings

warnings.filterwarnings('ignore')

# Cargar token
with open('current_token.json') as f:
    token_data = json.load(f)
    token = token_data.get('access_token')

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json'
}

urls = [
    'https://api.schwabapi.com/trader/v1/user/preferences',
    'https://api.schwabapi.com/trader/v1/accounts',
    'https://api.schwabapi.com/trader/v1/accounts/accountNumbers',
    'https://api.schwabapi.com/trader/v1/user/principals',
]

print("=" * 70)
print("DEBUGGING SCHWAB API - INVESTIGACION REAL")
print("=" * 70)
print()

for url in urls:
    print(f"Testing: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=5, verify=False)
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"  Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"  Top-level keys: {list(data.keys())}")
                
                # Buscar streamerInfo en cualquier lugar
                if 'streamerInfo' in data:
                    print(f"  >>> FOUND streamerInfo at root level")
                    print(f"      Keys: {list(data['streamerInfo'].keys())[:5]}")
                
                # Si es lista, revisar primer elemento
                if isinstance(data, list) and len(data) > 0:
                    print(f"  Is list with {len(data)} items")
                    if 'streamerInfo' in data[0]:
                        print(f"  >>> FOUND streamerInfo in first list item")
                        
            elif isinstance(data, list):
                print(f"  Response is list with {len(data)} items")
                if len(data) > 0:
                    print(f"  First item keys: {list(data[0].keys())[:5]}")
            
            # Print actual response
            print(f"  Full response:")
            print(f"  {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"  Error response:")
            print(f"  {r.text[:200]}")
    
    except Exception as e:
        print(f"  Exception: {e}")
    
    print()

print("=" * 70)
