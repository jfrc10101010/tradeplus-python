import json, requests
from pathlib import Path

token_file = Path('current_token.json')
with open(token_file) as f:
    token = json.load(f).get('access_token')

url = 'https://api.schwabapi.com/trader/v1/accounts'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

response = requests.get(url, headers=headers, timeout=10)
data = response.json()

print("=" * 80)
print("ESTRUCTURA COMPLETA DE /v1/accounts:")
print("=" * 80)
print(json.dumps(data, indent=2))

