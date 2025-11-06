"""
Busca EXACTAMENTE dónde está el balance de $525.57 USD
Verifica todos los endpoints y campos
"""
import sys
import json
import requests
from pathlib import Path
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from managers.coinbase_jwt_manager import CoinbaseJWTManager


def search_in_accounts():
    """Busca balance en endpoint de cuentas con diferentes queries"""
    print("\n" + "="*80)
    print("🔍 BUSCANDO BALANCE USD EN ACCOUNTS")
    print("="*80)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        jwt_token = manager.generate_jwt_for_endpoint(method='GET', path='/api/v3/brokerage/accounts')
        
        url = "https://api.coinbase.com/api/v3/brokerage/accounts"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            accounts = data.get('accounts', [])
            
            print(f"\n✅ Accounts obtenidas: {len(accounts)}\n")
            
            # Buscar USD específicamente
            for acc in accounts:
                if acc.get('currency') == 'USD':
                    print("📌 CUENTA USD ENCONTRADA:")
                    print(json.dumps(acc, indent=2)[:2000])
                    
                    print("\n🔍 TODOS LOS CAMPOS DEL ACCOUNT USD:")
                    for key, value in acc.items():
                        print(f"   {key}: {value}")
            
            # También mostrar todas las llaves disponibles
            print("\n\n📊 TODAS LAS CUENTAS (resumen):")
            for acc in accounts:
                currency = acc.get('currency')
                available = acc.get('available_balance', {}).get('value', 'N/A')
                hold = acc.get('hold', {}).get('value', 'N/A')
                print(f"   {currency:6s} | Available: {available:>10s} | Hold: {hold:>10s}")
        
        return data
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def search_in_products():
    """Busca si hay endpoint de productos/precios"""
    print("\n" + "="*80)
    print("🔍 BUSCANDO PRECIOS Y VALUACIÓN DE PRODUCTOS")
    print("="*80)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        
        # Intentar obtener producto BTC-USD para ver estructura
        products = ['BTC-USD', 'XRP-USD', 'XLM-USD']
        
        for product in products:
            # Este endpoint NO necesita JWT
            url = f"https://api.coinbase.com/api/v1/products/{product}"
            
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n✅ {product}:")
                    print(f"   Price: {data.get('price')}")
                    print(f"   Bid: {data.get('bid')}")
                    print(f"   Ask: {data.get('ask')}")
            except:
                pass
    
    except Exception as e:
        print(f"❌ Error: {e}")


def search_in_portfolio_breakdown():
    """Busca breakdown del portafolio con valuación"""
    print("\n" + "="*80)
    print("🔍 BUSCANDO VALUACIÓN EN PORTFOLIO")
    print("="*80)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        jwt_token = manager.generate_jwt_for_endpoint(
            method='GET',
            path='/api/v3/brokerage/portfolios'
        )
        
        # Primero obtener portfolios
        url = "https://api.coinbase.com/api/v3/brokerage/portfolios"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            portfolios = data.get('portfolios', [])
            
            print(f"\n✅ Portafolios: {len(portfolios)}\n")
            
            for portfolio in portfolios:
                uuid = portfolio.get('uuid')
                name = portfolio.get('name')
                
                print(f"Portfolio: {name} ({uuid})")
                print(f"Intentando obtener breakdown...")
                
                # Intentar con /breakdown
                breakdown_url = f"https://api.coinbase.com/api/v3/brokerage/portfolios/{uuid}"
                
                resp_breakdown = requests.get(
                    breakdown_url,
                    headers=headers,
                    timeout=10
                )
                
                print(f"   Status: {resp_breakdown.status_code}")
                
                if resp_breakdown.status_code == 200:
                    breakdown_data = resp_breakdown.json()
                    print(f"   Breakdown data:")
                    print(json.dumps(breakdown_data, indent=2)[:1500])
                else:
                    print(f"   Respuesta: {resp_breakdown.text[:500]}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Busca los datos de balance"""
    print("\n" + "#"*80)
    print("# BÚSQUEDA DE BALANCE REAL - $525.57 USD")
    print("#"*80)
    
    # Buscar en cada lugar posible
    search_in_accounts()
    search_in_products()
    search_in_portfolio_breakdown()
    
    print("\n" + "#"*80)
    print("# BÚSQUEDA COMPLETADA")
    print("#"*80)


if __name__ == "__main__":
    main()
