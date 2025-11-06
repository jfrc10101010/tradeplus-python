#!/usr/bin/env python3
"""
Script para obtener token REAL de Schwab la PRIMERA VEZ.
Después se guarda en .schwab_token.json y se renueva automáticamente.

Uso: python scripts/get_schwab_token.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_schwab_token():
    """Obtiene token de Schwab via OAuth (abre navegador automáticamente)"""
    try:
        from schwab import auth
        
        api_key = os.getenv("TOS_CLIENT_ID")
        app_secret = os.getenv("TOS_CLIENT_SECRET")
        callback_url = os.getenv("TOS_CALLBACK_URL")
        token_path = ".schwab_token.json"
        
        print("🌐 Abriendo navegador para autenticación con Schwab...")
        print("   (si no abre automáticamente, abre manualmente)")
        
        client = auth.easy_client(
            api_key,
            app_secret,
            callback_url,
            token_path
        )
        
        print("✅ Token obtenido y guardado en .schwab_token.json")
        
        # Verificar que funciona
        principals = client.get_principal()
        print(f"✅ Autenticación verificada")
        print(f"   Usuario: {principals['preferredUserName']}")
        print(f"   Cuenta: {principals['primaryAccountId']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = get_schwab_token()
    sys.exit(0 if success else 1)
