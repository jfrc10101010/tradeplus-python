"""
Extrae datos REALES de las pruebas:
- Posiciones abiertas
- Balance real
- Órdenes activas
- Portafolios
"""
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
import os

# Agregar hub al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from managers.coinbase_jwt_manager import CoinbaseJWTManager


def extract_accounts_data():
    """Extrae datos de CUENTAS (wallets y balances)"""
    print("\n" + "="*80)
    print("📊 EXTRAYENDO DATOS REALES - CUENTAS")
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
            
            print(f"\n✅ Conexión exitosa - HTTP 200")
            print(f"📈 Total de cuentas/wallets: {len(accounts)}\n")
            
            # Extraer y mostrar cada wallet
            total_usd = 0
            for i, account in enumerate(accounts, 1):
                currency = account.get('currency', 'UNKNOWN')
                balance = account.get('balance', {})
                amount = balance.get('amount', '0')
                
                # Convertir a float si es posible
                try:
                    amount_float = float(amount)
                except:
                    amount_float = 0
                
                print(f"  [{i:2d}] {currency:6s} | Balance: {amount:>15s} | ID: {account.get('uuid', 'N/A')[:8]}...")
                
                # Sumar si es USD
                if currency == 'USD':
                    total_usd = amount_float
            
            print(f"\n💰 BALANCE TOTAL EN USD: ${total_usd:.2f}")
            
            # Retornar data estructurada
            return {
                'status': 'success',
                'total_accounts': len(accounts),
                'total_usd': total_usd,
                'accounts': [
                    {
                        'currency': acc.get('currency'),
                        'balance': acc.get('balance', {}).get('amount', '0'),
                        'uuid': acc.get('uuid')
                    }
                    for acc in accounts
                ]
            }
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def extract_orders_data():
    """Extrae datos de ÓRDENES (historial completo)"""
    print("\n" + "="*80)
    print("📋 EXTRAYENDO DATOS REALES - ÓRDENES")
    print("="*80)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        jwt_token = manager.generate_jwt_for_endpoint(
            method='GET', 
            path='/api/v3/brokerage/orders/historical/batch'
        )
        
        url = "https://api.coinbase.com/api/v3/brokerage/orders/historical/batch"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            
            print(f"\n✅ Conexión exitosa - HTTP 200")
            print(f"📊 Total de órdenes: {len(orders)}\n")
            
            # Agrupar por estado
            states = {}
            for order in orders:
                state = order.get('order_type', 'UNKNOWN')
                if state not in states:
                    states[state] = 0
                states[state] += 1
            
            print("📊 ÓRDENES POR TIPO:")
            for state, count in sorted(states.items()):
                print(f"   {state:15s}: {count:3d} órdenes")
            
            # Mostrar últimas 5 órdenes
            print(f"\n📅 ÚLTIMAS 5 ÓRDENES:")
            for i, order in enumerate(orders[:5], 1):
                product_id = order.get('product_id', 'UNKNOWN')
                order_type = order.get('order_type', 'UNKNOWN')
                created_time = order.get('created_time', 'UNKNOWN')
                price = order.get('average_filled_price', '0')
                
                print(f"  [{i}] {product_id:15s} | {order_type:10s} | {price:>10s} | {created_time}")
            
            return {
                'status': 'success',
                'total_orders': len(orders),
                'order_types': states,
                'orders_sample': [
                    {
                        'product_id': o.get('product_id'),
                        'order_type': o.get('order_type'),
                        'price': o.get('average_filled_price'),
                        'created_time': o.get('created_time'),
                        'id': o.get('id')
                    }
                    for o in orders[:10]
                ]
            }
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def extract_fills_data():
    """Extrae datos de FILLS (transacciones completadas)"""
    print("\n" + "="*80)
    print("💸 EXTRAYENDO DATOS REALES - FILLS (TRANSACCIONES)")
    print("="*80)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        jwt_token = manager.generate_jwt_for_endpoint(
            method='GET',
            path='/api/v3/brokerage/orders/historical/fills'
        )
        
        url = "https://api.coinbase.com/api/v3/brokerage/orders/historical/fills"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            fills = data.get('fills', [])
            
            print(f"\n✅ Conexión exitosa - HTTP 200")
            print(f"💵 Total de fills/transacciones: {len(fills)}\n")
            
            # Agrupar por producto
            products = {}
            total_value = 0
            for fill in fills:
                product = fill.get('product_id', 'UNKNOWN')
                if product not in products:
                    products[product] = []
                products[product].append(fill)
                
                # Sumar valor total
                try:
                    price = float(fill.get('price', 0))
                    size = float(fill.get('size', 0))
                    total_value += price * size
                except:
                    pass
            
            print("📊 FILLS POR PRODUCTO:")
            for product, fills_list in sorted(products.items()):
                print(f"   {product:15s}: {len(fills_list):3d} transacciones")
            
            print(f"\n💰 VOLUMEN TOTAL ESTIMADO: ${total_value:,.2f}")
            
            # Mostrar últimos 5 fills
            print(f"\n📅 ÚLTIMOS 5 FILLS:")
            for i, fill in enumerate(fills[:5], 1):
                product = fill.get('product_id', 'UNKNOWN')
                price = fill.get('price', '0')
                size = fill.get('size', '0')
                side = fill.get('side', 'UNKNOWN')
                
                print(f"  [{i}] {product:15s} | {side:4s} | Precio: {price:>10s} | Cantidad: {size:>10s}")
            
            return {
                'status': 'success',
                'total_fills': len(fills),
                'products': {k: len(v) for k, v in products.items()},
                'total_value': total_value,
                'fills_sample': [
                    {
                        'product_id': f.get('product_id'),
                        'side': f.get('side'),
                        'price': f.get('price'),
                        'size': f.get('size'),
                        'created_at': f.get('created_at')
                    }
                    for f in fills[:10]
                ]
            }
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def extract_portfolios_data():
    """Extrae datos de PORTAFOLIOS"""
    print("\n" + "="*80)
    print("🎯 EXTRAYENDO DATOS REALES - PORTAFOLIOS")
    print("="*80)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        jwt_token = manager.generate_jwt_for_endpoint(
            method='GET',
            path='/api/v3/brokerage/portfolios'
        )
        
        url = "https://api.coinbase.com/api/v3/brokerage/portfolios"
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            portfolios = data.get('portfolios', [])
            
            print(f"\n✅ Conexión exitosa - HTTP 200")
            print(f"🎯 Total de portafolios: {len(portfolios)}\n")
            
            for i, portfolio in enumerate(portfolios, 1):
                name = portfolio.get('name', 'UNKNOWN')
                type_val = portfolio.get('type', 'UNKNOWN')
                uuid = portfolio.get('uuid', 'UNKNOWN')
                
                print(f"  [{i}] Nombre: {name:20s} | Tipo: {type_val:15s} | ID: {uuid[:8]}...")
                
                # Mostrar breakdown si existe
                breakdown = portfolio.get('breakdown', {})
                if breakdown:
                    total_balance = breakdown.get('total_balance', {})
                    amount = total_balance.get('amount', '0')
                    currency = total_balance.get('currency', 'USD')
                    print(f"       Balance: {amount} {currency}")
            
            return {
                'status': 'success',
                'total_portfolios': len(portfolios),
                'portfolios': [
                    {
                        'name': p.get('name'),
                        'type': p.get('type'),
                        'uuid': p.get('uuid'),
                        'balance': p.get('breakdown', {}).get('total_balance', {})
                    }
                    for p in portfolios
                ]
            }
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    """Ejecuta extracción completa de datos reales"""
    print("\n" + "#"*80)
    print("# EXTRACCIÓN DE DATOS REALES DEL TRADING ACCOUNT")
    print("#"*80)
    
    all_data = {}
    
    # Extraer cada tipo de dato
    all_data['accounts'] = extract_accounts_data()
    all_data['orders'] = extract_orders_data()
    all_data['fills'] = extract_fills_data()
    all_data['portfolios'] = extract_portfolios_data()
    
    # Guardar en JSON
    output_file = Path('hub/datos_reales_account.json')
    
    print("\n" + "="*80)
    print("💾 GUARDANDO DATOS EN ARCHIVO")
    print("="*80)
    
    try:
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        print(f"\n✅ Datos guardados en: {output_file}")
        print(f"   Archivo: {output_file}")
        print(f"   Tamaño: {output_file.stat().st_size} bytes")
    
    except Exception as e:
        print(f"❌ Error guardando: {e}")
    
    # Resumen final
    print("\n" + "#"*80)
    print("# RESUMEN FINAL DE DATOS REALES")
    print("#"*80)
    
    if all_data.get('accounts'):
        accounts = all_data['accounts']
        if accounts.get('status') == 'success':
            print(f"\n💰 BALANCE:")
            print(f"   Total USD: ${accounts.get('total_usd', 0):.2f}")
            print(f"   Wallets: {accounts.get('total_accounts', 0)}")
    
    if all_data.get('orders'):
        orders = all_data['orders']
        if orders.get('status') == 'success':
            print(f"\n📋 ÓRDENES:")
            print(f"   Total: {orders.get('total_orders', 0)}")
            for order_type, count in orders.get('order_types', {}).items():
                print(f"   {order_type}: {count}")
    
    if all_data.get('fills'):
        fills = all_data['fills']
        if fills.get('status') == 'success':
            print(f"\n💸 FILLS:")
            print(f"   Total: {fills.get('total_fills', 0)}")
            print(f"   Volumen: ${fills.get('total_value', 0):,.2f}")
    
    if all_data.get('portfolios'):
        portfolios = all_data['portfolios']
        if portfolios.get('status') == 'success':
            print(f"\n🎯 PORTAFOLIOS:")
            print(f"   Total: {portfolios.get('total_portfolios', 0)}")
    
    print("\n" + "#"*80 + "\n")


if __name__ == "__main__":
    main()
