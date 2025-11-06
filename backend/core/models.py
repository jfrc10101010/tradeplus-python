from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

@dataclass
class Tick:
    """Modelo normalizado de un tick de precio"""
    broker: str  # "SCHWAB" o "COINBASE"
    symbol: str
    price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime

@dataclass
class Candle:
    """Modelo normalizado de una vela OHLCV"""
    broker: str
    symbol: str
    timeframe: str = "1m"
    open: float = 0
    high: float = 0
    low: float = 0
    close: float = 0
    volume: float = 0
    timestamp_open: Optional[datetime] = None
    timestamp_close: Optional[datetime] = None
    
    def dict(self):
        """Convertir a diccionario con timestamps en ISO format"""
        d = asdict(self)
        if self.timestamp_open:
            d['timestamp_open'] = self.timestamp_open.isoformat()
        if self.timestamp_close:
            d['timestamp_close'] = self.timestamp_close.isoformat()
        return d
