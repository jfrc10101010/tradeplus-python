"""
Script de prueba para SchwabTokenManager
Verifica que toda la funcionalidad está operativa
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import os

# Agregar hub al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from managers.schwab_token_manager import SchwabTokenManager


def test_initialization():
    """Test 1: Inicialización correcta"""
    print("\n" + "="*60)
    print("TEST 1: INICIALIZACIÓN DEL MANAGER")
    print("="*60)
    
    try:
        manager = SchwabTokenManager(config_path='hub')
        print(f"✅ Manager inicializado correctamente")
        print(f"   CLIENT_ID cargado: {manager.client_id[:30]}...")
        print(f"   CLIENT_SECRET: {'Sí' if manager.client_secret else 'No'}")
        print(f"   REFRESH_TOKEN: {'Sí' if manager.refresh_token_value else 'No'}")
        return manager
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_refresh_token_real(manager):
    """Test 2: Renovación REAL de token (HTTP POST a Schwab)"""
    print("\n" + "="*60)
    print("TEST 2: RENOVACIÓN REAL DE TOKEN (HTTP POST A SCHWAB)")
    print("="*60)
    
    try:
        result = manager.refresh_token()
        
        if result:
            print(f"✅ Token renovado exitosamente")
            print(f"   Token: {manager.current_token[:40]}...")
            print(f"   Renovado en: {manager.token_obtained_at}")
            print(f"   Expira en: {manager.token_expires_at}")
            print(f"   Válido por: {manager.token_expires_in} segundos ({manager.token_expires_in/60:.0f} minutos)")
            return True
        else:
            print(f"❌ Error renovando token")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_token_validity(manager):
    """Test 3: Validación de token"""
    print("\n" + "="*60)
    print("TEST 3: VALIDACIÓN DE TOKEN")
    print("="*60)
    
    try:
        is_valid = manager.is_token_valid()
        print(f"✅ Token es válido: {is_valid}")
        return is_valid
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_auth_header(manager):
    """Test 4: Header de autorización"""
    print("\n" + "="*60)
    print("TEST 4: HEADER DE AUTORIZACIÓN")
    print("="*60)
    
    try:
        header = manager.get_auth_header()
        print(f"✅ Header de autorización generado")
        print(f"   Authorization: Bearer {header.get('Authorization', '')[:40]}...")
        print(f"   Content-Type: {header.get('Content-Type')}")
        
        # Validar formato
        auth = header.get('Authorization', '')
        if auth.startswith('Bearer '):
            print(f"✅ Formato Bearer válido")
            return True
        else:
            print(f"❌ Formato Bearer inválido")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_token_file_output():
    """Test 5: Archivo de salida"""
    print("\n" + "="*60)
    print("TEST 5: ARCHIVO TOKEN DE SALIDA")
    print("="*60)
    
    try:
        token_file = Path('hub/current_token.json')
        
        if token_file.exists():
            with open(token_file, 'r') as f:
                data = json.load(f)
            
            print(f"✅ Archivo encontrado: {token_file}")
            print(f"   Contiene access_token: {'access_token' in data}")
            print(f"   Contiene token_type: {'token_type' in data}")
            print(f"   Contiene expires_in: {'expires_in' in data}")
            print(f"   Contiene scope: {'scope' in data}")
            print(f"   Contiene obtained_at: {'obtained_at' in data}")
            print(f"   Contiene expires_at: {'expires_at' in data}")
            print(f"   Obtenido: {data.get('obtained_at')}")
            print(f"   Expira: {data.get('expires_at')}")
            
            # Validar que tiene datos
            has_all = all(k in data for k in ['access_token', 'token_type', 'expires_in', 'scope', 'obtained_at', 'expires_at'])
            return has_all
        else:
            print(f"❌ Archivo no encontrado: {token_file}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_error_handling():
    """Test 6: Manejo de errores"""
    print("\n" + "="*60)
    print("TEST 6: MANEJO DE ERRORES")
    print("="*60)
    
    try:
        # Intentar con credenciales inválidas
        os.environ['TOS_CLIENT_ID'] = 'INVALID'
        os.environ['TOS_CLIENT_SECRET'] = 'INVALID'
        os.environ['TOS_REFRESH_TOKEN'] = 'INVALID'
        
        manager_invalid = SchwabTokenManager(config_path='hub')
        result = manager_invalid.refresh_token()
        
        if not result:
            print(f"✅ Error handling funcionando (rechazó credenciales inválidas)")
            return True
        else:
            print(f"❌ No se detectó error con credenciales inválidas")
            return False
    except Exception as e:
        print(f"✅ Error handling funcionando (excepción capturada)")
        return True


def main():
    """Ejecuta todos los tests"""
    print("\n" + "#"*60)
    print("# PRUEBAS DEL SCHWAB TOKEN MANAGER")
    print("#"*60)
    
    results = []
    
    # Test 1: Inicialización
    manager = test_initialization()
    if not manager:
        print("\n❌ No se pudo continuar sin manager")
        return False
    
    # Test 2: Renovación real
    results.append(("Renovación real de token", test_refresh_token_real(manager)))
    
    # Test 3: Validación
    results.append(("Validación de token", test_token_validity(manager)))
    
    # Test 4: Auth header
    results.append(("Header de autorización", test_auth_header(manager)))
    
    # Test 5: Archivo de salida
    results.append(("Archivo de salida", test_token_file_output()))
    
    # Test 6: Manejo de errores
    results.append(("Manejo de errores", test_error_handling()))
    
    # Resumen
    print("\n" + "#"*60)
    print("# RESUMEN DE RESULTADOS")
    print("#"*60)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "#"*60)
    if all_passed:
        print("# ✅ TODOS LOS TESTS PASARON - MANAGER OPERATIVO")
    else:
        print("# ❌ ALGUNOS TESTS FALLARON")
    print("#"*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
