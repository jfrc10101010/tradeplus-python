#!/usr/bin/env python3
"""
🚀 TradePlus V5.0 - Generador de Tokens Completo
"""
import os
import asyncio
import aiohttp
import base64
import json
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class TokenManager:
    def __init__(self):
        self.client_id = os.getenv('TOS_CLIENT_ID')
        self.client_secret = os.getenv('TOS_CLIENT_SECRET')
        self.refresh_token = os.getenv('TOS_REFRESH_TOKEN')
        self.base_url = "https://api.schwabapi.com"
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("❌ Faltan credenciales en el archivo .env")
    
    def print_header(self):
        """Imprime header bonito"""
        print("🚀" + "="*60 + "🚀")
        print(" " * 15 + "TradePlus V5.0 - Token Manager")
        print(" " * 20 + "Generador Automático de Tokens")
        print("🚀" + "="*60 + "🚀")
        print()
    
    async def generate_new_token(self):
        """Genera un nuevo access_token usando refresh_token"""
        
        # Preparar autorización básica
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        url = f"{self.base_url}/v1/oauth/token"
        
        try:
            print("🔄 Generando nuevo access_token...")
            print(f"📡 Endpoint: {url}")
            print(f"🆔 Client ID: {self.client_id[:15]}...")
            print()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    status = response.status
                    data_response = await response.json()
                    
                    if status == 200:
                        print("✅ ¡TOKEN GENERADO EXITOSAMENTE!")
                        print("="*50)
                        
                        # Extraer información importante
                        access_token = data_response.get('access_token')
                        expires_in = data_response.get('expires_in', 0)
                        new_refresh_token = data_response.get('refresh_token')
                        
                        # Mostrar información clara
                        print(f"🎫 ACCESS TOKEN:")
                        print(f"   {access_token}")
                        print()
                        print(f"⏰ EXPIRA EN: {expires_in} segundos ({expires_in//60} minutos)")
                        print(f"🔄 NUEVO REFRESH TOKEN: {new_refresh_token[:30]}...")
                        print()
                        
                        # Guardar en archivo para fácil acceso
                        token_data = {
                            "access_token": access_token,
                            "expires_in": expires_in,
                            "generated_at": datetime.now().isoformat(),
                            "refresh_token": new_refresh_token
                        }
                        
                        with open('current_token.json', 'w') as f:
                            json.dump(token_data, f, indent=2)
                        
                        print("💾 Token guardado en: current_token.json")
                        print()
                        
                        # Instrucciones para el dashboard
                        print("🌐 PARA USAR EN EL DASHBOARD:")
                        print("-" * 30)
                        print("1. Abre dashboard.html en tu navegador")
                        print("2. Copia este token:")
                        print(f"   {access_token}")
                        print("3. Pégalo en el campo 'access_token'")
                        print("4. Click 'Probar Token'")
                        print()
                        
                        return access_token
                        
                    else:
                        print(f"❌ Error al generar token: {status}")
                        print(f"📄 Respuesta: {json.dumps(data_response, indent=2)}")
                        return None
                        
        except Exception as e:
            print(f"💥 Error de conexión: {e}")
            return None
    
    async def test_token(self, access_token):
        """Prueba el token generado"""
        print("🧪 PROBANDO TOKEN GENERADO...")
        print("-" * 30)
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        url = f"{self.base_url}/trader/v1/accounts"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    status = response.status
                    
                    if status == 200:
                        data = await response.json()
                        print("✅ TOKEN VÁLIDO - API SCHWAB RESPONDE")
                        print(f"📊 Cuentas encontradas: {len(data)}")
                        
                        for i, account in enumerate(data, 1):
                            account_num = account.get('securitiesAccount', {}).get('accountNumber', 'N/A')
                            cash = account.get('securitiesAccount', {}).get('currentBalances', {}).get('totalCash', 0)
                            print(f"   {i}. Cuenta {account_num} - Balance: ${cash:,.2f}")
                        
                        return True
                    else:
                        print(f"❌ Token inválido: {status}")
                        text = await response.text()
                        print(f"📄 Respuesta: {text}")
                        return False
                        
        except Exception as e:
            print(f"💥 Error al probar token: {e}")
            return False

async def main():
    """Función principal"""
    try:
        manager = TokenManager()
        manager.print_header()
        
        # Generar nuevo token
        access_token = await manager.generate_new_token()
        
        if access_token:
            print()
            # Probar el token
            await manager.test_token(access_token)
            
            print()
            print("🎉 PROCESO COMPLETADO")
            print("=" * 50)
            print("✅ Token generado y validado")
            print("✅ Listo para usar en dashboard.html")
            print("✅ Datos guardados en current_token.json")
            
        else:
            print("❌ No se pudo generar el token")
            
    except Exception as e:
        print(f"💥 Error fatal: {e}")

if __name__ == "__main__":
    asyncio.run(main())