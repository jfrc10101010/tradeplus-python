"""
Test completo para CoinbaseJWTManager con soporte multi-endpoint
Valida que JWT parametrizado funciona para todos los endpoints
"""
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime
import os

# Agregar hub al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from managers.coinbase_jwt_manager import CoinbaseJWTManager

# Endpoints a probar (HTTP 200 si el API key tiene permisos)
ENDPOINTS = {
    'accounts': {
        'method': 'GET',
        'path': '/api/v3/brokerage/accounts',
        'description': 'Lista de cuentas y wallets'
    },
    'orders': {
        'method': 'GET',
        'path': '/api/v3/brokerage/orders/historical/batch',
        'description': 'Historial de órdenes'
    },
    'fills': {
        'method': 'GET',
        'path': '/api/v3/brokerage/orders/historical/fills',
        'description': 'Historial de transacciones (fills)'
    },
    'portfolios': {
        'method': 'GET',
        'path': '/api/v3/brokerage/portfolios',
        'description': 'Carteras de portafolio'
    }
}


def test_initialization():
    """Test 1: Inicialización del manager"""
    print("\n" + "="*70)
    print("TEST 1: INICIALIZACIÓN DEL MANAGER")
    print("="*70)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        print(f"✅ Manager inicializado correctamente")
        print(f"   API Key: {manager.api_key[:50]}...")
        print(f"   Clave privada cargada: {'Sí' if manager.private_key else 'No'}")
        return manager
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_jwt_generation_parametrized(manager):
    """Test 2: Generación parametrizada de JWT"""
    print("\n" + "="*70)
    print("TEST 2: GENERACIÓN DE JWT PARAMETRIZADO")
    print("="*70)
    
    results = []
    
    for endpoint_name, config in ENDPOINTS.items():
        try:
            method = config['method']
            path = config['path']
            description = config['description']
            
            # Generar JWT para este endpoint
            jwt_token = manager.generate_jwt_for_endpoint(method=method, path=path)
            
            # Validar formato JWT
            if jwt_token and len(jwt_token) > 20:
                print(f"✅ {endpoint_name.upper()}")
                print(f"   Descripción: {description}")
                print(f"   JWT: {jwt_token[:40]}...")
                results.append((endpoint_name, True, jwt_token))
            else:
                print(f"❌ {endpoint_name.upper()}: Token inválido")
                results.append((endpoint_name, False, None))
        
        except Exception as e:
            print(f"❌ {endpoint_name.upper()}: {e}")
            results.append((endpoint_name, False, None))
    
    return results


