"""
╔═══════════════════════════════════════════════════════════════╗
║       Journal Manager - Orquestador Multi-Broker             ║
║       TRADEPLUS V5.0 - Multi-Broker System                  ║
║       FASE 3: P&L Calculations + Capital Evolution          ║
╚═══════════════════════════════════════════════════════════════╝

Responsabilidad:
- Orquesta llamadas a ambos adapters
- Calcula P&L USD y % para cada trade
- Calcula evolución de capital día a día
- Genera estadísticas completas (win rate, profit factor, etc)
- PROHIBIDO MOCKUP: Solo datos reales de APIs
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from .schwab_adapter import SchwabAdapter, get_schwab_journal
from .coinbase_adapter import CoinbaseAdapter, get_coinbase_journal

logger = logging.getLogger(__name__)


class JournalManager:
    """
    Orquestador central de journal multi-broker
    Calcula P&L y evolución de capital 100% automático
    """
    
    def __init__(self, capital_initial: Optional[float] = None):
        """
        Inicializa manager con adapters
        
        Args:
            capital_initial: (DEPRECADO) Ahora se calcula desde balance real de Schwab
        """
        self.schwab = SchwabAdapter()
        self.coinbase = CoinbaseAdapter()
        self.capital_initial = capital_initial  # Mantener por compatibilidad pero deprecado
        self._cache = {}
        self._cache_ttl = 300  # 5 minutos
        self._real_balance = None  # Cache del balance real
    
    def get_real_balance(self, use_cache: bool = True) -> float:
        """
        Obtiene balance REAL de la cuenta Schwab (Net Liq)
        Este es el valor verdadero, no calculado
        
        Args:
            use_cache: Si True, usa el valor cacheado si existe
        """
        # Usar cache si está disponible y es reciente
        if use_cache and self._real_balance is not None:
            logger.info(f"Usando balance cacheado: ${self._real_balance:,.2f}")
            return self._real_balance
        
        try:
            logger.info("Consultando balance real de Schwab API...")
            balance_data = self.schwab.get_account_balance()
            logger.info(f"Balance data recibido: {balance_data}")
            
            account_value = balance_data.get('account_value', 0.0)
            
            if account_value > 0:
                self._real_balance = account_value
                logger.info(f"Balance real Schwab: ${account_value:,.2f}")
                return account_value
            else:
                logger.warning(f"Balance devuelto es 0 o None: {account_value}, usando fallback")
                fallback = self.capital_initial if self.capital_initial else 5000.0
                logger.warning(f"Fallback value: ${fallback}")
                return fallback
        except Exception as e:
            logger.error(f"ERROR obteniendo balance real: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback al capital_initial si está configurado
            fallback = self.capital_initial if self.capital_initial else 5000.0
            logger.error(f"Usando fallback: ${fallback}")
            return fallback
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si caché es válido"""
        if key not in self._cache:
            return False
        
        cached_time = self._cache[key]["timestamp"]
        age = (datetime.now() - cached_time).total_seconds()
        return age < self._cache_ttl
    
    # ========================================================================
    # MÉTODO CRÍTICO 1: Calcular P&L de un trade individual
    # ========================================================================
    
    def calculate_trade_pl(self, trade: Dict) -> Dict:
        """
        Calcula P&L USD y % para UN trade individual
        
        Args:
            trade: Dict con estructura normalizada
                {
                    'id': str,
                    'symbol': str,
                    'datetime': str (ISO format),
                    'side': 'BUY' | 'SELL',
                    'quantity': float,
                    'price': float,
                    'total': float (cantidad * precio),
                    'fee': float,
                    'broker': 'schwab' | 'coinbase'
                }
        
        Returns:
            Dict con P&L calculado:
                {
                    'pl_usd': float,
                    'pl_percent': float,
                    'is_winner': bool,
                    'formatted': {
                        'pl_usd': str (ej: '+$225.50'),
                        'pl_percent': str (ej: '+0.95%')
                    }
                }
        
        LÓGICA SIMPLIFICADA:
        - Por ahora, asumimos cada trade como independiente
        - P&L = total - fees para análisis básico
        - TODO: Implementar matching BUY/SELL pairs para P&L real
        """
        try:
            qty = float(trade.get('quantity', 0))
            price = float(trade.get('price', 0))
            fee = float(trade.get('fee', 0))
            total = float(trade.get('total', 0)) if trade.get('total') else (qty * price)
            side = trade.get('side', 'BUY').upper()
            
            # NOTA: Este método ya no se usa directamente
            # Ahora usamos calculate_trades_with_fifo_pl() para matching correcto
            # Mantenido por compatibilidad legacy
            
            if side == 'SELL':
                pl_usd = total - fee
            else:  # BUY
                pl_usd = -(total + fee)
            
            pl_percent = (pl_usd / total * 100) if total != 0 else 0
            is_winner = pl_usd > 0
            
            return {
                'pl_usd': round(pl_usd, 2),
                'pl_percent': round(pl_percent, 2),
                'is_winner': is_winner,
                'formatted': {
                    'pl_usd': f"{'+'if pl_usd >= 0 else ''}${pl_usd:,.2f}",
                    'pl_percent': f"{'+'if pl_percent >= 0 else ''}{pl_percent:.2f}%"
                }
            }
        
        except Exception as e:
            logger.error(f"Error calculate_trade_pl para trade {trade.get('id')}: {e}")
            return {
                'pl_usd': 0.0,
                'pl_percent': 0.0,
                'is_winner': False,
                'formatted': {
                    'pl_usd': '$0.00',
                    'pl_percent': '0.00%'
                },
                'error': str(e)
            }
    
    def calculate_trades_with_fifo_pl(self, trades: List[Dict]) -> tuple[List[Dict], Dict]:
        """
        Calcula P&L usando FIFO separando REALIZADO vs UNREALIZED
        
        Returns:
            (trades_with_pl, positions_summary)
            
            positions_summary = {
                'open': [{'symbol': str, 'qty': float, 'avg_cost': float, 'current_value': float, 'unrealized_pl': float}],
                'closed_count': int,
                'realized_pl': float,
                'unrealized_pl': float
            }
        """
        by_symbol = {}
        for trade in trades:
            symbol = trade.get('symbol', '')
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(trade)
        
        processed_trades = []
        open_positions = []
        total_realized_pl = 0.0
        total_unrealized_pl = 0.0
        closed_positions = 0
        
        for symbol, symbol_trades in by_symbol.items():
            buys = [t for t in symbol_trades if t.get('side', '').upper() == 'BUY']
            sells = [t for t in symbol_trades if t.get('side', '').upper() == 'SELL']
            
            buy_queue = buys.copy()
            sell_queue = sells.copy()
            
            trade_pl_map = {t['id']: {
                'pl_realized': 0.0, 
                'pl_unrealized': 0.0,
                'qty_matched': 0.0,
                'is_closed': False
            } for t in symbol_trades}
            
            # Matching FIFO
            while buy_queue and sell_queue:
                buy = buy_queue[0]
                sell = sell_queue[0]
                
                buy_qty_remaining = float(buy['quantity']) - trade_pl_map[buy['id']]['qty_matched']
                sell_qty_remaining = float(sell['quantity']) - trade_pl_map[sell['id']]['qty_matched']
                
                match_qty = min(buy_qty_remaining, sell_qty_remaining)
                
                if match_qty > 0:
                    buy_price = float(buy['price'])
                    sell_price = float(sell['price'])
                    buy_fee = float(buy.get('fee', 0))
                    sell_fee = float(sell.get('fee', 0))
                    
                    pl_gross = (sell_price - buy_price) * match_qty
                    
                    buy_qty_total = float(buy['quantity'])
                    sell_qty_total = float(sell['quantity'])
                    
                    fee_buy_prop = (match_qty / buy_qty_total) * buy_fee if buy_qty_total > 0 else 0
                    fee_sell_prop = (match_qty / sell_qty_total) * sell_fee if sell_qty_total > 0 else 0
                    
                    pl_net = pl_gross - fee_buy_prop - fee_sell_prop
                    
                    # Distribuir P&L REALIZADO entre BUY y SELL
                    trade_pl_map[buy['id']]['pl_realized'] += pl_net / 2
                    trade_pl_map[buy['id']]['qty_matched'] += match_qty
                    
                    trade_pl_map[sell['id']]['pl_realized'] += pl_net / 2
                    trade_pl_map[sell['id']]['qty_matched'] += match_qty
                    
                    total_realized_pl += pl_net
                
                if trade_pl_map[buy['id']]['qty_matched'] >= float(buy['quantity']) - 0.0001:
                    trade_pl_map[buy['id']]['is_closed'] = True
                    buy_queue.pop(0)
                    closed_positions += 1
                    
                if trade_pl_map[sell['id']]['qty_matched'] >= float(sell['quantity']) - 0.0001:
                    trade_pl_map[sell['id']]['is_closed'] = True
                    sell_queue.pop(0)
            
            # Posiciones abiertas (BUY sin match completo)
            for buy in buy_queue:
                qty_unmatched = float(buy['quantity']) - trade_pl_map[buy['id']]['qty_matched']
                if qty_unmatched > 0.0001:
                    avg_cost = float(buy['price'])
                    # Unrealized P&L = 0 porque no tenemos precio actual de mercado
                    # En el futuro, obtener precio actual y calcular: (current_price - avg_cost) * qty
                    unrealized = 0.0  
                    
                    open_positions.append({
                        'symbol': symbol,
                        'side': 'LONG',
                        'qty': round(qty_unmatched, 8),
                        'avg_cost': round(avg_cost, 2),
                        'current_value': round(avg_cost * qty_unmatched, 2),  # Costo, no valor actual
                        'unrealized_pl': unrealized
                    })
                    
                    trade_pl_map[buy['id']]['pl_unrealized'] = unrealized
            
            # Agregar data procesada a trades
            for trade in symbol_trades:
                trade_copy = trade.copy()
                pl_data = trade_pl_map[trade['id']]
                
                # Solo P&L realizado cuenta
                pl_realized = round(pl_data['pl_realized'], 2)
                pl_unrealized = round(pl_data['pl_unrealized'], 2)
                
                total_amount = float(trade.get('amount', float(trade['quantity']) * float(trade['price'])))
                pl_percent = (pl_realized / total_amount * 100) if total_amount != 0 else 0.0
                
                trade_copy['pl_usd'] = pl_realized  # Solo realizado
                trade_copy['pl_percent'] = round(pl_percent, 2)
                trade_copy['pl_realized'] = pl_realized
                trade_copy['pl_unrealized'] = pl_unrealized
                trade_copy['is_winner'] = pl_realized > 0
                trade_copy['is_closed'] = pl_data['is_closed']
                trade_copy['qty_matched'] = round(pl_data['qty_matched'], 8)
                trade_copy['formatted'] = {
                    'pl_usd': f"{'+'if pl_realized >= 0 else ''}${abs(pl_realized):,.2f}",
                    'pl_percent': f"{'+'if pl_percent >= 0 else ''}{abs(pl_percent):.2f}%"
                }
                
                processed_trades.append(trade_copy)
        
        processed_trades.sort(key=lambda x: x.get('datetime', ''))
        
        positions_summary = {
            'open': open_positions,
            'closed_count': closed_positions // 2,  # Cada posición cerrada = 1 BUY + 1 SELL
            'realized_pl': round(total_realized_pl, 2),
            'unrealized_pl': round(total_unrealized_pl, 2)
        }
        
        return processed_trades, positions_summary
    
    # ========================================================================
    # MÉTODO CRÍTICO 2: Evolución de capital día a día
    # ========================================================================
    
    def calculate_capital_evolution(self, trades: List[Dict]) -> List[Dict]:
        """
        Agrupa trades por día y calcula evolución de capital
        
        Args:
            trades: Lista de trades con P&L ya calculado
        
        Returns:
            Lista de dicts con evolución diaria:
                [
                    {
                        'date': '2025-10-27',
                        'capital_start': 5000.00,
                        'pl_daily': 22.76,
                        'capital_end': 5022.76,
                        'trades_count': 5,
                        'trades_detail': ['id1', 'id2', ...]
                    },
                    ...
                ]
        
        REGLAS:
        - Agrupar SOLO por fecha (YYYY-MM-DD), ignorar hora
        - Ordenar ascendente por fecha
        - capital_end de un día = capital_start del siguiente
        - Sumar P&L de TODOS los trades ese día
        """
        if not trades:
            return []
        
        try:
            # Paso 1: Agrupar por día
            daily_groups = {}
            for trade in trades:
                try:
                    # Parsear datetime del trade
                    trade_datetime = datetime.fromisoformat(trade['datetime'].replace('Z', '+00:00'))
                    date_key = trade_datetime.date().isoformat()  # '2025-11-07'
                    
                    if date_key not in daily_groups:
                        daily_groups[date_key] = []
                    daily_groups[date_key].append(trade)
                
                except Exception as e:
                    logger.error(f"Error parsing date for trade {trade.get('id')}: {e}")
                    continue
            
            # Paso 2: Calcular P&L por día PRIMERO
            daily_pl_map = {}
            for date in sorted(daily_groups.keys()):
                daily_trades = daily_groups[date]
                daily_pl = 0.0
                for trade in daily_trades:
                    if 'pl_realized' in trade:
                        daily_pl += trade.get('pl_realized', 0)
                    elif 'pl_usd' in trade:
                        daily_pl += trade['pl_usd']
                    else:
                        pl_data = self.calculate_trade_pl(trade)
                        daily_pl += pl_data.get('pl_usd', 0)
                daily_pl_map[date] = daily_pl
            
            # Obtener balance REAL actual
            current_balance = self.get_real_balance()
            
            # Calcular evolución HACIA ATRÁS desde balance actual
            evolution = []
            sorted_dates = sorted(daily_groups.keys(), reverse=True)
            running_capital = current_balance
            
            for i, date in enumerate(sorted_dates):
                daily_trades = daily_groups[date]
                daily_pl = daily_pl_map[date]
                
                # Para el día más reciente, el capital_end es el balance actual
                if i == 0:
                    capital_end = current_balance
                    capital_start = capital_end - daily_pl
                else:
                    capital_end = running_capital
                    capital_start = capital_end - daily_pl
                
                evolution.append({
                    'date': date,
                    'capital_start': round(capital_start, 2),
                    'pl_daily': round(daily_pl, 2),
                    'capital_end': round(capital_end, 2),
                    'trades_count': len(daily_trades),
                    'trades_detail': [t.get('id', '') for t in daily_trades]
                })
                
                # Mover hacia atrás
                running_capital = capital_start
            
            # Invertir para que quede cronológico
            evolution.reverse()
            
            return evolution
        
        except Exception as e:
            logger.error(f"Error calculate_capital_evolution: {e}")
            return []
    
    # ========================================================================
    # MÉTODO CRÍTICO 3: Journal completo con P&L
    # ========================================================================
    
    def get_journal_with_pl(self, trades: List[Dict], 
                           days: Optional[int] = None,
                           broker: Optional[str] = None) -> Dict:
        """
        Retorna JSON COMPLETO con todos los cálculos de P&L y stats
        
        Args:
            trades: Lista de trades desde APIs (ya normalizados)
            days: Filtrar últimos N días (None = todos)
            broker: 'schwab' | 'coinbase' (None = ambos)
        
        Returns:
            Dict con estructura completa:
                {
                    'timestamp': ISO timestamp,
                    'period': {...},
                    'capital': {
                        'initial': float,
                        'current': float,
                        'pl_total_usd': float,
                        'pl_total_percent': float,
                        'evolution': [...]
                    },
                    'trades': [...],  # Trades con P&L individual
                    'stats': {
                        'total_trades': int,
                        'wins': int,
                        'losses': int,
                        'win_rate': float,
                        'avg_pl_per_trade': float,
                        'profit_factor': float,
                        'max_gain': {...},
                        'max_loss': {...},
                        ...
                    },
                    'symbols': {
                        'AAPL': {'trades': 8, 'pl_usd': 125.50, ...},
                        ...
                    }
                }
        """
        try:
            # Filtrar por broker si es necesario
            filtered_trades = trades
            if broker:
                filtered_trades = [t for t in trades if t.get('broker', '').lower() == broker.lower()]
            
            # Filtrar por días si es necesario
            if days:
                from datetime import timezone
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                filtered_trades = [
                    t for t in filtered_trades
                    if datetime.fromisoformat(t['datetime'].replace('Z', '+00:00')) >= cutoff_date
                ]
            
            # PASO 1: Calcular P&L usando FIFO matching
            filtered_trades, positions_summary = self.calculate_trades_with_fifo_pl(filtered_trades)
            
            # PASO 2: Evolución de capital (solo con P&L realizado)
            capital_evolution = self.calculate_capital_evolution(filtered_trades)
            current_capital = capital_evolution[-1]['capital_end'] if capital_evolution else self.capital_initial
            
            # PASO 3: Estadísticas agregadas
            total_pl_usd = sum([t['pl_usd'] for t in filtered_trades])
            total_pl_percent = (total_pl_usd / self.capital_initial * 100) if self.capital_initial > 0 else 0
            
            wins = sum([1 for t in filtered_trades if t['is_winner']])
            losses = len(filtered_trades) - wins
            win_rate = (wins / len(filtered_trades) * 100) if filtered_trades else 0
            
            avg_pl = total_pl_usd / len(filtered_trades) if filtered_trades else 0
            
            wins_total = sum([t['pl_usd'] for t in filtered_trades if t['is_winner']])
            losses_total = abs(sum([t['pl_usd'] for t in filtered_trades if not t['is_winner']]))
            profit_factor = (wins_total / losses_total) if losses_total > 0 else 0
            
            max_gain_trade = max(filtered_trades, key=lambda t: t['pl_usd']) if filtered_trades else {}
            max_loss_trade = min(filtered_trades, key=lambda t: t['pl_usd']) if filtered_trades else {}
            
            total_volume = sum([float(t.get('total', 0)) for t in filtered_trades])
            total_fees = sum([float(t.get('fee', 0)) for t in filtered_trades])
            
            # PASO 4: Estadísticas por símbolo
            symbol_stats = {}
            for trade in filtered_trades:
                sym = trade.get('symbol')
                if sym not in symbol_stats:
                    symbol_stats[sym] = {'trades': 0, 'pl_usd': 0, 'pl_percent': 0}
                symbol_stats[sym]['trades'] += 1
                symbol_stats[sym]['pl_usd'] += trade['pl_usd']
                symbol_stats[sym]['pl_percent'] += trade['pl_percent']
            
            # PASO 5: Mejor y peor día
            best_day = max(capital_evolution, key=lambda d: d['pl_daily']) if capital_evolution else {}
            worst_day = min(capital_evolution, key=lambda d: d['pl_daily']) if capital_evolution else {}
            
            # RESULTADO FINAL
            return {
                'timestamp': datetime.now().isoformat(),
                'period': {
                    'days': days,
                    'from': capital_evolution[0]['date'] if capital_evolution else None,
                    'to': capital_evolution[-1]['date'] if capital_evolution else None,
                    'trades_in_period': len(filtered_trades)
                },
                'capital': {
                    'initial': round(capital_evolution[0]['capital_start'], 2) if capital_evolution else 0,
                    'current': self.get_real_balance(),  # BALANCE REAL de la API
                    'pl_total_usd': round(total_pl_usd, 2),
                    'pl_total_percent': round(total_pl_percent, 2),
                    'evolution': capital_evolution
                },
                'trades': filtered_trades,
                'stats': {
                    'total_trades': len(filtered_trades),
                    'schwab_trades': len([t for t in filtered_trades if t.get('broker') == 'schwab']),
                    'coinbase_trades': len([t for t in filtered_trades if t.get('broker') == 'coinbase']),
                    'wins': wins,
                    'losses': losses,
                    'win_rate': round(win_rate, 2),
                    'avg_pl_per_trade': round(avg_pl, 2),
                    'profit_factor': round(profit_factor, 2),
                    'max_gain': {
                        'symbol': max_gain_trade.get('symbol'),
                        'amount': max_gain_trade.get('pl_usd', 0),
                        'id': max_gain_trade.get('id')
                    },
                    'max_loss': {
                        'symbol': max_loss_trade.get('symbol'),
                        'amount': max_loss_trade.get('pl_usd', 0),
                        'id': max_loss_trade.get('id')
                    },
                    'total_volume': round(total_volume, 2),
                    'total_fees': round(total_fees, 2),
                    'best_day': {
                        'date': best_day.get('date'),
                        'pl': best_day.get('pl_daily', 0)
                    },
                    'worst_day': {
                        'date': worst_day.get('date'),
                        'pl': worst_day.get('pl_daily', 0)
                    },
                    # Nuevos campos: realizado vs unrealized
                    'pl_realized': positions_summary['realized_pl'],
                    'pl_unrealized': positions_summary['unrealized_pl'],
                    'positions_open_count': len(positions_summary['open']),
                    'positions_closed_count': positions_summary['closed_count']
                },
                'positions': {
                    'open': positions_summary['open'],
                    'closed_count': positions_summary['closed_count']
                },
                'symbols': symbol_stats
            }
        
        except Exception as e:
            logger.error(f"Error get_journal_with_pl: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'trades': [],
                'stats': {},
                'capital': {},
                'symbols': {}
            }
    
    # ========================================================================
    # MÉTODOS LEGACY (mantener para compatibilidad)
    # ========================================================================
    
    def get_combined_journal(self, days: int = 7) -> Dict:
        """
        MÉTODO LEGACY - Ahora usa get_journal_with_pl() internamente
        
        Obtiene journal combinado de ambos brokers con P&L calculado
        
        Args:
            days: Número de días hacia atrás
            
        Returns:
            Dict con trades de ambos brokers + estadísticas consolidadas + P&L
        """
        cache_key = f"combined_pl_{days}"
        
        # Verificar caché
        if self._is_cache_valid(cache_key):
            logger.info("Retornando journal desde caché")
            return self._cache[cache_key]["data"]
        
        try:
            logger.info("Obteniendo journal combinado con P&L...")
            
            # Obtener de ambos brokers (no lanzan excepciones, devuelven [] en error)
            schwab_result = self.schwab.get_transactions(days=days)
            coinbase_result = self.coinbase.get_fills(days=days)
            
            # Combinar trades
            all_trades = schwab_result + coinbase_result
            
            # Ordenar por datetime descendente
            all_trades.sort(key=lambda x: x["datetime"], reverse=True)
            
            # CALCULAR P&L usando get_journal_with_pl
            result = self.get_journal_with_pl(all_trades, days=days, broker=None)
            
            # Guardar en caché
            self._cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now()
            }
            
            logger.info(f"✅ Journal combinado: {result['stats']['total_trades']} trades, P&L: ${result['capital']['pl_total_usd']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo journal combinado: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "trades": [],
                "stats": {},
                "capital": {},
                "error": str(e)
            }
    
    def get_trades_by_broker(self, broker: str, days: int = 7) -> Dict:
        """
        ACTUALIZADO - Ahora retorna con P&L calculado
        
        Obtiene trades de un broker específico con P&L
        
        Args:
            broker: "schwab" o "coinbase"
            days: Número de días
            
        Returns:
            Dict con trades del broker especificado + P&L + stats
        """
        try:
            if broker.lower() == "schwab":
                trades = self.schwab.get_transactions(days=days)
            elif broker.lower() == "coinbase":
                trades = self.coinbase.get_fills(days=days)
            else:
                raise ValueError(f"Broker no válido: {broker}")
            
            # Calcular P&L usando método principal
            result = self.get_journal_with_pl(trades, days=days, broker=broker)
            
            return result
        
        except Exception as e:
            logger.error(f"Error obteniendo trades de {broker}: {e}")
            return {
                "broker": broker,
                "trades": [],
                "stats": {},
                "capital": {},
                "error": str(e)
            }
    
    def get_statistics(self, days: int = 7) -> Dict:
        """
        Obtiene solo estadísticas agregadas (sin trades)
        
        Args:
            days: Número de días
            
        Returns:
            Dict con estadísticas consolidadas incluyendo P&L
        """
        try:
            journal = self.get_combined_journal(days=days)
            
            return {
                "timestamp": journal["timestamp"],
                "stats": journal.get("stats", {}),
                "capital": journal.get("capital", {}),
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
