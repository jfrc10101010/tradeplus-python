"""
TEST REAL SIMPLE - Schwab: Token + Streamer Info + WebSocket Conectado

Sin bloqueos. Solo verifica que todo funciona correctamente.
"""

import asyncio
import json
import logging
from hub.managers.schwab_websocket_manager import SchwabWebSocketManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    manager = SchwabWebSocketManager(config_path=".")
    
    try:
        print("\n" + "="*80)
        print("TEST REAL: SCHWAB TOKEN REFRESH + WEBSOCKET PRIVADO")
        print("="*80)
        
        # PASO 1: Token válido
        print("\n[1/3] Verificando token...")
        if manager._ensure_valid_token():
            print(f"✅ Token válido: {manager.access_token[:30]}...\n")
        else:
            print("❌ Error obteniendo token\n")
            return
        
        # PASO 2: Obtener streamer info
        print("[2/3] Obteniendo streamer info...")
        if manager._get_streamer_info():
            print(f"✅ Streamer URL: {manager.streamer_info.get('streamerSocketUrl')}")
            print(f"✅ Customer ID: {manager.streamer_info.get('schwabClientCustomerId')[:30]}...\n")
        else:
            print("❌ Error obteniendo streamer info\n")
            return
        
        # PASO 3: Conectar WebSocket (sin bloquear en receive_loop)
        print("[3/3] Conectando a WebSocket...")
        
        import websockets
        import uuid
        
        ws_url = manager.streamer_info.get("streamerSocketUrl")
        
        async with websockets.connect(ws_url) as ws:
            manager.ws = ws
            manager.connected = True
            print("✅ WebSocket conectado\n")
            
            # Enviar LOGIN
            login_msg = {
                "requests": [
                    {
                        "requestid": "1",
                        "service": "ADMIN",
                        "command": "LOGIN",
                        "SchwabClientCustomerId": manager.streamer_info.get("schwabClientCustomerId", ""),
                        "SchwabClientCorrelId": manager.streamer_info.get("schwabClientCorrelId", str(uuid.uuid4())),
                        "parameters": {
                            "Authorization": manager.access_token,
                            "SchwabClientChannel": manager.streamer_info.get("schwabClientChannel", "IO"),
                            "SchwabClientFunctionId": manager.streamer_info.get("schwabClientFunctionId", "Tradeticket")
                        }
                    }
                ]
            }
            
            print("→ Enviando LOGIN...")
            await ws.send(json.dumps(login_msg))
            
            # Recibir respuesta LOGIN
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            resp_data = json.loads(response)
            resp_code = resp_data.get("response", [{}])[0].get("content", {}).get("code")
            
            if resp_code == 0:
                print("✅ LOGIN EXITOSO\n")
                
                # BONUS: Intentar suscribirse a un símbolo
                print("→ Suscribiendo a AAPL...")
                sub_msg = {
                    "requests": [
                        {
                            "requestid": "2",
                            "service": "LEVELONE_EQUITIES",
                            "command": "SUBS",
                            "parameters": {
                                "keys": "AAPL",
                                "fields": "0,1,2,3,4,5,6,7,8,9,10"
                            }
                        }
                    ]
                }
                
                await ws.send(json.dumps(sub_msg))
                print("✅ Suscripción enviada\n")
                
                # Recibir datos durante 10 segundos
                print("📊 Recibiendo datos en tiempo real (10 segundos)...\n")
                start = asyncio.get_event_loop().time()
                ticks = 0
                
                while asyncio.get_event_loop().time() - start < 10:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        data = json.loads(msg)
                        if "data" in data or "response" in data:
                            ticks += 1
                            msg_preview = json.dumps(data)[:100]
                            print(f"[TICK #{ticks}] {msg_preview}...")
                    except asyncio.TimeoutError:
                        continue
                
                print(f"\n✅ COMPLETADO - {ticks} ticks recibidos")
            else:
                print(f"❌ LOGIN FALLÓ (código: {resp_code})")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    finally:
        manager.connected = False
        print("\n✅ Test finalizado")

if __name__ == "__main__":
    asyncio.run(main())
