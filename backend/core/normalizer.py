from core.models import Tick
from datetime import datetime
from typing import Dict, Any

class Normalizer:
    """Convierte raw data de cualquier broker a Tick normalizado"""
    
    @staticmethod
    def from_schwab(raw_data: Dict[str, Any]) -> Tick:
        """Schwab/TOS raw data → Tick normalizado"""
        return Tick(
            broker="SCHWAB",
            symbol=raw_data.get('symbol', ''),
            price=float(raw_data.get('last', 0)),
            bid=float(raw_data.get('bid', 0)),
            ask=float(raw_data.get('ask', 0)),
            volume=float(raw_data.get('volume', 0)),
            timestamp=datetime.now()
        )
    
    @staticmethod
    def from_coinbase(raw_data: Dict[str, Any]) -> Tick:
        """Coinbase WebSocket data → Tick normalizado"""
        return Tick(
            broker="COINBASE",
            symbol=raw_data.get('product_id', ''),
            price=float(raw_data.get('price', 0)),
            bid=float(raw_data.get('best_bid', 0)),
            ask=float(raw_data.get('best_ask', 0)),
            volume=float(raw_data.get('last_size', 0)),
            timestamp=datetime.now()
        )
