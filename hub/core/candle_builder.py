from core.models import Tick, Candle
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional

class CandleBuilder:
    """Acumula Ticks y genera Candles cerradas cada minuto"""
    
    def __init__(self):
        self.candles = defaultdict(self._default_candle)
        self.last_minute = {}
    
    def _default_candle(self):
        return {
            'open': None,
            'high': -float('inf'),
            'low': float('inf'),
            'close': None,
            'volume': 0,
            'timestamp_open': None,
            'count': 0
        }
    
    def add_tick(self, tick: Tick) -> Optional[Candle]:
        """
        Agrega un tick y retorna una Candle cerrada si cambió el minuto.
        """
        key = f"{tick.broker}:{tick.symbol}"
        minute = tick.timestamp.replace(second=0, microsecond=0)
        
        # Detectar cierre de minuto anterior
        if key in self.last_minute and self.last_minute[key] != minute:
            candle = self._close_candle(key, self.last_minute[key])
            # Reset para nuevo minuto
            self.candles[key] = self._default_candle()
            self.candles[key]['open'] = tick.price
            self.candles[key]['high'] = tick.price
            self.candles[key]['low'] = tick.price
            self.candles[key]['close'] = tick.price
            self.candles[key]['volume'] = tick.volume
            self.candles[key]['timestamp_open'] = minute
            self.last_minute[key] = minute
            return candle
        
        # Actualizar candle actual
        state = self.candles[key]
        if state['open'] is None:
            state['open'] = tick.price
            state['timestamp_open'] = minute
        
        state['high'] = max(state['high'], tick.price)
        state['low'] = min(state['low'], tick.price)
        state['close'] = tick.price
        state['volume'] += tick.volume
        state['count'] += 1
        self.last_minute[key] = minute
        
        return None
    
    def _close_candle(self, key: str, minute: datetime) -> Candle:
        """Crear Candle cerrada"""
        broker, symbol = key.split(':')
        state = self.candles[key]
        
        return Candle(
            broker=broker,
            symbol=symbol,
            timeframe="1m",
            open=state['open'],
            high=state['high'],
            low=state['low'],
            close=state['close'],
            volume=state['volume'],
            timestamp_open=state['timestamp_open'],
            timestamp_close=state['timestamp_open'] + timedelta(minutes=1)
        )