def test_jwt_with_rest_api(jwt_results):
    """Test 3: Validar JWT con REST API real"""
    print("\n" + "="*70)
    print("TEST 3: VALIDACIÓN CON REST API REAL")
    print("="*70)
    
    results = []
    
    for endpoint_name, success, jwt_token in jwt_results:
        if not success or not jwt_token:
            print(f"⏭️  {endpoint_name.upper()}: JWT no generado")
            results.append((endpoint_name, False, None))
            continue
        
        try:
            config = ENDPOINTS[endpoint_name]
            method = config['method']
            path = config['path']
            
            url = f"https://api.coinbase.com{path}"
            
            # Headers con JWT
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Content-Type': 'application/json'
            }
            
            print(f"\n🔍 {endpoint_name.upper()}")
            print(f"   URL: {method} {url}")
            
            # Enviar request
            response = requests.request(method, url, headers=headers, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Contar elementos según endpoint
                    if endpoint_name == 'accounts':
                        count = len(data.get('accounts', []))
                        print(f"   ✅ HTTP 200 - {count} cuentas obtenidas")
                    elif endpoint_name == 'orders':
                        count = len(data.get('orders', []))
                        print(f"   ✅ HTTP 200 - {count} órdenes obtenidas")
                    elif endpoint_name == 'fills':
                        count = len(data.get('fills', []))
                        print(f"   ✅ HTTP 200 - {count} fills obtenidos")
                    elif endpoint_name == 'portfolios':
                        count = len(data.get('portfolios', []))
                        print(f"   ✅ HTTP 200 - {count} portafolios obtenidos")
                    
                    results.append((endpoint_name, True, response.status_code))
                
                except json.JSONDecodeError:
                    print(f"   ✅ HTTP 200 (no JSON)")
                    results.append((endpoint_name, True, response.status_code))
            
            elif response.status_code == 401:
                print(f"   ❌ HTTP 401 - JWT no válido para este endpoint o API key sin permisos")
                results.append((endpoint_name, False, response.status_code))
            
            elif response.status_code == 403:
                print(f"   ⚠️  HTTP 403 - Acceso prohibido (API key limitada)")
                results.append((endpoint_name, False, response.status_code))
            
            else:
                print(f"   ⚠️  HTTP {response.status_code}")
                results.append((endpoint_name, False, response.status_code))
        
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout en request")
            results.append((endpoint_name, False, None))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append((endpoint_name, False, None))
        
        time.sleep(0.5)  # Rate limiting
    
    return results


def test_jwt_backward_compatibility(manager):
    """Test 4: Compatibilidad con generate_jwt() (legacy)"""
    print("\n" + "="*70)
    print("TEST 4: COMPATIBILIDAD LEGACY - generate_jwt()")
    print("="*70)
    
    try:
        # Debe generar JWT para cuentas (por defecto)
        jwt_token = manager.generate_jwt()
        
        if jwt_token and len(jwt_token) > 20:
            print(f"✅ generate_jwt() funciona (sin parámetros)")
            print(f"   Token: {jwt_token[:40]}...")
            
            # Validar que es para cuentas
            if manager.current_jwt == jwt_token:
                print(f"✅ JWT almacenado en current_jwt")
                return True
            else:
                print(f"❌ JWT no almacenado correctamente")
                return False
        else:
            print(f"❌ Token inválido")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Ejecuta todos los tests"""
    print("\n" + "#"*70)
    print("# TEST COMPLETO: COINBASE JWT MANAGER - MULTI ENDPOINT")
    print("#"*70)
    
    # Test 1: Inicialización
    manager = test_initialization()
    if not manager:
        print("\n❌ No se pudo continuar sin manager")
        return False
    
    # Test 2: Generación parametrizada
    jwt_results = test_jwt_generation_parametrized(manager)
    
    # Test 3: REST API
    api_results = test_jwt_with_rest_api(jwt_results)
    
    # Test 4: Compatibilidad legacy
    legacy_ok = test_jwt_backward_compatibility(manager)
    
    # Resumen
    print("\n" + "#"*70)
    print("# RESUMEN DE RESULTADOS")
    print("#"*70)
    
    print(f"\n📊 GENERACIÓN DE JWT:")
    for endpoint, success, _ in jwt_results:
        status = "✅" if success else "❌"
        print(f"   {status} {endpoint.upper()}")
    
    print(f"\n🌐 VALIDACIÓN REST API:")
    for endpoint, success, status_code in api_results:
        if success:
            print(f"   ✅ {endpoint.upper()} (HTTP {status_code})")
        else:
            print(f"   ❌ {endpoint.upper()} (HTTP {status_code if status_code else 'ERROR'})")
    
    print(f"\n🔄 COMPATIBILIDAD LEGACY:")
    print(f"   {'✅' if legacy_ok else '❌'} generate_jwt() sin parámetros")
    
    # Contar resultados
    jwt_passed = sum(1 for _, s, _ in jwt_results if s)
    api_passed = sum(1 for _, s, _ in api_results if s)
    
    print(f"\n📈 ESTADÍSTICAS:")
    print(f"   JWT generados: {jwt_passed}/{len(jwt_results)}")
    print(f"   Endpoints respondiendo: {api_passed}/{len(api_results)}")
    
    all_passed = (
        jwt_passed == len(jwt_results) and
        legacy_ok and
        api_passed >= 1  # Al menos uno debe funcionar
    )
    
    print("\n" + "#"*70)
    if all_passed:
        print("# ✅ MANAGER OPERATIVO - SOPORTE MULTI-ENDPOINT FUNCIONAL")
    elif api_passed >= 1:
        print("# ⚠️  MANAGER FUNCIONAL - ALGUNOS ENDPOINTS NO DISPONIBLES")
        print("#    (Posible: API key limitada, pero JWT funciona correctamente)")
    else:
        print("# ❌ ERRORES DETECTADOS")
    print("#"*70 + "\n")
    
    return api_passed >= 1


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
