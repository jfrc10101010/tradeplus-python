"""
DEBUG: Verificar EXACTAMENTE qué devuelve /v1/userPreference

Imprime la respuesta completa para ver los datos reales.
"""

import json
from hub.managers.schwab_token_manager import SchwabTokenManager

# Obtener token válido
token_manager = SchwabTokenManager(config_path="hub")
token = token_manager.get_current_token()

print(f"\n✅ Token: {token[:30]}...\n")

# Hacer la petición
import requests

url = "https://api.schwabapi.com/trader/v1/userPreference"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"
}

print(f"→ GET {url}\n")
response = requests.get(url, headers=headers, timeout=10)

print(f"← Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    
    print("="*80)
    print("RESPUESTA COMPLETA:")
    print("="*80)
    print(json.dumps(data, indent=2))
    print("="*80)
    
    # Extraer streamerInfo
    if "streamerInfo" in data:
        streamer_info = data["streamerInfo"]
        
        print(f"\nTipo de streamerInfo: {type(streamer_info)}")
        print(f"Contenido: {json.dumps(streamer_info, indent=2)}")
        
        # Si es array
        if isinstance(streamer_info, list):
            print(f"\n✅ streamerInfo es ARRAY con {len(streamer_info)} elemento(s)")
            if len(streamer_info) > 0:
                info = streamer_info[0]
                
                print(f"\n" + "="*80)
                print("CAMPOS EXTRAÍDOS:")
                print("="*80)
                print(f"streamerSocketUrl: {info.get('streamerSocketUrl')}")
                print(f"schwabClientCustomerId: {info.get('schwabClientCustomerId')}")
                print(f"schwabClientCorrelId: {info.get('schwabClientCorrelId')}")
                print(f"schwabClientChannel: {info.get('schwabClientChannel')}")
                print(f"schwabClientFunctionId: {info.get('schwabClientFunctionId')}")
                print("="*80)
        
        # Si es dict
        elif isinstance(streamer_info, dict):
            print(f"\n✅ streamerInfo es DICT")
            print(f"\n" + "="*80)
            print("CAMPOS EXTRAÍDOS:")
            print("="*80)
            print(f"streamerSocketUrl: {streamer_info.get('streamerSocketUrl')}")
            print(f"schwabClientCustomerId: {streamer_info.get('schwabClientCustomerId')}")
            print(f"schwabClientCorrelId: {streamer_info.get('schwabClientCorrelId')}")
            print(f"schwabClientChannel: {streamer_info.get('schwabClientChannel')}")
            print(f"schwabClientFunctionId: {streamer_info.get('schwabClientFunctionId')}")
            print("="*80)
else:
    print(f"ERROR: {response.status_code}")
    print(response.text)
