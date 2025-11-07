"""
TRADEPLUS V5.0 - Main FastAPI Entry Point
Con endpoints de Journal
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional

# Crear app
app = FastAPI(title="TRADEPLUS Journal")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar Journal
try:
    from journal_simple import JournalSimple
    journal = JournalSimple()
except:
    journal = None

# Endpoint health
@app.get("/health")
async def health():
    return {"status": "ok", "message": "Server is running"}

# Endpoint journal
@app.get("/api/journal")
async def get_journal(broker: str = "schwab", days: int = 7):
    """
    Obtiene trading journal

    Query params:
    - broker: "schwab" o "coinbase"
    - days: número de días
    """
    if not journal:
        return {"error": "Journal no disponible"}

    if broker == "schwab":
        trades = journal.get_schwab_trades(days)
    elif broker == "coinbase":
        trades = journal.get_coinbase_trades(days)
    else:
        return {"error": "Broker desconocido"}

    return {
        "broker": broker,
        "trades": trades,
        "count": len(trades)
    }

if __name__ == "__main__":
    print("Starting TRADEPLUS server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
