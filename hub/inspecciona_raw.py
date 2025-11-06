"""
Inspecciona la respuesta REAL de la API sin interpretaciones
Muestra la estructura exacta de lo que devuelve Coinbase
"""
import sys
import json
import requests
from pathlib import Path
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from managers.coinbase_jwt_manager import CoinbaseJWTManager


def inspect_raw_response(endpoint_name, method, path):
    """Inspecciona la respuesta RAW exacta"""
    print(f"\n{'='*80}")
    print(f"🔍 INSPECCIONANDO: {endpoint_name.upper()}")
    print(f"   Method: {method} {path}")
    print(f"{'='*80}\n")
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        jwt_token = manager.generate_jwt_for_endpoint(method=method, path=path)
        
        url = f"https://api.coinbase.com{path}"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"HTTP Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("RAW JSON RESPONSE (COMPLETO):")
            print(json.dumps(data, indent=2)[:5000])  # Primeros 5000 caracteres
            
            # Analizar estructura
            print(f"\n📊 ANÁLISIS DE ESTRUCTURA:")
            print(f"   Tipo: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"   Keys principales: {list(data.keys())}")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"     - '{key}': LIST con {len(value)} elementos")
                        if len(value) > 0:
                            print(f"       Primer elemento keys: {list(value[0].keys())}")
                    else:
                        print(f"     - '{key}': {type(value).__name__}")
            
            return data
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(response.text[:1000])
            return None
    
    except Exception as e:
        print(f"EXCEPCIÓN: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Inspecciona todos los endpoints"""
    print("\n" + "#"*80)
    print("# INSPECCIÓN RAW DE RESPUESTAS COINBASE API")
    print("#"*80)
    
    endpoints = [
        ('Accounts', 'GET', '/api/v3/brokerage/accounts'),
        ('Orders', 'GET', '/api/v3/brokerage/orders/historical/batch'),
        ('Fills', 'GET', '/api/v3/brokerage/orders/historical/fills'),
        ('Portfolios', 'GET', '/api/v3/brokerage/portfolios'),
    ]
    
    all_responses = {}
    
    for name, method, path in endpoints:
        data = inspect_raw_response(name, method, path)
        all_responses[name] = data
    
    # Guardar todo completo
    print(f"\n\n{'='*80}")
    print("💾 GUARDANDO RESPUESTAS COMPLETAS")
    print(f"{'='*80}\n")
    
    output_file = Path('hub/raw_api_responses.json')
    try:
        with open(output_file, 'w') as f:
            json.dump(all_responses, f, indent=2)
        print(f"✅ Guardado en: {output_file}")
    except Exception as e:
        print(f"❌ Error guardando: {e}")


if __name__ == "__main__":
    main()
