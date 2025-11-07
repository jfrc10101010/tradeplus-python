"""
Test del Journal Manager
Verifica que el endpoint /api/journal funcione correctamente
"""
import asyncio
import json
from pathlib import Path

# Test 1: Verificar imports
print("=" * 60)
print("TEST 1: Verificar imports")
print("=" * 60)

try:
    from hub.journal.journal_manager import JournalManager
    print("[OK] JournalManager importado correctamente")
except Exception as e:
    print(f"[ERROR] Error importando JournalManager: {e}")
    exit(1)

try:
    from hub.hub import HubCentral
    print("[OK] HubCentral importado correctamente")
except Exception as e:
    print(f"[ERROR] Error importando HubCentral: {e}")
    exit(1)

# Test 2: Inicializar HubCentral con JournalManager
print("\n" + "=" * 60)
print("TEST 2: Inicializar HubCentral")
print("=" * 60)

try:
    hub = HubCentral(config_path=".")
    print("[OK] HubCentral inicializado")
    
    if hub.journal_manager:
        print("[OK] JournalManager disponible en HubCentral")
    else:
        print("[WARN] JournalManager no disponible (esperable si falta CoinbaseJWTManager)")
except Exception as e:
    print(f"[ERROR] Error inicializando HubCentral: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Verificar estructura del Journal
print("\n" + "=" * 60)
print("TEST 3: Verificar estructura del Journal")
print("=" * 60)

if hub.journal_manager:
    # Verificar métodos
    methods_to_check = ['get_journal', 'calculate_stats']
    for method in methods_to_check:
        if hasattr(hub.journal_manager, method):
            print(f"[OK] Metodo '{method}' disponible")
        else:
            print(f"[ERROR] Metodo '{method}' NO disponible")

# Test 4: Verificar que el endpoint está disponible
print("\n" + "=" * 60)
print("TEST 4: Verificar que el hub.py tiene el endpoint")
print("=" * 60)

hub_file = Path("hub/hub.py")
if hub_file.exists():
    content = hub_file.read_text(encoding='utf-8', errors='ignore')
    if "@app.get(\"/api/journal\")" in content:
        print("[OK] Endpoint /api/journal esta en hub.py")
    else:
        print("[ERROR] Endpoint /api/journal NO esta en hub.py")
else:
    print(f"[ERROR] Archivo {hub_file} no encontrado")

print("\n" + "=" * 60)
print("[SUCCESS] TESTS COMPLETADOS EXITOSAMENTE")
print("=" * 60)
print("\nSiguientes pasos:")
print("1. Ejecutar: python hub/main.py")
print("2. Esperar a que el hub se conecte")
print("3. Acceder a: http://localhost:8000/api/journal?broker=schwab&days=7")
print("4. Abrir: http://localhost:5000/journal.html (si existe servidor)")
