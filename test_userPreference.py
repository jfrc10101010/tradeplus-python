import json, requests
from pathlib import Path

token_file = Path('current_token.json')
with open(token_file) as f:
    token = json.load(f).get('access_token')

url = 'https://api.schwabapi.com/trader/v1/userPreference'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

print('Probando /v1/userPreference con token FRESCO\n')
response = requests.get(url, headers=headers, timeout=10)
print(f'Status: {response.status_code}\n')

if response.status_code == 200:
    data = response.json()
    if 'streamerInfo' in data:
        info = data['streamerInfo']
        print(f'Type of streamerInfo: {type(info).__name__}')
        
        if isinstance(info, list):
            print(f'streamerInfo es una LISTA con {len(info)} elementos\n')
            if len(info) > 0:
                print('Primer elemento:')
                print(json.dumps(info[0], indent=2)[:500])
        else:
            print('Estructura completa:')
            print(json.dumps(info, indent=2))
    else:
        print('✗ streamerInfo NO encontrado')
        print('Keys disponibles:', list(data.keys()))
else:
    print(f'✗ Error {response.status_code}')
    print(response.text[:500])

