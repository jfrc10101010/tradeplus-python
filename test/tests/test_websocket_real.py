"""
TEST REAL: WebSocket Schwab con datos EXACTOS del API

Usa los valores reales extraídos de /v1/userPreference
y conecta al WebSocket correctamente.
"""

import asyncio
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

from hub.managers.schwab_token_manager import SchwabTokenManager

async def main():
    print("\n" + "="*80)
    print("PRUEBA REAL: SCHWAB WEBSOCKET CON DATOS EXACTOS")
    print("="*80 + "\n")
    
    # Paso 1: Obtener token válido
    print("[1/4] Obteniendo token...")
    token_manager = SchwabTokenManager(config_path="hub")
    access_token = token_manager.get_current_token()
    
    if not access_token:
        print("❌ Error obteniendo token")
        return
    
    print(f"✅ Token: {access_token[:50]}...\n")
    
    # Paso 2: Obtener streamer info
    print("[2/4] Obteniendo streamer info...")
    import requests
    
    url = "https://api.schwabapi.com/trader/v1/userPreference"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Error HTTP {response.status_code}")
        return
    
    data = response.json()
    streamer_info = data["streamerInfo"][0]  # Es un array
    
    # Extraer campos EXACTOS
    ws_url = streamer_info["streamerSocketUrl"]
    customer_id = streamer_info["schwabClientCustomerId"]
    correl_id = streamer_info["schwabClientCorrelId"]
    channel = streamer_info["schwabClientChannel"]
    function_id = streamer_info["schwabClientFunctionId"]
    
    print(f"✅ Streamer info obtenido:")
    print(f"   URL: {ws_url}")
    print(f"   Customer ID: {customer_id[:30]}...")
    print(f"   Channel: {channel}")
    print(f"   Function ID: {function_id}\n")
    
    # Paso 3: Conectar WebSocket
    print("[3/4] Conectando a WebSocket...")
    
    try:
        import websockets
        
        async with websockets.connect(ws_url, ping_interval=None) as ws:
            print(f"✅ WebSocket conectado\n")
            
            # Paso 4: Enviar LOGIN con datos EXACTOS
            print("[4/4] Enviando LOGIN...")
            
            login_msg = {
                "requests": [{
                    "service": "ADMIN",
                    "command": "LOGIN",
                    "requestid": "0",
                    "SchwabClientCustomerId": customer_id,
                    "SchwabClientCorrelId": correl_id,
                    "parameters": {
                        "Authorization": access_token,
                        "SchwabClientChannel": channel,
                        "SchwabClientFunctionId": function_id
                    }
                }]
            }
            
            print(f"→ Enviando: {json.dumps(login_msg, indent=2)[:200]}...\n")
            
            await ws.send(json.dumps(login_msg))
            
            # Recibir respuesta LOGIN
            try:
                response_msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                response_data = json.loads(response_msg)
                
                print(f"← Respuesta recibida: {json.dumps(response_data, indent=2)[:300]}...\n")
                
                # Verificar respuesta
                resp_code = response_data.get("response", [{}])[0].get("content", {}).get("code")
                
                if resp_code == 0:
                    print("✅ LOGIN EXITOSO\n")
                    print("📊 RECIBIENDO DATOS EN TIEMPO REAL...\n")
                    
                    # Suscribirse a un símbolo
                    sub_msg = {
                        "requests": [{
                            "service": "LEVELONE_EQUITIES",
                            "command": "SUBS",
                            "requestid": "1",
                            "parameters": {
                                "keys": "AAPL,MSFT,SPY",
                                "fields": "0,1,2,3,4,5,6,7,8,9,10,11,12"
                            }
                        }]
                    }
                    
                    print(f"→ Suscribiendo a AAPL, MSFT, SPY...")
                    await ws.send(json.dumps(sub_msg))
                    
                    # Recibir ticks
                    start_time = datetime.now()
                    ticks_received = 0
                    
                    while (datetime.now() - start_time).total_seconds() < 30:  # 30 segundos
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                            data = json.loads(msg)
                            
                            # Buscar ticks (pueden estar en "data" o "response" o "snapshot")
                            if "data" in data or "response" in data or "snapshot" in data:
                                ticks_received += 1
                                
                                # Mostrar preview
                                msg_str = json.dumps(data)
                                if len(msg_str) > 150:
                                    msg_str = msg_str[:150] + "..."
                                
                                elapsed = (datetime.now() - start_time).total_seconds()
                                print(f"[{elapsed:.1f}s] TICK #{ticks_received}: {msg_str}")
                        
                        except asyncio.TimeoutError:
                            pass
                        except Exception as e:
                            logger.debug(f"Error procesando mensaje: {e}")
                    
                    print(f"\n✅ TEST COMPLETADO")
                    print(f"   Ticks recibidos: {ticks_received}")
                    print(f"   Duración: {(datetime.now() - start_time).total_seconds():.1f}s")
                
                else:
                    print(f"❌ LOGIN FALLÓ - Código: {resp_code}")
                    print(f"   Respuesta: {response_data}")
            
            except asyncio.TimeoutError:
                print("❌ Timeout esperando respuesta LOGIN")
            except Exception as e:
                print(f"❌ Error en comunicación: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error WebSocket: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
