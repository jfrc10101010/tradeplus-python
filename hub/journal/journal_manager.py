"""
╔═══════════════════════════════════════════════════════════════╗
║       Journal Manager - Orquestador Multi-Broker             ║
║       TRADEPLUS V5.0 - Multi-Broker System                  ║
╚═══════════════════════════════════════════════════════════════╝

Responsabilidad Única:
- Orquesta llamadas a ambos adapters
- Fusiona resultados en formato común
- Maneja caché y timeout
"""

from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from .schwab_adapter import SchwabAdapter, get_schwab_journal
from .coinbase_adapter import CoinbaseAdapter, get_coinbase_journal

logger = logging.getLogger(__name__)


class JournalManager:
    """Orquestador central de journal multi-broker"""
    
    def __init__(self):
        """Inicializa manager con adapters"""
        self.schwab = SchwabAdapter()
        self.coinbase = CoinbaseAdapter()
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si caché es válido"""
        if key not in self._cache:
            return False
        
        cached_time = self._cache[key]["timestamp"]
        age = (datetime.now() - cached_time).total_seconds()
        return age < self._cache_ttl
    
    def get_combined_journal(self, days: int = 7) -> Dict:
        """
        Obtiene journal combinado de ambos brokers
        
        Args:
            days: Número de días hacia atrás
            
        Returns:
            Dict con trades de ambos brokers + estadísticas consolidadas
        """
        cache_key = f"combined_{days}"
        
        # Verificar caché
        if self._is_cache_valid(cache_key):
            logger.info("Retornando journal desde caché")
            return self._cache[cache_key]["data"]
        
        try:
            logger.info("Obteniendo journal combinado...")
            
            # Obtener de ambos brokers (no lanzan excepciones, devuelven [] en error)
            schwab_result = self.schwab.get_transactions(days=days)
            coinbase_result = self.coinbase.get_fills(days=days)
            
            # Combinar trades
            all_trades = schwab_result + coinbase_result
            
            # Ordenar por datetime descendente
            all_trades.sort(key=lambda x: x["datetime"], reverse=True)
            
            # Calcular estadísticas consolidadas
            total_trades = len(all_trades)
            total_volume = sum(t["amount"] for t in all_trades)
            total_fees = sum(t["fee"] for t in all_trades)
            buys = sum(1 for t in all_trades if t["side"] == "BUY")
            sells = sum(1 for t in all_trades if t["side"] == "SELL")
            
            # Estadísticas por broker
            schwab_trades = len(schwab_result)
            coinbase_trades = len(coinbase_result)
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "trades": all_trades,
                "stats": {
                    "total_trades": total_trades,
                    "total_volume": round(total_volume, 2),
                    "total_fees": round(total_fees, 2),
                    "buys": buys,
                    "sells": sells,
                    "by_broker": {
                        "schwab": {
                            "trades": schwab_trades,
                            "volume": round(sum(t["amount"] for t in schwab_result), 2),
                            "fees": round(sum(t["fee"] for t in schwab_result), 2)
                        },
                        "coinbase": {
                            "trades": coinbase_trades,
                            "volume": round(sum(t["amount"] for t in coinbase_result), 2),
                            "fees": round(sum(t["fee"] for t in coinbase_result), 2)
                        }
                    }
                }
            }
            
            # Guardar en caché
            self._cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now()
            }
            
            logger.info(f"✅ Journal combinado: {total_trades} trades, ${total_volume:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo journal combinado: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "trades": [],
                "stats": {},
                "error": str(e)
            }
    
    def get_trades_by_broker(self, broker: str, days: int = 7) -> Dict:
        """
        Obtiene trades de un broker específico
        
        Args:
            broker: "schwab" o "coinbase"
            days: Número de días
            
        Returns:
            Dict con trades del broker especificado
        """
        try:
            if broker.lower() == "schwab":
                trades = self.schwab.get_transactions(days=days)
                total_volume = sum(t["amount"] for t in trades)
                total_fees = sum(t["fee"] for t in trades)
                
                return {
                    "broker": "schwab",
                    "trades": trades,
                    "stats": {
                        "total_trades": len(trades),
                        "total_volume": round(total_volume, 2),
                        "total_fees": round(total_fees, 2)
                    }
                }
            
            elif broker.lower() == "coinbase":
                trades = self.coinbase.get_fills(days=days)
                total_volume = sum(t["amount"] for t in trades)
                total_fees = sum(t["fee"] for t in trades)
                
                return {
                    "broker": "coinbase",
                    "trades": trades,
                    "stats": {
                        "total_trades": len(trades),
                        "total_volume": round(total_volume, 2),
                        "total_fees": round(total_fees, 2)
                    }
                }
            
            else:
                raise ValueError(f"Broker no válido: {broker}")
        
        except Exception as e:
            logger.error(f"Error obteniendo trades de {broker}: {e}")
            return {
                "broker": broker,
                "trades": [],
                "stats": {},
                "error": str(e)
            }
    
    def get_statistics(self, days: int = 7) -> Dict:
        """
        Obtiene solo estadísticas agregadas (sin trades)
        
        Args:
            days: Número de días
            
        Returns:
            Dict con estadísticas consolidadas
        """
        try:
            journal = self.get_combined_journal(days=days)
            
            return {
                "timestamp": journal["timestamp"],
                "stats": journal.get("stats", {}),
                "error": journal.get("error")
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """Limpia el caché"""
        self._cache.clear()
        logger.info("Caché limpiado")


# Instancia global
_manager = None


def get_manager() -> JournalManager:
    """Obtiene o crea instancia del manager"""
    global _manager
    if _manager is None:
        _manager = JournalManager()
    return _manager
