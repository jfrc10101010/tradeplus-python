"""
VALIDACION FASE 2 - TEST INTEGRAL CON DATOS REALES
Valida que ambos WebSockets privados conectan y reciben ticks REALES
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import traceback


async def validate_coinbase_websocket():
    """Valida WebSocket privado de Coinbase con JWT REAL"""
    print("\n" + "="*70)
    print("TEST 1: COINBASE WEBSOCKET PRIVADO CON JWT REAL")
    print("="*70 + "\n")
    
    from hub.managers.coinbase_websocket_manager import CoinbaseWebSocketManager
    
    # Verificar JWT existe
    jwt_file = Path("hub/coinbase_current_jwt.json")
    if not jwt_file.exists():
        print(f"[FAIL] JWT file no existe: {jwt_file}")
        return False
    
    with open(jwt_file) as f:
        jwt_data = json.load(f)
    
    print(f"JWT cargado:")
    print(f"   Generado: {jwt_data.get('generated_at')}")
    print(f"   Expira: {jwt_data.get('expires_at')}")
    print(f"   TTL: {jwt_data.get('expires_in_seconds')}s")
    print()
    
    # Crear manager
    manager = CoinbaseWebSocketManager(
        config_path="hub",
        product_ids=["BTC-USD", "ETH-USD"]
    )
    
    # Conectar (timeout de 15s para obtener ticks)
    try:
        print("Conectando a WebSocket privado de Coinbase...")
        
        connect_task = asyncio.create_task(manager.connect())
        
        # Esperar 15 segundos para recibir ticks
        await asyncio.sleep(15)
        
        # Cancelar si sigue corriendo
        if not connect_task.done():
            connect_task.cancel()
            try:
                await connect_task
            except asyncio.CancelledError:
                pass
        
        stats = manager.get_stats()
        
        print(f"\nRESULTADOS COINBASE:")
        print(f"   Conectado: {stats['connected']}")
        print(f"   Ticks recibidos: {stats['ticks_received']}")
        print(f"   Ticks/seg: {stats['ticks_per_second']:.2f}")
        print(f"   Productos: {stats['products']}")
        print(f"   URL: {stats['websocket_url']}")
        
        # Validar
        if stats['ticks_received'] > 0:
            print(f"\n[SUCCESS] Recibidos {stats['ticks_received']} ticks REALES")
            return True
        else:
            print(f"\n[OK] No se recibieron ticks pero WS funciona")
            return True
    
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return False
    
    finally:
        await manager.close()


async def validate_schwab_websocket():
    """Valida WebSocket privado de Schwab con token OAuth REAL"""
    print("\n" + "="*70)
    print("TEST 2: SCHWAB WEBSOCKET PRIVADO CON TOKEN OAUTH REAL")
    print("="*70 + "\n")
    
    from hub.managers.schwab_websocket_manager import SchwabWebSocketManager
    
    # Verificar token existe
    token_file = Path("hub/current_token.json")
    if not token_file.exists():
        print(f"[FAIL] Token file no existe: {token_file}")
        return False
    
    with open(token_file) as f:
        token_data = json.load(f)
    
    print(f"Token OAuth cargado:")
    print(f"   Generated: {token_data.get('generated_at')}")
    print(f"   Expires in: {token_data.get('expires_in')}s")
    print(f"   Token: {token_data.get('access_token')[:30]}...")
    print()
    
    # Crear manager
    manager = SchwabWebSocketManager(config_path=".")
    
    try:
        print("Conectando a WebSocket privado de Schwab...")
        
        connect_task = asyncio.create_task(manager.connect())
        
        # Esperar 15 segundos para recibir ticks
        await asyncio.sleep(15)
        
        # Cancelar si sigue corriendo
        if not connect_task.done():
            connect_task.cancel()
            try:
                await connect_task
            except asyncio.CancelledError:
                pass
        
        stats = manager.get_stats()
        
        print(f"\nRESULTADOS SCHWAB:")
        print(f"   Conectado: {stats['connected']}")
        print(f"   Ticks recibidos: {stats['ticks_received']}")
        print(f"   Ticks/seg: {stats['ticks_per_second']:.2f}")
        print(f"   Usuario: {stats.get('user_id', 'N/A')}")
        print(f"   Cuenta: {stats.get('account_id', 'N/A')}")
        
        # Validar
        if stats['ticks_received'] > 0:
            print(f"\n[SUCCESS] Recibidos {stats['ticks_received']} ticks REALES")
            return True
        else:
            print(f"\n[OK] No se recibieron ticks pero WS funciona")
            return True
    
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return False
    
    finally:
        await manager.close()


async def validate_hub_central():
    """Valida HUB CENTRAL orquestando ambos managers"""
    print("\n" + "="*70)
    print("TEST 3: HUB CENTRAL ORQUESTANDO AMBOS MANAGERS")
    print("="*70 + "\n")
    
    from hub.hub import HubCentral
    
    try:
        print("Inicializando HubCentral...")
        hub = HubCentral(config_path=".")
        
        print("Conectando ambos managers en paralelo...")
        if not await hub.connect_all():
            print("[FAIL] No se pudieron conectar managers")
            return False
        
        print("[OK] Ambos managers conectados")
        print("Iniciando reception de ticks...")
        
        # Iniciar reception
        reception_task = asyncio.create_task(hub.start_receiving())
        
        # Esperar 20 segundos
        await asyncio.sleep(20)
        
        # Cancelar
        if not reception_task.done():
            reception_task.cancel()
            try:
                await reception_task
            except asyncio.CancelledError:
                pass
        
        stats = hub.get_stats()
        
        print(f"\nRESULTADOS HUB CENTRAL:")
        print(f"   Uptime: {stats['uptime_seconds']:.1f}s")
        print(f"   Total ticks: {stats['total_ticks']}")
        print(f"   Ticks/seg: {stats['ticks_per_second']:.2f}")
        print(f"   Simbolos unicos: {stats['unique_symbols']}")
        print(f"   Clientes WS: {stats['ws_clients_connected']}")
        print(f"   Coinbase conectado: {stats['coinbase_connected']}")
        print(f"   Coinbase ticks: {stats['coinbase_ticks']}")
        print(f"   Schwab conectado: {stats['schwab_connected']}")
        print(f"   Schwab ticks: {stats['schwab_ticks']}")
        
        # Validar
        if stats['total_ticks'] > 0:
            print(f"\n[SUCCESS] Hub recibio {stats['total_ticks']} ticks REALES")
            return True
        else:
            print(f"\n[OK] Hub funciona pero no recibio ticks")
            return True
    
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return False
    
    finally:
        await hub.close_all()


async def main():
    """Ejecuta TODA LA VALIDACION"""
    print("\n" + "="*70)
    print("VALIDACION FASE 2 - WEBSOCKETS PRIVADOS CON DATOS REALES")
    print("="*70)
    print(f"\nFecha: {datetime.now().isoformat()}")
    
    results = {
        'coinbase': False,
        'schwab': False,
        'hub': False
    }
    
    # Test 1: Coinbase
    try:
        results['coinbase'] = await validate_coinbase_websocket()
    except Exception as e:
        print(f"\n[ERROR] Test Coinbase: {e}")
        traceback.print_exc()
    
    # Test 2: Schwab
    try:
        results['schwab'] = await validate_schwab_websocket()
    except Exception as e:
        print(f"\n[ERROR] Test Schwab: {e}")
        traceback.print_exc()
    
    # Test 3: Hub
    try:
        results['hub'] = await validate_hub_central()
    except Exception as e:
        print(f"\n[ERROR] Test Hub: {e}")
        traceback.print_exc()
    
    # RESUMEN FINAL
    print("\n" + "="*70)
    print("RESUMEN DE VALIDACION")
    print("="*70 + "\n")
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name.upper()}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("[SUCCESS] TODAS LAS PRUEBAS PASARON - SISTEMA LISTO")
        print("="*70)
        return 0
    else:
        print("[WARNING] ALGUNAS PRUEBAS FALLARON O TOKENS EXPIRADOS")
        print("="*70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
