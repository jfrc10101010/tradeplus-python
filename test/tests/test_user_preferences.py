import json, requests
from pathlib import Path

token_file = Path('current_token.json')
with open(token_file) as f:
    token = json.load(f).get('access_token')

url = 'https://api.schwabapi.com/trader/v1/user/preferences'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

print("=" * 80)
print("PROBANDO ENDPOINT: /v1/user/preferences")
print("=" * 80)

response = requests.get(url, headers=headers, timeout=10)
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nEstructura de respuesta:")
    print(json.dumps(data, indent=2)[:1000])
    
    if 'streamerInfo' in data:
        print(f"\n✓ streamerInfo encontrado:")
        print(json.dumps(data['streamerInfo'], indent=2))
    else:
        print(f"\n✗ streamerInfo NO encontrado")
        print(f"Keys disponibles: {list(data.keys())}")
else:
    print(f"\nError: {response.text[:500]}")
