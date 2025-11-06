import json
import requests
from pathlib import Path

token_file = Path('hub/current_token.json')
with open(token_file) as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {'Authorization': f'Bearer {token}'}

resp = requests.get('https://api.schwabapi.com/trader/v1/accounts', headers=headers, timeout=5)

if resp.status_code == 200:
    data = resp.json()
    print('✅ 200 OK - Token válido')
    print(f'Cuentas encontradas: {len(data)}')
    print()
    for i, acc in enumerate(data[:2], 1):
        sec = acc.get('securitiesAccount', {})
        print(f'Cuenta {i}:')
        print(f'  Número: {sec.get("accountNumber")[-4:]}...')
        print(f'  Tipo: {sec.get("type")}')
        bal = sec.get('balances', {})
        print(f'  Cash: ${bal.get("cashBalance", "N/A")}')
        print(f'  Equity: ${bal.get("accountValue", "N/A")}')
        print()
else:
    print(f'Status: {resp.status_code}')
    print(resp.text[:200])
