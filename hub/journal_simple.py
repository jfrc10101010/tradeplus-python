"""
TRADEPLUS V5.0 - Journal Manager Simple
Obtiene trades de Schwab y Coinbase sin complicaciones
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class JournalSimple:
    """Obtiene trades de ambos brokers"""

    def __init__(self):
        # Imports locales para no romper si faltan
        try:
            from managers.schwab_token_manager import SchwabTokenManager
            from managers.coinbase_jwt_manager import CoinbaseJWTManager
            self.schwab_ready = True
            self.coinbase_ready = True
        except Exception as e:
            print(f"Init error: {e}")
            self.schwab_ready = False
            self.coinbase_ready = False

    def get_schwab_trades(self, days: int = 7) -> List[Dict]:
        """Obtiene trades de Schwab"""
        if not self.schwab_ready:
            return []

        try:
            from managers.schwab_token_manager import SchwabTokenManager

            manager = SchwabTokenManager()
            token = manager._ensure_valid_token()
            token_data = manager.get_current_token()
            account_hash = token_data.get("account_hash", "")

            if not account_hash or not token:
                return []

            url = f"https://api.schwabapi.com/trader/v1/accounts/{account_hash}/transactions"
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params={"types": "TRADE"}
            )

            if response.status_code != 200:
                return []

            data = response.json()
            trades = []

            for t in data:
                if t.get("type") != "TRADE":
                    continue

                try:
                    trades.append({
                        "id": str(t["transactionId"]),
                        "datetime": t["transactionDate"],
                        "symbol": t["transactionItem"]["instrument"]["symbol"],
                        "side": t["transactionItem"]["instruction"],
                        "quantity": abs(float(t["transactionItem"]["amount"])),
                        "price": float(t["transactionItem"]["price"]),
                        "fee": float(t.get("fees", {}).get("commission", 0)),
                        "total": abs(float(t["netAmount"])),
                        "broker": "schwab"
                    })
                except:
                    continue

            return trades

        except Exception as e:
            print(f"Error Schwab: {e}")
            return []

    def get_coinbase_trades(self, days: int = 7) -> List[Dict]:
        """Obtiene trades de Coinbase"""
        if not self.coinbase_ready:
            return []

        try:
            from managers.coinbase_jwt_manager import CoinbaseJWTManager

            manager = CoinbaseJWTManager()
            jwt_token = manager.generate_jwt()

            url = "https://api.coinbase.com/api/v3/brokerage/orders/historical/fills"
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Content-Type": "application/json"
                },
                params={"limit": 100}
            )

            if response.status_code != 200:
                return []

            data = response.json()
            trades = []

            for f in data.get("fills", []):
                try:
                    size = float(f["size"])
                    price = float(f["price"])
                    fee = float(f.get("commission", 0))

                    trades.append({
                        "id": f["trade_id"],
                        "datetime": f["trade_time"],
                        "symbol": f["product_id"],
                        "side": f["side"],
                        "quantity": size,
                        "price": price,
                        "fee": fee,
                        "total": size * price,
                        "broker": "coinbase"
                    })
                except:
                    continue

            return trades

        except Exception as e:
            print(f"Error Coinbase: {e}")
            return []
