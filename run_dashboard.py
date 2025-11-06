"""
Start WebSocket Dashboard - Robusto para mantener conexión abierta
"""
import sys
import os
import asyncio
import logging

# Set encoding to UTF-8 para evitar issues con emojis
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Importar después
from websocket_dashboard import app
import uvicorn

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 DASHBOARD WEBSOCKET EN VIVO")
    print("="*80)
    print("\n📍 URL: http://localhost:8000")
    print("\n📊 Secciones:")
    print("   - Schwab: Saldo, Posiciones, Compra/Venta")
    print("   - Coinbase: Wallets, Saldos, Disponible")
    print("\n✅ Presiona CTRL+C para detener")
    print("="*80 + "\n")
    
    # Configurar logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO"},
        },
    }
    
    # Ejecutar con uvicorn
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_config=log_config,
            access_log=False
        )
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard detenido")
        sys.exit(0)
