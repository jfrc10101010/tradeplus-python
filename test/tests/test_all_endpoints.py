import json, requests
from pathlib import Path

token_file = Path('current_token.json')
with open(token_file) as f:
    token = json.load(f).get('access_token')

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
base_url = 'https://api.schwabapi.com/trader'

# Probar múltiples endpoints
endpoints = [
    '/v1/user/preferences',
    '/v1/user/principals',
    '/v1/accounts',
    '/v1/streaming',
    '/user/preferences',
    '/user/principals',
]

print("=" * 80)
print("PROBANDO ENDPOINTS DE SCHWAB")
print("=" * 80)

for endpoint in endpoints:
    url = f"{base_url}{endpoint}"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"\n{endpoint}")
        print(f"  Status: {response.status_code}", end="")
        
        if response.status_code == 200:
            print(" ✓")
            data = response.json()
            keys = list(data.keys()) if isinstance(data, dict) else f"List({len(data)})"
            print(f"  Keys/Type: {keys}")
            
            # Buscar streamerInfo
            if isinstance(data, dict) and 'streamerInfo' in data:
                print(f"  ✓ ENCONTRADO streamerInfo!")
            elif isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    keys = list(data[0].keys())
                    print(f"  First item keys: {keys}")
                    if 'streamerInfo' in keys:
                        print(f"  ✓ streamerInfo en primer elemento!")
        else:
            print(f" ✗")
            err_msg = response.text[:100]
            print(f"  Error: {err_msg}")
    except Exception as e:
        print(f"\n{endpoint}")
        print(f"  Exception: {str(e)[:80]}")

print("\n" + "=" * 80)
