"""
Regenerar Access Token de Schwab
Script simple para obtener nuevo access_token usando refresh_token
"""

import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Credenciales de Schwab
CLIENT_ID = "E5JeBvUNWNkRSt4iH2a9iGOWFnY2HP9s4Y792ftffemWFLLe"
CLIENT_SECRET = "3mKEG3P4bgYDGErOEVzPaGswI7ckqN6wBfIljAfZ0wQzjSTMaiyG8AQbnZQGFEPN"
REFRESH_TOKEN = os.getenv("TOS_REFRESH_TOKEN")

print("🔄 Regenerando Access Token de Schwab...")
print(f"📄 Usando refresh_token: {REFRESH_TOKEN[:50]}..." if REFRESH_TOKEN else "❌ No se encontró TOS_REFRESH_TOKEN")

if not REFRESH_TOKEN:
    print("❌ Error: No se encontró TOS_REFRESH_TOKEN en el archivo .env")
    print("Asegúrate de que existe la variable TOS_REFRESH_TOKEN en tu .env")
    exit(1)

# Solicitar nuevo access token
try:
    response = requests.post(
        "https://auth.schwabapi.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    print(f"📡 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        access_token = data.get('access_token', '')
        expires_in = data.get('expires_in', 0)
        new_refresh_token = data.get('refresh_token', REFRESH_TOKEN)
        
        print("\n✅ ¡ÉXITO! Nuevo access token generado:")
        print(f"🔑 Access Token: {access_token[:50]}...")
        print(f"⏰ Válido por: {expires_in} segundos ({expires_in/60:.1f} minutos)")
        print(f"🔄 Nuevo Refresh Token: {new_refresh_token[:50]}...")
        
        # Guardar el access token en un archivo temporal
        with open("access_token.txt", "w") as f:
            f.write(access_token)
        
        print(f"\n💾 Access token guardado en: access_token.txt")
        print(f"📋 Úsalo en el siguiente paso para obtener datos de cuentas")
        
        # Mostrar el nuevo refresh token si cambió
        if new_refresh_token != REFRESH_TOKEN:
            print(f"\n⚠️ IMPORTANTE: Tu refresh token se actualizó!")
            print(f"🔄 Nuevo Refresh Token: {new_refresh_token}")
            print("📝 Actualiza tu .env con el nuevo refresh token")
    
    else:
        print(f"\n❌ Error al regenerar token:")
        print(f"Status: {response.status_code}")
        
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Response text: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Error de conexión: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")