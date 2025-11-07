"""
╔═══════════════════════════════════════════════════════════════╗
║           Journal Module - Package Initialization            ║
║           TRADEPLUS V5.0 - Multi-Broker System              ║
╚═══════════════════════════════════════════════════════════════╝
"""

from .schwab_adapter import SchwabAdapter, get_schwab_journal
from .coinbase_adapter import CoinbaseAdapter, get_coinbase_journal

__all__ = [
    "SchwabAdapter",
    "CoinbaseAdapter",
    "get_schwab_journal",
    "get_coinbase_journal"
]

__version__ = "1.0.0"
__module_name__ = "journal"
