"""
Script de prueba para CoinbaseJWTManager
Verifica que toda la funcionalidad está operativa
"""
import sys
import json
from pathlib import Path
from datetime import datetime
import os

# Agregar hub al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hub'))

from managers.coinbase_jwt_manager import CoinbaseJWTManager


def test_initialization():
    """Test 1: Inicialización correcta"""
    print("\n" + "="*60)
    print("TEST 1: INICIALIZACIÓN DEL MANAGER")
    print("="*60)
    
    try:
        manager = CoinbaseJWTManager(config_path='hub')
        print(f"✅ Manager inicializado correctamente")
        print(f"   API Key cargada: {manager.api_key[:50]}...")
        print(f"   Clave privada: {'Sí' if manager.private_key else 'No'}")
        return manager
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_jwt_generation(manager):
    """Test 2: Generación de JWT"""
    print("\n" + "="*60)
    print("TEST 2: GENERACIÓN DE JWT")
    print("="*60)
    
    try:
        jwt_token = manager.get_current_jwt()
        print(f"✅ JWT generado exitosamente")
        print(f"   Token: {jwt_token[:40]}...")
        print(f"   Generado en: {manager.jwt_generated_at}")
        print(f"   Expira en: {manager.jwt_expires_at}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_jwt_validity(manager):
    """Test 3: Validación de JWT"""
    print("\n" + "="*60)
    print("TEST 3: VALIDACIÓN DE JWT")
    print("="*60)
    
    try:
        is_valid = manager.is_jwt_valid()
        print(f"✅ JWT es válido: {is_valid}")
        return is_valid
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_jwt_refresh(manager):
    """Test 4: Renovación de JWT"""
    print("\n" + "="*60)
    print("TEST 4: RENOVACIÓN DE JWT")
    print("="*60)
    
    try:
        # Primera renovación (debe retornar False - aún válido)
        result = manager.refresh_jwt()
        print(f"✅ Primer refresh: {result} (esperado: False)")
        
        # Forzar expiración y renovar
        from datetime import timedelta
        manager.jwt_expires_at = datetime.now() - timedelta(seconds=30)
        result = manager.refresh_jwt()
        print(f"✅ Refresh con expiración simulada: {result} (esperado: True)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_jwt_file_output():
    """Test 5: Archivo JWT de salida"""
    print("\n" + "="*60)
    print("TEST 5: ARCHIVO JWT DE SALIDA")
    print("="*60)
    
    try:
        jwt_file = Path('hub/coinbase_current_jwt.json')
        
        if jwt_file.exists():
            with open(jwt_file, 'r') as f:
                data = json.load(f)
            
            print(f"✅ Archivo encontrado: {jwt_file}")
            print(f"   Contiene JWT: {'jwt' in data}")
            print(f"   Contiene timestamp: {'generated_at' in data}")
            print(f"   Contiene expiración: {'expires_at' in data}")
            print(f"   Generado: {data.get('generated_at')}")
            print(f"   Expira: {data.get('expires_at')}")
            return True
        else:
            print(f"❌ Archivo no encontrado: {jwt_file}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Ejecuta todos los tests"""
    print("\n" + "#"*60)
    print("# PRUEBAS DEL COINBASE JWT MANAGER")
    print("#"*60)
    
    results = []
    
    # Test 1: Inicialización
    manager = test_initialization()
    if not manager:
        print("\n❌ No se pudo continuar sin manager")
        return False
    
    # Test 2: Generación
    results.append(("Generación JWT", test_jwt_generation(manager)))
    
    # Test 3: Validación
    results.append(("Validación JWT", test_jwt_validity(manager)))
    
    # Test 4: Renovación
    results.append(("Renovación JWT", test_jwt_refresh(manager)))
    
    # Test 5: Archivo de salida
    results.append(("Archivo de salida", test_jwt_file_output()))
    
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
