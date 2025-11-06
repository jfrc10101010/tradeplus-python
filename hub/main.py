"""
Hub FastAPI - Ejecuta el servidor de orquestación de WebSockets
"""
import uvicorn
import sys
from pathlib import Path

# Asegurar que el Hub puede importar sus managers
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════╗
║         🚀 TradePlus Hub - FastAPI Server              ║
║                                                        ║
║  Orquestador de WebSockets Privados:                  ║
║  • Coinbase (BTC-USD, ETH-USD)                        ║
║  • Schwab (Equities)                                   ║
║                                                        ║
║  Endpoints disponibles:                               ║
║  • GET  /health     - Estado del Hub                  ║
║  • GET  /stats      - Estadísticas                    ║
║  • GET  /ticks      - Últimos ticks                   ║
║  • WS   /ws/live    - WebSocket para ticks            ║
║                                                        ║
║  Dashboard en Flask: http://localhost:5000/test       ║
║  API FastAPI: http://localhost:8000                   ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
    """)
    
    # Importar app desde hub.py DESPUÉS de los prints
    from hub.hub import app
    
    # Ejecutar con Uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
