#!/usr/bin/env python3
"""
TEST SIMPLE PARA COINBASE WEBSOCKET
Sin Schwab, sin complejidad - solo diagnosticar Coinbase
"""
import asyncio
import json
import websockets
from datetime import datetime
from hub.managers.coinbase_jwt_manager import CoinbaseJWTManager

async def test_coinbase():
    print("\n" + "="*60)
    print("INICIANDO TEST COINBASE WEBSOCKET")
    print("="*60 + "\n")
    
    try:
        # Paso 1: Generar JWT
        print("🔑 [1] Generando JWT...")
        jwt_mgr = CoinbaseJWTManager(config_path="hub")
        jwt_token = jwt_mgr.generate_jwt()
        
        if not jwt_token:
            print("❌ No se pudo generar JWT")
            return
        print(f"✅ JWT generado: {jwt_token[:40]}...")
        
        # Paso 2: Conectar a WebSocket
        print("\n🌐 [2] Conectando a wss://advanced-trade-ws.coinbase.com...")
        ws = await websockets.connect("wss://advanced-trade-ws.coinbase.com")
        print("✅ WebSocket conectado\n")
        
        # Paso 3: Enviar suscripción
        print("📨 [3] Enviando suscripción al canal 'user'...")
        subscribe_msg = json.dumps({
            "type": "subscribe",
            "channel": "user",
            "jwt": jwt_token
        })
        
        await ws.send(subscribe_msg)
        print("✅ Suscripción enviada\n")
        
        # Paso 4: ESCUCHAR POR 60 SEGUNDOS
        print("="*60)
        print("🎧 ESCUCHANDO MENSAJES DE COINBASE (60 segundos)...")
        print("="*60 + "\n")
        
        msg_count = 0
        start_time = datetime.now()
        
        try:
            while (datetime.now() - start_time).total_seconds() < 60:
                try:
                    # Esperar mensaje con timeout corto
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    
                    msg_count += 1
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    try:
                        data = json.loads(msg)
                        channel = data.get('channel', 'UNKNOWN')
                        msg_type = data.get('type', 'UNKNOWN')
                        
                        print(f"📨 [{elapsed:.1f}s] Mensaje {msg_count}:")
                        print(f"   Canal: {channel}")
                        print(f"   Tipo: {msg_type}")
                        print(f"   Completo: {json.dumps(data)[:150]}\n")
                    except:
                        print(f"📨 [{elapsed:.1f}s] Mensaje {msg_count} (no-JSON): {msg[:100]}\n")
                
                except asyncio.TimeoutError:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if msg_count == 0:
                        print(f"⏱️  [{elapsed:.1f}s] Sin mensajes aún...")
                    else:
                        print(f"⏱️  [{elapsed:.1f}s] Sin nuevos mensajes (últimos {msg_count} recibidos)...")
                
                except Exception as e:
                    print(f"❌ Error al recibir: {e}")
                    break
        
        except Exception as e:
            print(f"❌ Error en bucle: {e}")
        
        # Resultado
        print("\n" + "="*60)
        print(f"RESULTADO FINAL: {msg_count} mensajes recibidos")
        print("="*60)
        
        if msg_count == 0:
            print("⚠️  Coinbase NO envió ningún mensaje")
        elif msg_count == 2:
            print("⚠️  Coinbase envió solo 2 mensajes de confirmación, luego se desconectó")
            print("   Solución: Probablemente necesita enviar 'ping' periódicamente")
        else:
            print(f"✅ Coinbase envió {msg_count} mensajes - ¡Funcionando!")
        
        await ws.close()
        
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_coinbase())
