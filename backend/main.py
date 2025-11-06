from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from dotenv import load_dotenv

from adapters.schwab_adapter import SchwabAdapter
from adapters.coinbase_adapter import CoinbaseAdapter
from core.normalizer import Normalizer
from core.candle_builder import CandleBuilder

load_dotenv()

app = FastAPI(
    title="TRADEPLUS API",
    description="Multi-broker trading platform",
    version="0.0.1"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar componentes
schwab = SchwabAdapter()
coinbase = CoinbaseAdapter()
normalizer = Normalizer()
builder = CandleBuilder()

# Estado de conexión
connected_websockets = set()

@app.get("/health")
async def health():
    """Verificar estado del servidor"""
    return {
        "status": "ok",
        "service": "TRADEPLUS API",
        "connected_clients": len(connected_websockets)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint que emite candles normalizadas"""
    await websocket.accept()
    connected_websockets.add(websocket)
    print(f"✅ Cliente conectado. Total: {len(connected_websockets)}")
    
    try:
        # Conectar adapters
        await schwab.connect()
        await coinbase.connect()
        
        # Suscribir a símbolos
        await schwab.subscribe(["AAPL", "MSFT", "TSLA"])
        await coinbase.subscribe(["BTC-USD", "ETH-USD"])
        
        print("🔄 Iniciando loop de datos...")
        
        # Loop de recepción de datos
        while True:
            # Procesar datos de Schwab
            schwab_tick = await schwab.get_tick()
            if schwab_tick:
                tick = normalizer.from_schwab(schwab_tick)
                candle = builder.add_tick(tick)
                if candle:
                    await websocket.send_json(candle.dict())
            
            # Procesar datos de Coinbase
            coinbase_tick = await coinbase.get_tick()
            if coinbase_tick:
                tick = normalizer.from_coinbase(coinbase_tick)
                candle = builder.add_tick(tick)
                if candle:
                    await websocket.send_json(candle.dict())
            
            await asyncio.sleep(0.01)
    
    except WebSocketDisconnect:
        print("❌ Cliente desconectado")
        connected_websockets.discard(websocket)
    except Exception as e:
        print(f"❌ Error: {e}")
        connected_websockets.discard(websocket)
    finally:
        await schwab.disconnect()
        await coinbase.disconnect()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 5000))
    print(f"🚀 Iniciando TRADEPLUS en puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
