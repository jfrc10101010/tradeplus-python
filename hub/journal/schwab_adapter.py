"""
╔═══════════════════════════════════════════════════════════════╗
║         Schwab Adapter - Transaction Normalizer              ║
║         TRADEPLUS V5.0 - Multi-Broker System                ║
╚═══════════════════════════════════════════════════════════════╝

Responsabilidad Única:
- Obtiene transacciones de Schwab API
- Normaliza a formato común
- Maneja errores específicos de Schwab
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import requests

logger = logging.getLogger(__name__)


class SchwabAdapter:
    """Adaptador exclusivo para Schwab - obtiene y normaliza trades"""
    
    BASE_URL = "https://api.schwabapi.com"
    ENDPOINT = "/trader/v1/accounts/{account_hash}/transactions"
    
    def __init__(self):
        """Inicializa el adaptador con token manager"""
        try:
            # Importar desde hub.managers
            import sys
            import os
            hub_path = os.path.dirname(os.path.dirname(__file__))
            if hub_path not in sys.path:
                sys.path.insert(0, hub_path)
            
            from managers.schwab_token_manager import SchwabTokenManager
            self.token_manager = SchwabTokenManager()
            self.session = requests.Session()
        except ImportError as e:
            logger.error(f"Error importando SchwabTokenManager: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene headers con token válido (auto-renovado si es necesario)"""
        try:
            token = self.token_manager.get_current_token()
            return {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
        except Exception as e:
            logger.error(f"Error obteniendo token Schwab: {e}")
            raise
    
    def _get_account_hash(self) -> str:
        """Extrae account_hash (hashValue) mediante llamada a API de accountNumbers"""
        try:
            # Obtener token válido
            token = self.token_manager.get_current_token()
            
            # Llamar a API de accountNumbers para obtener el hashValue (encrypted account number)
            url = f"{self.BASE_URL}/trader/v1/accounts/accountNumbers"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            accounts = response.json()
            logger.debug(f"Respuesta de accountNumbers API: {accounts}")
            
            if not accounts or len(accounts) == 0:
                raise ValueError("No se encontraron cuentas")
            
            # Estructura: [{"accountNumber": "74164065", "hashValue": "6C2F..."}]
            first_account = accounts[0]
            account_hash = first_account.get("hashValue")
            
            if not account_hash:
                logger.error(f"Estructura de cuenta: {first_account}")
                raise ValueError("hashValue no encontrado en accountNumbers")
            
            logger.debug(f"Account hash obtenido: {account_hash}")
            return account_hash
            
        except Exception as e:
            logger.error(f"Error obteniendo account_hash: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        Obtiene balance actual de la cuenta Schwab
        
        Returns:
            Dict con: cash_balance, account_value (Net Liq), buying_power
        """
        try:
            logger.info("Obteniendo balance de cuenta Schwab...")
            
            token = self.token_manager.get_current_token()
            account_hash = self._get_account_hash()
            
            url = f"{self.BASE_URL}/trader/v1/accounts/{account_hash}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            sec_account = data.get('securitiesAccount', {})
            balances = sec_account.get('currentBalances', {})
            
            result = {
                'cash_balance': balances.get('cashBalance', 0.0),
                'account_value': balances.get('liquidationValue', 0.0),  # Net Liq
                'buying_power': balances.get('buyingPower', 0.0),
                'long_market_value': balances.get('longMarketValue', 0.0)
            }
            
            logger.info(f"Balance obtenido: Net Liq=${result['account_value']:,.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return {'cash_balance': 0.0, 'account_value': 0.0, 'buying_power': 0.0, 'long_market_value': 0.0}
    
    def get_transactions(self, days: int = 7) -> List[Dict]:
        """
        Obtiene y normaliza transacciones de Schwab
        
        Args:
            days: Número de días hacia atrás a consultar
            
        Returns:
            Lista de transacciones normalizadas
            
        Raises:
            requests.RequestException: Error en la API REST
            ValueError: Datos inválidos en la respuesta
        """
        try:
            logger.info(f"Obteniendo transacciones Schwab (últimos {days} días)")
            
            # Calcular rango de fechas en formato ISO 8601 completo
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Formato: YYYY-MM-DDTHH:MM:SS.000Z (requerido por Schwab API)
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Construir URL con account_hash (hashValue de /accountNumbers)
            account_hash = self._get_account_hash()
            url = f"{self.BASE_URL}{self.ENDPOINT.format(account_hash=account_hash)}"
            
            # Parámetros de filtro
            params = {
                "types": "TRADE",  # Solo trades, no deposits/withdrawals
                "startDate": start_str,
                "endDate": end_str
            }
            
            # Request con headers válidos
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            transactions = response.json()
            
            if not isinstance(transactions, list):
                logger.warning(f"Respuesta no es lista: {type(transactions)}")
                return []
            
            # Normalizar cada transacción
            normalized = []
            for tx in transactions:
                try:
                    normalized_tx = self._normalize_transaction(tx)
                    if normalized_tx:
                        normalized.append(normalized_tx)
                except Exception as e:
                    logger.warning(f"Transacción individual rechazada: {e}")
                    continue
            
            logger.info(f"✅ {len(normalized)} transacciones normalizadas de Schwab")
            return normalized
            
        except requests.RequestException as e:
            logger.error(f"Error REST en Schwab API: {e}")
            # No lanzar excepción, devolver lista vacía para no romper el journal
            return []
        except Exception as e:
            logger.error(f"Error inesperado obteniendo transacciones: {e}")
            # No lanzar excepción, devolver lista vacía para no romper el journal
            return []
    
    def _normalize_transaction(self, tx: Dict) -> Optional[Dict]:
        """
        Normaliza una transacción Schwab al formato común
        
        Estructura real de Schwab:
        {
          "activityId": 106403717567,
          "time": "2025-11-06T18:38:29+0000",
          "type": "TRADE",
          "netAmount": 736.26,
          "transferItems": [
            {"instrument": {"assetType": "CURRENCY", "symbol": "CURRENCY_USD"}, "feeType": "COMMISSION"},
            {"instrument": {"assetType": "EQUITY", "symbol": "ORCL"}, "amount": -3.0, "cost": 736.26, "price": 245.42, "positionEffect": "CLOSING"}
          ]
        }
        
        Args:
            tx: Transacción cruda de Schwab
            
        Returns:
            Transacción normalizada o None si no válida
        """
        try:
            # Validación estructura mínima
            if not isinstance(tx, dict):
                return None
            
            if "transferItems" not in tx or not isinstance(tx["transferItems"], list):
                logger.debug("Transacción sin transferItems")
                return None
            
            # Buscar el transferItem que tiene el instrumento (no CURRENCY)
            stock_item = None
            commission = 0.0
            
            for item in tx["transferItems"]:
                instrument = item.get("instrument", {})
                asset_type = instrument.get("assetType", "")
                
                # Buscar item con fee COMMISSION
                if item.get("feeType") == "COMMISSION":
                    commission = abs(float(item.get("amount", 0) or 0))
                
                # Buscar item con EQUITY/OPTION (el trade real)
                if asset_type in ["EQUITY", "OPTION"] and not item.get("feeType"):
                    stock_item = item
            
            if not stock_item:
                logger.debug("No se encontró item de stock/option en transferItems")
                return None
            
            # Extraer datos del stock_item
            instrument = stock_item.get("instrument", {})
            symbol = instrument.get("symbol", "UNKNOWN")
            
            # Cantidad (amount negativo = SELL, positivo = BUY)
            amount = float(stock_item.get("amount", 0) or 0)
            quantity = abs(amount)
            side = "SELL" if amount < 0 else "BUY"
            
            # Precio y total
            price = float(stock_item.get("price", 0) or 0)
            total = abs(float(tx.get("netAmount", 0) or 0))
            
            # ID y fecha
            trade_id = str(tx.get("activityId", ""))
            date_str = tx.get("time", "")
            
            if not all([trade_id, symbol]):
                logger.debug(f"Datos incompletos: id={trade_id}, sym={symbol}")
                return None
            
            # Parsear fecha
            try:
                datetime_obj = datetime.fromisoformat(date_str.replace("+0000", "+00:00"))
            except (ValueError, AttributeError):
                datetime_obj = datetime.now()
                logger.debug(f"Fecha no válida: {date_str}, usando ahora")
            
            # Formato normalizado
            return {
                "id": trade_id,
                "datetime": datetime_obj.isoformat(),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "fee": commission,
                "amount": round(total, 2),
                "status": tx.get("status", "UNKNOWN"),
                "broker": "schwab"
            }
            
        except (KeyError, ValueError, TypeError) as e:
            logger.debug(f"Error normalizando transacción: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado normalizando: {e}")
            return None


async def get_schwab_journal(days: int = 7) -> Dict:
    """
    Función de conveniencia: obtiene journal completo de Schwab
    
    Args:
        days: Rango de días
        
    Returns:
        Dict con trades y estadísticas agregadas
    """
    try:
        adapter = SchwabAdapter()
        trades = adapter.get_transactions(days=days)
        
        # Estadísticas
        total_trades = len(trades)
        total_volume = sum(t["amount"] for t in trades)
        total_fees = sum(t["fee"] for t in trades)
        buys = sum(1 for t in trades if t["side"] == "BUY")
        sells = sum(1 for t in trades if t["side"] == "SELL")
        
        logger.info(f"Journal Schwab: {total_trades} trades, ${total_volume:.2f} volumen")
        
        return {
            "broker": "schwab",
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
        logger.error(f"Error en get_schwab_journal: {e}")
        return {
            "broker": "schwab",
            "trades": [],
            "stats": {},
            "error": str(e)
        }
