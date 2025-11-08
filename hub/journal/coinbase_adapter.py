"""
╔═══════════════════════════════════════════════════════════════╗
║         Coinbase Adapter - Fills Normalizer                  ║
║         TRADEPLUS V5.0 - Multi-Broker System                ║
╚═══════════════════════════════════════════════════════════════╝

Responsabilidad Única:
- Obtiene fills de Coinbase API
- Normaliza a formato común
- Maneja errores específicos de Coinbase
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import requests

logger = logging.getLogger(__name__)


class CoinbaseAdapter:
    """Adaptador exclusivo para Coinbase - obtiene y normaliza fills"""
    
    BASE_URL = "https://api.coinbase.com"
    ENDPOINT = "/api/v3/brokerage/orders/historical/fills"
    
    def __init__(self):
        """Inicializa el adaptador con JWT manager"""
        try:
            # Importar desde hub.managers
            import sys
            import os
            hub_path = os.path.dirname(os.path.dirname(__file__))
            if hub_path not in sys.path:
                sys.path.insert(0, hub_path)
            
            from managers.coinbase_jwt_manager import CoinbaseJWTManager
            self.jwt_manager = CoinbaseJWTManager()
            self.session = requests.Session()
            
            # Cache de quote_increment por símbolo para formateo correcto
            self.quote_increments: Dict[str, str] = {}
        except ImportError as e:
            logger.error(f"Error importando CoinbaseJWTManager: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene headers con JWT fresco para el endpoint de fills"""
        try:
            # Generar JWT específicamente para el endpoint de fills
            jwt = self.jwt_manager.generate_jwt_for_endpoint(
                method='GET',
                path=self.ENDPOINT
            )
            return {
                "Authorization": f"Bearer {jwt}",
                "Content-Type": "application/json"
            }
        except Exception as e:
            logger.error(f"Error generando JWT Coinbase: {e}")
            raise
    
    def get_fills(self, days: int = 7) -> List[Dict]:
        """
        Obtiene y normaliza fills de Coinbase
        
        Args:
            days: Número de días hacia atrás a consultar
            
        Returns:
            Lista de fills normalizados
            
        Raises:
            requests.RequestException: Error en la API REST
            ValueError: Datos inválidos en la respuesta
        """
        try:
            logger.info(f"Obteniendo fills Coinbase (últimos {days} días)")
            
            # Calcular fecha de inicio con timezone UTC
            start_date = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(days=days)
            
            # URL del endpoint (SIN start_sequence_timestamp que causa 401)
            url = f"{self.BASE_URL}{self.ENDPOINT}"
            
            # Parámetros: solo limit (Coinbase devuelve los más recientes primero)
            params = {
                "limit": 100  # Coinbase máximo por página
            }
            
            # Request con JWT fresco
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            fills = data.get("fills", [])
            
            if not isinstance(fills, list):
                logger.warning(f"Fills no es lista: {type(fills)}")
                return []
            
            # Filtrar por fecha y normalizar
            normalized = []
            for fill in fills:
                try:
                    # Verificar fecha antes de normalizar
                    trade_time = fill.get("trade_time", "")
                    if trade_time:
                        fill_date = datetime.fromisoformat(trade_time.replace("Z", "+00:00"))
                        if fill_date < start_date:
                            continue  # Saltar fills antiguos
                    
                    normalized_fill = self._normalize_fill(fill)
                    if normalized_fill:
                        normalized.append(normalized_fill)
                except Exception as e:
                    logger.warning(f"Fill individual rechazado: {e}")
                    continue
            
            logger.info(f"✅ {len(normalized)} fills normalizados de Coinbase")
            return normalized
            
        except requests.RequestException as e:
            logger.error(f"Error REST en Coinbase API: {e}")
            # No lanzar excepción, devolver lista vacía para no romper el journal
            return []
        except Exception as e:
            logger.error(f"Error inesperado obteniendo fills: {e}")
            # No lanzar excepción, devolver lista vacía para no romper el journal
            return []
    
    def _normalize_fill(self, fill: Dict) -> Optional[Dict]:
        """
        Normaliza un fill de Coinbase al formato común
        
        Args:
            fill: Fill crudo de Coinbase
            
        Returns:
            Fill normalizado o None si no válido
        """
        try:
            # Validación estructura mínima
            if not isinstance(fill, dict):
                return None
            
            # Extraer datos
            trade_id = fill.get("trade_id", "")
            product_id = fill.get("product_id", "")  # BTC-USD, ETH-USDC, etc
            side = fill.get("side", "").upper()
            
            if not all([trade_id, product_id, side]):
                logger.debug(f"Datos incompletos: id={trade_id}, prod={product_id}, side={side}")
                return None
            
            # Campos numéricos (con strings a float seguro)
            try:
                size = float(fill.get("size", 0) or 0)
                price = float(fill.get("price", 0) or 0)
                commission = float(fill.get("commission", 0) or 0)
            except (ValueError, TypeError):
                logger.debug(f"Conversión numérica falló en fill {trade_id}")
                return None
            
            # Calcular total
            total = size * price
            
            # Fecha
            date_str = fill.get("trade_time", "")
            try:
                datetime_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                datetime_obj = datetime.now()
                logger.debug(f"Fecha no válida: {date_str}, usando ahora")
            
            # Formato normalizado
            return {
                "id": trade_id,
                "datetime": datetime_obj.isoformat(),
                "symbol": product_id,
                "side": side,  # BUY o SELL
                "quantity": size,
                "price": price,
                "fee": commission,
                "amount": round(total, 2),
                "broker": "coinbase"
            }
            
        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Error normalizando fill: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado normalizando: {e}")
            return None
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, float]:
        """
        Obtiene cotizaciones actuales de Coinbase Products API
        
        Args:
            symbols: Lista de símbolos (ej: ["BTC-USD", "ETH-USD"])
        
        Returns:
            Dict con symbol: precio actual
            Ejemplo: {"BTC-USD": 76234.50, "ETH-USD": 3456.78}
        """
        try:
            if not symbols:
                return {}
            
            prices = {}
            
            # Coinbase requiere requests individuales por producto
            for symbol in symbols:
                try:
                    # GET /api/v3/brokerage/products/{product_id}
                    endpoint = f"/api/v3/brokerage/products/{symbol}"
                    jwt = self.jwt_manager.generate_jwt_for_endpoint(
                        method='GET',
                        path=endpoint
                    )
                    
                    headers = {
                        "Authorization": f"Bearer {jwt}",
                        "Accept": "application/json"
                    }
                    
                    url = f"{self.BASE_URL}{endpoint}"
                    response = self.session.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # El precio está en data['price']
                    if 'price' in data:
                        prices[symbol] = float(data['price'])
                        
                        # Guardar quote_increment para formateo correcto
                        if 'quote_increment' in data:
                            self.quote_increments[symbol] = data['quote_increment']
                            logger.debug(f"{symbol} quote_increment: {data['quote_increment']}")
                    else:
                        logger.warning(f"No se encontró precio para {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error obteniendo quote para {symbol}: {e}")
                    continue
            
            logger.info(f"Quotes obtenidos para {len(prices)} símbolos de Coinbase")
            return prices
            
        except Exception as e:
            logger.error(f"Error obteniendo quotes de Coinbase: {e}")
            return {}
    
    def get_decimals_for_symbol(self, symbol: str) -> int:
        """
        Determina el número de decimales correcto para un símbolo basado en quote_increment
        
        Args:
            symbol: Símbolo del producto (ej: "BTC-USD", "SHIB-USD")
        
        Returns:
            Número de decimales (2-8)
            
        Ejemplos:
            "0.01" -> 2 decimales (BTC, ETH)
            "0.0001" -> 4 decimales
            "0.00000001" -> 8 decimales (SHIB, PEPE)
        """
        if symbol not in self.quote_increments:
            # Default: 8 decimales para crypto si no sabemos
            return 8
        
        increment = self.quote_increments[symbol]
        
        try:
            # Contar decimales en el increment
            if '.' in increment:
                decimals = len(increment.split('.')[1])
                return decimals
            else:
                return 0
        except Exception as e:
            logger.warning(f"Error determinando decimales para {symbol}: {e}")
            return 8  # Default seguro


async def get_coinbase_journal(days: int = 7) -> Dict:
    """
    Función de conveniencia: obtiene journal completo de Coinbase
    
    Args:
        days: Rango de días
        
    Returns:
        Dict con fills y estadísticas agregadas
    """
    try:
        adapter = CoinbaseAdapter()
        trades = adapter.get_fills(days=days)
        
        # Estadísticas
        total_trades = len(trades)
        total_volume = sum(t["amount"] for t in trades)
        total_fees = sum(t["fee"] for t in trades)
        buys = sum(1 for t in trades if t["side"] == "BUY")
        sells = sum(1 for t in trades if t["side"] == "SELL")
        
        logger.info(f"Journal Coinbase: {total_trades} fills, ${total_volume:.2f} volumen")
        
        return {
            "broker": "coinbase",
            "trades": trades,
            "stats": {
                "total_trades": total_trades,
                "total_volume": round(total_volume, 2),
                "total_fees": round(total_fees, 2),
                "buys": buys,
                "sells": sells
            }
        }
    except Exception as e:
        logger.error(f"Error en get_coinbase_journal: {e}")
        return {
            "broker": "coinbase",
            "trades": [],
            "stats": {},
            "error": str(e)
        }
