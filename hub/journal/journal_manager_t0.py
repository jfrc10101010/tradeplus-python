"""
╔═══════════════════════════════════════════════════════════════╗
║       Journal Manager T0 - FIFO Multi-Broker Metrics         ║
║       TRADEPLUS V5.0 - Refactor con Agrupación por Símbolo  ║
║       T0: Operaciones Abiertas/Cerradas + Win Rate Real     ║
╚═══════════════════════════════════════════════════════════════╝

CAMBIOS T0:
- compute_metrics(): Nueva función core con agrupación FIFO correcta
- Operaciones separadas: abiertas vs cerradas (por símbolo, no por trade)
- Win rate solo cuenta operaciones CERRADAS completas
- Profit factor calculado correctamente
- P&L realizado con porcentaje sobre capital invertido
- P&L no realizado actualizable cada REFRESH_MS=5000
- Compatible con endpoint actual apijournal
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class JournalManager:
    """
    Orquestador central con cálculo FIFO correcto
    T0: Sin cambios en adapters, solo refactor de métricas
    """
    
    def __init__(self, capital_initial: float = 5000.0):
        """
        Args:
            capital_initial: Capital base para cálculos (deprecado, usar balance real)
        """
        # Importar adapters
        try:
            from .schwab_adapter import SchwabAdapter
            from .coinbase_adapter import CoinbaseAdapter
            self.schwab = SchwabAdapter()
            self.coinbase = CoinbaseAdapter()
        except ImportError:
            logger.warning("Adapters no disponibles en test mode")
            self.schwab = None
            self.coinbase = None
        
        self.capital_initial = capital_initial
        self._real_balance_cache = None
    
    def get_real_balance(self) -> float:
        """Obtiene balance real de Schwab API"""
        if self._real_balance_cache:
            return self._real_balance_cache
        
        try:
            if self.schwab:
                balance_data = self.schwab.get_account_balance()
                account_value = balance_data.get('account_value', 0.0)
                if account_value > 0:
                    self._real_balance_cache = account_value
                    return account_value
        except Exception as e:
            logger.error(f"Error obteniendo balance real: {e}")
        
        return self.capital_initial
    
    # ========================================================================
    # T0: FUNCIÓN CORE - compute_metrics con FIFO correcto
    # ========================================================================
    
    def compute_metrics(self, trades: List[Dict], days: Optional[int] = None, 
                       current_prices: Optional[Dict[str, float]] = None) -> Dict:
        """
        Calcula métricas completas con agrupación FIFO por símbolo
        
        Args:
            trades: Lista de trades normalizados de ambos brokers
            days: Filtrar últimos N días (None = todos)
            current_prices: Dict {symbol: precio_actual} para P&L no realizado
        
        Returns:
            Dict con estructura completa para apijournal:
            {
                'timestamp': str,
                'period': {'days': int, 'from': str, 'to': str},
                'capital': {
                    'initial': float,
                    'current': float,  # Balance real API
                    'pl_total_usd': float,
                    'pl_total_percent': float
                },
                'positions': {
                    'open_count': int,      # Posiciones abiertas (por símbolo)
                    'closed_count': int,    # Posiciones cerradas completas
                    'open_detail': [...]    # Lista de posiciones abiertas
                },
                'stats': {
                    'total_ops': int,           # Total operaciones (abiertas + cerradas)
                    'wins': int,                # Operaciones cerradas ganadoras
                    'losses': int,              # Operaciones cerradas perdedoras
                    'win_rate': float,          # % wins / (wins + losses)
                    'profit_factor': float,     # Total wins / Total losses
                    'pl_realized_usd': float,   # P&L de cerradas
                    'pl_realized_percent': float,  # % sobre capital invertido en cerradas
                    'pl_unrealized_usd': float, # P&L de abiertas (requiere precios)
                    'avg_pl_per_trade': float
                },
                'trades': [...]  # Trades con P&L individual
            }
        """
        from datetime import timezone
        
        # Filtrar por período
        if days:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            trades = [
                t for t in trades
                if datetime.fromisoformat(t['datetime'].replace('Z', '+00:00')) >= cutoff
            ]
        
        if not trades:
            return self._empty_metrics()
        
        # Agrupar por símbolo
        by_symbol = defaultdict(list)
        for trade in trades:
            by_symbol[trade['symbol']].append(trade)
        
        # Ordenar cada símbolo por fecha
        for symbol in by_symbol:
            by_symbol[symbol].sort(key=lambda t: t['datetime'])
        
        # Procesar cada símbolo con FIFO
        open_positions = []
        closed_operations = []
        all_trades_processed = []
        
        for symbol, symbol_trades in by_symbol.items():
            result = self._process_symbol_fifo(symbol, symbol_trades, current_prices)
            
            if result['open_position']:
                open_positions.append(result['open_position'])
            
            closed_operations.extend(result['closed_operations'])
            all_trades_processed.extend(result['trades'])
        
        # Calcular métricas agregadas
        wins = len([op for op in closed_operations if op['pl_usd'] > 0])
        losses = len([op for op in closed_operations if op['pl_usd'] <= 0])
        
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
        
        total_wins_usd = sum([op['pl_usd'] for op in closed_operations if op['pl_usd'] > 0])
        total_losses_usd = abs(sum([op['pl_usd'] for op in closed_operations if op['pl_usd'] <= 0]))
        profit_factor = (total_wins_usd / total_losses_usd) if total_losses_usd > 0 else 0.0
        
        pl_realized_usd = sum([op['pl_usd'] for op in closed_operations])
        capital_invested_closed = sum([op['cost_basis'] for op in closed_operations])
        pl_realized_percent = (pl_realized_usd / capital_invested_closed * 100) if capital_invested_closed > 0 else 0.0
        
        pl_unrealized_usd = sum([pos['unrealized_pl'] for pos in open_positions])
        
        # Balance real
        current_balance = self.get_real_balance()
        pl_total = pl_realized_usd + pl_unrealized_usd
        
        # Período
        dates = sorted([t['datetime'][:10] for t in trades])
        period_from = dates[0] if dates else None
        period_to = dates[-1] if dates else None
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'period': {
                'days': days,
                'from': period_from,
                'to': period_to,
                'trades_count': len(trades)
            },
            'capital': {
                'initial': self.capital_initial,
                'current': round(current_balance, 2),
                'pl_total_usd': round(pl_total, 2),
                'pl_total_percent': round((pl_total / self.capital_initial * 100), 2)
            },
            'positions': {
                'open_count': len(open_positions),
                'closed_count': len(closed_operations),
                'open_detail': open_positions
            },
            'stats': {
                'total_ops': len(open_positions) + len(closed_operations),
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 2),
                'profit_factor': round(profit_factor, 2),
                'pl_realized_usd': round(pl_realized_usd, 2),
                'pl_realized_percent': round(pl_realized_percent, 2),
                'pl_unrealized_usd': round(pl_unrealized_usd, 2),
                'avg_pl_per_trade': round(pl_realized_usd / len(closed_operations), 2) if closed_operations else 0.0
            },
            'trades': all_trades_processed
        }
    
    def _process_symbol_fifo(self, symbol: str, trades: List[Dict], 
                            current_prices: Optional[Dict[str, float]] = None) -> Dict:
        """
        Procesa un símbolo con matching FIFO correcto
        
        Returns:
            {
                'open_position': dict o None,
                'closed_operations': [list de ops cerradas],
                'trades': [trades con metadata]
            }
        """
        buy_queue = []  # Cola FIFO de compras
        closed_ops = []
        trades_meta = []
        
        for trade in trades:
            side = trade['side'].upper()
            qty = float(trade['quantity'])
            price = float(trade['price'])
            total = float(trade.get('total', qty * price))
            fee = float(trade.get('fee', 0))
            
            trade_meta = trade.copy()
            trade_meta['pl_usd'] = 0.0
            trade_meta['pl_percent'] = 0.0
            trade_meta['is_closed'] = False
            
            if side == 'BUY':
                # Agregar a cola FIFO
                buy_queue.append({
                    'qty': qty,
                    'price': price,
                    'cost': total + fee,
                    'trade_id': trade['id'],
                    'datetime': trade['datetime']
                })
                trade_meta['cost_basis'] = total + fee
            
            elif side == 'SELL':
                # Hacer match con compras FIFO
                qty_remaining = qty
                sell_proceeds = total - fee
                total_cost_basis = 0.0
                
                while qty_remaining > 0.0001 and buy_queue:
                    buy = buy_queue[0]
                    
                    if buy['qty'] <= qty_remaining:
                        # Consumir compra completa
                        matched_qty = buy['qty']
                        qty_remaining -= matched_qty
                        total_cost_basis += buy['cost']
                        buy_queue.pop(0)
                    else:
                        # Consumir parcial
                        matched_qty = qty_remaining
                        cost_portion = (matched_qty / buy['qty']) * buy['cost']
                        total_cost_basis += cost_portion
                        buy['qty'] -= matched_qty
                        buy['cost'] -= cost_portion
                        qty_remaining = 0.0
                
                # Crear operación cerrada
                pl_usd = sell_proceeds - total_cost_basis
                pl_percent = (pl_usd / total_cost_basis * 100) if total_cost_basis > 0 else 0.0
                
                closed_ops.append({
                    'symbol': symbol,
                    'pl_usd': pl_usd,
                    'pl_percent': pl_percent,
                    'cost_basis': total_cost_basis,
                    'sell_proceeds': sell_proceeds,
                    'qty': qty,
                    'sell_date': trade['datetime']
                })
                
                trade_meta['pl_usd'] = pl_usd
                trade_meta['pl_percent'] = round(pl_percent, 2)
                trade_meta['is_closed'] = True
            
            trades_meta.append(trade_meta)
        
        # Calcular posición abierta si hay compras sin match
        open_position = None
        if buy_queue:
            total_qty = sum([b['qty'] for b in buy_queue])
            total_cost = sum([b['cost'] for b in buy_queue])
            avg_price = total_cost / total_qty if total_qty > 0 else 0.0
            
            # P&L no realizado
            current_price = current_prices.get(symbol, avg_price) if current_prices else avg_price
            current_value = total_qty * current_price
            unrealized_pl = current_value - total_cost
            unrealized_percent = (unrealized_pl / total_cost * 100) if total_cost > 0 else 0.0
            
            open_position = {
                'symbol': symbol,
                'qty': round(total_qty, 8),
                'avg_cost': round(avg_price, 2),
                'current_price': round(current_price, 2),
                'cost_basis': round(total_cost, 2),
                'current_value': round(current_value, 2),
                'unrealized_pl': round(unrealized_pl, 2),
                'unrealized_percent': round(unrealized_percent, 2),
                'entries': len(buy_queue)
            }
        
        return {
            'open_position': open_position,
            'closed_operations': closed_ops,
            'trades': trades_meta
        }
    
    def _empty_metrics(self) -> Dict:
        """Retorna estructura vacía"""
        from datetime import timezone
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'period': {'days': 0, 'from': None, 'to': None, 'trades_count': 0},
            'capital': {
                'initial': self.capital_initial,
                'current': self.get_real_balance(),
                'pl_total_usd': 0.0,
                'pl_total_percent': 0.0
            },
            'positions': {
                'open_count': 0,
                'closed_count': 0,
                'open_detail': []
            },
            'stats': {
                'total_ops': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'pl_realized_usd': 0.0,
                'pl_realized_percent': 0.0,
                'pl_unrealized_usd': 0.0,
                'avg_pl_per_trade': 0.0
            },
            'trades': []
        }
    
    # ========================================================================
    # COMPATIBILIDAD CON ENDPOINT ACTUAL
    # ========================================================================
    
    def get_combined_journal(self, days: int = 30, 
                            current_prices: Optional[Dict[str, float]] = None) -> Dict:
        """
        Método compatible con endpoint actual /api/journal
        Combina Schwab + Coinbase y aplica compute_metrics()
        
        Args:
            days: Número de días hacia atrás
            current_prices: Precios actuales para P&L no realizado
        
        Returns:
            Dict con estructura esperada por server.js
        """
        all_trades = []
        
        # Obtener trades de Schwab
        try:
            if self.schwab:
                schwab_trades = self.schwab.get_transactions(days=days)
                all_trades.extend(schwab_trades)
                logger.info(f"Schwab: {len(schwab_trades)} trades obtenidos")
        except Exception as e:
            logger.error(f"Error obteniendo Schwab: {e}")
        
        # Obtener trades de Coinbase
        try:
            if self.coinbase:
                coinbase_fills = self.coinbase.get_fills(days=days)
                all_trades.extend(coinbase_fills)
                logger.info(f"Coinbase: {len(coinbase_fills)} fills obtenidos")
        except Exception as e:
            logger.error(f"Error obteniendo Coinbase: {e}")
        
        # Aplicar compute_metrics
        return self.compute_metrics(all_trades, days=days, current_prices=current_prices)
    
    def get_trades_by_broker(self, broker: str, days: int = 7, 
                            current_prices: Optional[Dict[str, float]] = None) -> Dict:
        """
        Método compatible con endpoint /api/journal/broker/:name
        
        Args:
            broker: 'schwab' o 'coinbase'
            days: Número de días
            current_prices: Precios actuales
        
        Returns:
            Dict con métricas de un solo broker
        """
        trades = []
        
        try:
            if broker.lower() == 'schwab' and self.schwab:
                trades = self.schwab.get_transactions(days=days)
            elif broker.lower() == 'coinbase' and self.coinbase:
                trades = self.coinbase.get_fills(days=days)
            
            logger.info(f"{broker}: {len(trades)} trades obtenidos")
        except Exception as e:
            logger.error(f"Error obteniendo {broker}: {e}")
            return {'error': str(e), 'broker': broker, **self._empty_metrics()}
        
        result = self.compute_metrics(trades, days=days, current_prices=current_prices)
        result['broker'] = broker
        return result


# ========================================================================
# FUNCIONES HELPER PARA COMPATIBILIDAD LEGACY
# ========================================================================

def get_combined_journal(days: int = 30, capital_initial: float = 5000.0) -> Dict:
    """Función standalone para backward compatibility"""
    manager = JournalManager(capital_initial=capital_initial)
    return manager.get_combined_journal(days=days)


def get_trades_by_broker(broker: str, days: int = 7, capital_initial: float = 5000.0) -> Dict:
    """Función standalone para backward compatibility"""
    manager = JournalManager(capital_initial=capital_initial)
    return manager.get_trades_by_broker(broker, days=days)
