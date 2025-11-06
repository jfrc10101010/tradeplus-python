import json, requests
from pathlib import Path

token_file = Path('hub/current_token.json')
with open(token_file) as f:
    token = json.load(f)['access_token']

resp = requests.get('https://api.schwabapi.com/trader/v1/accounts', 
                    headers={'Authorization': f'Bearer {token}'})

print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    print(f'Cuentas: {len(data)}')
    if data:
        acc = data[0]['securitiesAccount']
        bal = acc['initialBalances']
        print(f'Account Type: {acc["type"]}')
        print(f'Account Number: {acc["accountNumber"]}')
        print(f'Cash Available: {bal["cashAvailableForTrading"]}')
        print(f'Liquidation Value: {bal["liquidationValue"]}')
        
        # Guardar completo
        with open('validacion_fase_1_4_data.json', 'w') as f:
            json.dump({
                'timestamp': '',
                'http_status': 200,
                'accounts_found': len(data),
                'first_account': acc
            }, f, indent=2)
        print('✅ Guardado en validacion_fase_1_4_data.json')
