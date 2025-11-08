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
    
    # ========================================================================
    # FORMATEO CENTRALIZADO DE NÚMEROS
    # ========================================================================
    
    def _format_number(self, value: float, decimals: int = 2, use_thousands: bool = True) -> str:
        """
        Formatea un número con separador de miles y decimales específicos
        
        Args:
            value: Valor numérico a formatear
            decimals: Número de decimales (2-8)
            use_thousands: Si True, usa coma como separador de miles
        
        Returns:
            String formateado: "1,234.56" o "1234.56"
        """
        if use_thousands:
            return f"{value:,.{decimals}f}"
        else:
            return f"{value:.{decimals}f}"
    
    def _get_decimals_for_trade(self, trade: Dict) -> int:
        """
        Determina el número de decimales correcto para un trade según broker y símbolo
        
        Args:
            trade: Dict con 'broker' y 'symbol'
        
        Returns:
            Número de decimales (2 para stocks, 2-8 para crypto)
        """
        broker = trade.get('broker', 'schwab')
        symbol = trade.get('symbol', '')
        
        if broker == 'schwab':
            # Stocks: siempre 2 decimales
            return 2
        elif broker == 'coinbase':
            # Crypto: depende del quote_increment
            if self.coinbase:
                return self.coinbase.get_decimals_for_symbol(symbol)
            return 8  # Default para crypto
        
        return 2  # Default general
    
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
        
        # NO filtrar trades antes del FIFO - necesitamos todo el historial para calcular correctamente
        # El filtro se aplicará DESPUÉS a las operaciones cerradas
        cutoff = None
        if days:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
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
        
        # FILTRAR operaciones cerradas por período (si se especificó)
        # El filtro se aplica a la fecha de la VENTA (cierre de la operación)
        if cutoff:
            closed_operations = [
                op for op in closed_operations
                if datetime.fromisoformat(op['sell_date'].replace('Z', '+00:00')) >= cutoff
            ]
            # Filtrar también los trades mostrados en la lista
            all_trades_processed = [
                t for t in all_trades_processed
                if datetime.fromisoformat(t['datetime'].replace('Z', '+00:00')) >= cutoff
            ]
        
        # Calcular métricas agregadas
        wins = len([op for op in closed_operations if op['pl_usd'] > 0])
        losses = len([op for op in closed_operations if op['pl_usd'] <= 0])
        
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0
        
        total_wins_usd = sum([op['pl_usd'] for op in closed_operations if op['pl_usd'] > 0])
        total_losses_usd = abs(sum([op['pl_usd'] for op in closed_operations if op['pl_usd'] <= 0]))
        
        # Profit Factor = Total Wins / Total Losses
        # Si no hay pérdidas, el Profit Factor es técnicamente infinito, pero usamos 999.99 como indicador
        if total_losses_usd > 0:
            profit_factor = total_wins_usd / total_losses_usd
        elif total_wins_usd > 0:
            profit_factor = 999.99  # Indicador de "sin pérdidas" (win rate 100%)
        else:
            profit_factor = 0.0  # No hay trades cerrados
        
        pl_realized_usd = sum([op['pl_usd'] for op in closed_operations])
        capital_invested_closed = sum([op['cost_basis'] for op in closed_operations])
        pl_realized_percent = (pl_realized_usd / capital_invested_closed * 100) if capital_invested_closed > 0 else 0.0
        
        # DEBUG: Log de cálculos
        logger.info(f"📊 P&L Realizado - Ops cerradas: {len(closed_operations)}, "
                   f"PL USD: ${pl_realized_usd:.2f}, Capital invertido: ${capital_invested_closed:.2f}, "
                   f"PL %: {pl_realized_percent:.2f}%")
        
        pl_unrealized_usd = sum([pos['unrealized_pl'] for pos in open_positions])
        capital_invested_open = sum([pos['cost_basis'] for pos in open_positions])
        pl_unrealized_percent = (pl_unrealized_usd / capital_invested_open * 100) if capital_invested_open > 0 else 0.0
        
        # Balance real
        current_balance = self.get_real_balance()
        pl_total = pl_realized_usd + pl_unrealized_usd
        
        # Período - usar los trades FILTRADOS para calcular el rango de fechas
        dates = sorted([t['datetime'][:10] for t in all_trades_processed])
        period_from = dates[0] if dates else None
        period_to = dates[-1] if dates else None
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'period': {
                'days': days,
                'from': period_from,
                'to': period_to,
                'trades_count': len(all_trades_processed)
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
                'total_ops': len(closed_operations),  # Solo operaciones cerradas
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 2),
                'profit_factor': round(profit_factor, 2),
                'pl_realized_usd': round(pl_realized_usd, 2),
                'pl_realized_percent': round(pl_realized_percent, 2),
                'pl_unrealized_usd': round(pl_unrealized_usd, 2),
                'pl_unrealized_percent': round(pl_unrealized_percent, 2),
                'avg_pl_per_trade': round(pl_realized_usd / len(closed_operations), 2) if closed_operations else 0.0
            },
            'trades': all_trades_processed
        }
    
    def _format_metrics_response(self, metrics: Dict) -> Dict:
        """
        Formatea todos los números en la respuesta de métricas con formato correcto
        
        Args:
            metrics: Dict retornado por compute_metrics()
        
        Returns:
            Dict con números formateados como strings donde corresponde
        """
        # Por ahora retornamos sin formatear - el frontend hará el formateo
        # Esto es porque necesitamos números para cálculos en Ag-Grid
        # El formateo se hace en los valueFormatters de Ag-Grid
        return metrics
    
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
                
                # Crear operación cerrada SOLO si hubo match con compras
                if total_cost_basis > 0:
                    pl_usd = sell_proceeds - total_cost_basis
                    pl_percent = (pl_usd / total_cost_basis * 100)
                    
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
                    trade_meta['cost_basis'] = total_cost_basis
                    trade_meta['is_closed'] = True
                else:
                    # SELL sin BUY previo - ignorar (short o datos incompletos)
                    logger.warning(f"⚠️ SELL sin BUY previo para {symbol} - ignorando en P&L")
                    trade_meta['pl_usd'] = 0.0
                    trade_meta['pl_percent'] = 0.0
                    trade_meta['is_closed'] = False
            
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
            current_prices: Precios actuales para P&L no realizado (si None, se obtienen automáticamente)
        
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
        
        # Si no se pasaron precios, obtenerlos de Schwab API
        if current_prices is None and all_trades:
            current_prices = self._get_current_prices(all_trades)
        
        # Aplicar compute_metrics con precios actuales
        return self.compute_metrics(all_trades, days=days, current_prices=current_prices)
    
    def _get_current_prices(self, trades: List[Dict]) -> Dict[str, float]:
        """
        Obtiene precios actuales para todos los símbolos en trades
        
        Args:
            trades: Lista de trades
        
        Returns:
            Dict con symbol: precio actual
        """
        try:
            # Extraer símbolos únicos
            symbols = list(set([t['symbol'] for t in trades if t.get('symbol')]))
            
            if not symbols:
                return {}
            
            # Separar por broker
            schwab_symbols = [s for s in symbols if not s.endswith('-USD')]  # Stocks
            coinbase_symbols = [s for s in symbols if s.endswith('-USD')]     # Crypto
            
            prices = {}
            
            # Obtener quotes de Schwab
            if schwab_symbols and self.schwab:
                try:
                    schwab_prices = self.schwab.get_quotes(schwab_symbols)
                    prices.update(schwab_prices)
                    logger.info(f"Precios obtenidos para {len(schwab_prices)} símbolos de Schwab")
                except Exception as e:
                    logger.error(f"Error obteniendo quotes Schwab: {e}")
            
            # Obtener precios de Coinbase (criptomonedas)
            if coinbase_symbols and self.coinbase:
                try:
                    coinbase_prices = self.coinbase.get_quotes(coinbase_symbols)
                    prices.update(coinbase_prices)
                    logger.info(f"Precios obtenidos para {len(coinbase_prices)} símbolos de Coinbase")
                except Exception as e:
                    logger.error(f"Error obteniendo quotes Coinbase: {e}")
            
            return prices
            
        except Exception as e:
            logger.error(f"Error obteniendo precios actuales: {e}")
            return {}
    
    def get_trades_by_broker(self, broker: str, days: int = 7, 
                            current_prices: Optional[Dict[str, float]] = None) -> Dict:
        """
        Método compatible con endpoint /api/journal/broker/:name
        
        Args:
            broker: 'schwab' o 'coinbase'
            days: Número de días
            current_prices: Precios actuales (si None, se obtienen automáticamente)
        
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
        
        # Si no se pasaron precios, obtenerlos automáticamente
        if current_prices is None and trades:
            current_prices = self._get_current_prices(trades)
        
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
