#!/usr/bin/env python3
"""
Script mínimo para probar regeneración de token de Schwab
"""
import os
import asyncio
import aiohttp
import base64
from urllib.parse import urlencode
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class SchwabTokenTest:
    def __init__(self):
        self.client_id = os.getenv('TOS_CLIENT_ID')
        self.client_secret = os.getenv('TOS_CLIENT_SECRET')
        self.refresh_token = os.getenv('TOS_REFRESH_TOKEN')
        self.base_url = "https://api.schwabapi.com"
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("Faltan credenciales en el archivo .env")
    
    async def refresh_access_token(self):
        """Prueba de regeneración de token usando refresh_token"""
        
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
            async with aiohttp.ClientSession() as session:
                print(f"🔄 Intentando regenerar token en: {url}")
                print(f"📋 Cliente ID: {self.client_id[:10]}...")
                print(f"🔑 Refresh token: {self.refresh_token[:20]}...")
                
                async with session.post(url, headers=headers, data=data) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"\n📊 Respuesta del servidor:")
                    print(f"   Status: {status}")
                    print(f"   Headers: {dict(response.headers)}")
                    print(f"   Body: {text}")
                    
                    if status == 200:
                        print("\n✅ ¡Token regenerado exitosamente!")
                        return True
                    else:
                        print(f"\n❌ Error al regenerar token: {status}")
                        return False
                        
        except Exception as e:
            print(f"\n💥 Error de conexión: {e}")
            return False

async def main():
    """Función principal"""
    print("🚀 TradePlus V5.0 - Test de Token Schwab")
    print("=" * 50)
    
    try:
        tester = SchwabTokenTest()
        success = await tester.refresh_access_token()
        
        if success:
            print("\n🎉 Test completado exitosamente")
        else:
            print("\n⚠️  Test falló - revisar credenciales")
            
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")

if __name__ == "__main__":
    asyncio.run(main())