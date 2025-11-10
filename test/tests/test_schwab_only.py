#!/usr/bin/env python3
"""
TEST SIMPLE PARA SCHWAB WEBSOCKET
Sin Coinbase, sin complejidad - solo diagnosticar Schwab
"""
import asyncio
import json
import websockets
import sys
from datetime import datetime
from hub.managers.schwab_websocket_manager import SchwabWebSocketManager

async def test_schwab():
    print("\n" + "="*60)
    print("INICIANDO TEST SCHWAB WEBSOCKET")
    print("="*60 + "\n")
    
    try:
        # Paso 1: Inicializar manager
        print("📡 [1] Inicializando SchwabWebSocketManager...")
        mgr = SchwabWebSocketManager(config_path="hub")
        
        # Paso 2: Validar token
        print("🔑 [2] Validando token...")
        if not mgr._ensure_valid_token():
            print("❌ Token no válido")
            return
        print("✅ Token válido")
        
        # Paso 3: Obtener streamer info
        print("📋 [3] Obteniendo streamerInfo...")
        if not mgr._get_streamer_info():
            print("❌ No se pudo obtener streamerInfo")
            return
        print(f"✅ streamerInfo obtenido: {mgr.streamer_info.get('schwabClientCustomerId')[:20]}...")
        
        # Paso 4: Conectar a WebSocket
        ws_url = mgr.streamer_info.get("streamerSocketUrl", "wss://streamer-api.schwab.com/ws")
        print(f"\n🌐 [4] Conectando a {ws_url}...")
        ws = await websockets.connect(ws_url)
        print("✅ WebSocket conectado\n")
        
        # Paso 5: Enviar LOGIN
        print("🔐 [5] Enviando LOGIN...")
        login_msg = {
            "requests": [{
                "requestid": "1",
                "service": "ADMIN",
                "command": "LOGIN",
                "SchwabClientCustomerId": mgr.streamer_info.get("schwabClientCustomerId"),
                "SchwabClientCorrelId": mgr.streamer_info.get("schwabClientCorrelId"),
                "SchwabClientChannel": mgr.streamer_info.get("schwabClientChannel"),
                "SchwabClientFunctionId": mgr.streamer_info.get("schwabClientFunctionId"),
                "parameters": {
                    "Authorization": mgr.access_token,
                    "SchwabClientChannel": mgr.streamer_info.get("schwabClientChannel"),
                    "SchwabClientFunctionId": mgr.streamer_info.get("schwabClientFunctionId")
                }
            }]
        }
        
        await ws.send(json.dumps(login_msg))
        print("✅ LOGIN enviado")
        
        # Paso 6: Esperar respuesta LOGIN
        print("⏳ [6] Esperando respuesta LOGIN...")
        login_response = await asyncio.wait_for(ws.recv(), timeout=10)
        login_data = json.loads(login_response)
        code = login_data['response'][0]['content']['code']
        print(f"✅ LOGIN response: code {code}")
        if code != 0:
            print(f"⚠️  ERROR en LOGIN: {login_data['response'][0]['content'].get('msg', 'Unknown')}")
        
        # Paso 7: ESCUCHAR SIN HACER NADA
        print("\n" + "="*60)
        print("🎧 ESCUCHANDO MENSAJES DE SCHWAB (60 segundos)...")
        print("="*60 + "\n")
        
        msg_count = 0
        start_time = datetime.now()
        timeout_check = 15  # Dar 15 segundos para ver si llegan datos
        
        try:
            while (datetime.now() - start_time).total_seconds() < 60:
                try:
                    # Esperar mensaje con timeout corto para poder actualizar el display
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    
                    msg_count += 1
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    try:
                        data = json.loads(msg)
                        msg_type = "JSON"
                        msg_preview = json.dumps(data)[:100]
                    except:
                        msg_type = "TEXT"
                        msg_preview = msg[:100]
                    
                    print(f"📨 [{elapsed:.1f}s] Mensaje {msg_count} ({msg_type}):")
                    print(f"   {msg_preview}\n")
                    
                except asyncio.TimeoutError:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"⏱️  [{elapsed:.1f}s] Sin mensajes en los últimos 5 segundos...")
                    
                except Exception as e:
                    print(f"❌ Error al recibir: {e}")
                    break
        
        except Exception as e:
            print(f"❌ Error en bucle: {e}")
        
        # Resultado final
        print("\n" + "="*60)
        print(f"RESULTADO FINAL: {msg_count} mensajes recibidos")
        print("="*60)
        
        if msg_count == 0:
            print("⚠️  PROBLEMA: Schwab no envía datos después de LOGIN")
            print("   Posibles causas:")
            print("   - Conexión se cierra automáticamente")
            print("   - Se requiere enviar subscription")
            print("   - API espera diferente patrón de comunicación")
        else:
            print(f"✅ Recibimos datos de Schwab!")
        
        await ws.close()
        
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_schwab())
