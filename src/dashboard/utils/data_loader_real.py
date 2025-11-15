"""
Real Data Loader - Connect to actual database/cache
Replaces mock data with real TimescaleDB and Redis queries
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.cache import get_cache
from src.utils import get_logger

logger = get_logger(__name__)

# Database connection
def get_db_connection():
    """Get TimescaleDB connection"""
    try:
        import psycopg2
        import os

        conn = psycopg2.connect(
            host=os.getenv('TIMESCALE_HOST', 'localhost'),
            port=int(os.getenv('TIMESCALE_PORT', '5432')),
            database=os.getenv('TIMESCALE_DB', 'trading_data'),
            user=os.getenv('TIMESCALE_USER', 'trading'),
            password=os.getenv('TIMESCALE_PASSWORD', 'trading123')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


# ========================================
# Quick Stats (Sidebar)
# ========================================

def get_quick_stats() -> Dict[str, Any]:
    """Get quick stats from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return _get_fallback_stats()

        cursor = conn.cursor()

        # Get portfolio value (sum of current positions + cash)
        cursor.execute("""
            SELECT COALESCE(SUM(quantity * current_price), 0) as position_value
            FROM positions
            WHERE status = 'OPEN'
        """)
        position_value = cursor.fetchone()[0] or 0

        # Get cash balance
        cursor.execute("SELECT balance FROM portfolio LIMIT 1")
        cash_balance = cursor.fetchone()
        cash_balance = cash_balance[0] if cash_balance else 50000

        portfolio_value = position_value + cash_balance

        # Get initial capital for change calculation
        initial_capital = 50000  # Could be stored in config
        portfolio_change = ((portfolio_value - initial_capital) / initial_capital) * 100

        # Get today's P&L
        today = datetime.now().date()
        cursor.execute("""
            SELECT COALESCE(SUM(pnl), 0)
            FROM trades
            WHERE DATE(exit_time) = %s
        """, (today,))
        daily_pnl = cursor.fetchone()[0] or 0
        daily_pnl_pct = (daily_pnl / portfolio_value) * 100 if portfolio_value > 0 else 0

        # Get open positions count
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
        open_positions = cursor.fetchone()[0] or 0

        cursor.close()
        conn.close()

        return {
            'portfolio_value': portfolio_value,
            'portfolio_change': portfolio_change,
            'daily_pnl': daily_pnl,
            'daily_pnl_pct': daily_pnl_pct,
            'open_positions': open_positions
        }

    except Exception as e:
        logger.error(f"Error getting quick stats: {e}")
        return _get_fallback_stats()


def _get_fallback_stats():
    """Fallback stats if database unavailable"""
    return {
        'portfolio_value': 50000,
        'portfolio_change': 0,
        'daily_pnl': 0,
        'daily_pnl_pct': 0,
        'open_positions': 0
    }


def get_system_status() -> Dict[str, Any]:
    """Get real system status"""
    try:
        from datetime import datetime
        import subprocess

        # Check if market is open (9:15 AM to 3:30 PM IST)
        now = datetime.now()
        market_open_time = now.replace(hour=9, minute=15, second=0)
        market_close_time = now.replace(hour=15, minute=30, second=0)
        market_status = 'OPEN' if market_open_time <= now <= market_close_time else 'CLOSED'

        # Check actual service status
        services = {}

        # Check Kafka
        try:
            from kafka import KafkaConsumer
            consumer = KafkaConsumer(bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'))
            consumer.close()
            services['Kafka'] = 'running'
        except:
            services['Kafka'] = 'stopped'

        # Check Redis
        try:
            cache = get_cache()
            if cache.is_enabled():
                services['Redis'] = 'running'
            else:
                services['Redis'] = 'stopped'
        except:
            services['Redis'] = 'stopped'

        # Check TimescaleDB
        try:
            conn = get_db_connection()
            if conn:
                conn.close()
                services['TimescaleDB'] = 'running'
            else:
                services['TimescaleDB'] = 'stopped'
        except:
            services['TimescaleDB'] = 'stopped'

        # Check workers (via Docker if running in container)
        try:
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'],
                                  capture_output=True, text=True, timeout=2)
            containers = result.stdout.split('\n')

            services['Data Fetcher'] = 'running' if any('ingestion' in c for c in containers) else 'stopped'
            services['Signal Processor'] = 'running' if any('processor' in c for c in containers) else 'stopped'
        except:
            services['Data Fetcher'] = 'unknown'
            services['Signal Processor'] = 'unknown'

        return {
            'market_status': market_status,
            'services': services
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            'market_status': 'UNKNOWN',
            'services': {}
        }


# ========================================
# Overview Metrics
# ========================================

def get_overview_metrics() -> Dict[str, Any]:
    """Get overview metrics from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return _get_fallback_stats()

        cursor = conn.cursor()

        # Portfolio metrics (same as quick stats)
        quick_stats = get_quick_stats()

        # Get all-time trade statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losses,
                COALESCE(SUM(pnl), 0) as total_pnl
            FROM trades
            WHERE exit_time IS NOT NULL
        """)

        row = cursor.fetchone()
        total_trades = row[0] or 0
        wins = row[1] or 0
        losses = row[2] or 0

        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        cursor.close()
        conn.close()

        return {
            **quick_stats,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'wins': wins,
            'losses': losses
        }

    except Exception as e:
        logger.error(f"Error getting overview metrics: {e}")
        return _get_fallback_stats()


# ========================================
# Trades Data (REAL)
# ========================================

def get_recent_trades(limit: int = 5) -> pd.DataFrame:
    """Get recent trades from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        query = """
            SELECT
                exit_time as timestamp,
                symbol,
                position_type as type,
                entry_price as entry,
                exit_price as exit,
                quantity as qty,
                pnl,
                (pnl / (entry_price * quantity) * 100) as pnl_pct,
                EXTRACT(EPOCH FROM (exit_time - entry_time))/3600 as duration_hours,
                exit_reason as reason
            FROM trades
            WHERE exit_time IS NOT NULL
            ORDER BY exit_time DESC
            LIMIT %s
        """

        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()

        # Format duration
        if len(df) > 0:
            df['duration'] = df['duration_hours'].apply(lambda h:
                f"{int(h)}h {int((h % 1) * 60)}m" if h < 24 else f"{int(h/24)} days"
            )
            df = df.drop('duration_hours', axis=1)

        return df

    except Exception as e:
        logger.error(f"Error getting recent trades: {e}")
        return pd.DataFrame()


def get_all_trades(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                   symbol: Optional[str] = None, status: Optional[str] = None) -> pd.DataFrame:
    """Get all trades with filters"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        conditions = ["exit_time IS NOT NULL"]
        params = []

        if start_date:
            conditions.append("exit_time >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("exit_time <= %s")
            params.append(end_date)

        if symbol and symbol != 'All':
            conditions.append("symbol = %s")
            params.append(symbol)

        if status and status != 'All':
            if status == 'Profit':
                conditions.append("pnl > 0")
            elif status == 'Loss':
                conditions.append("pnl < 0")
            elif status == 'Breakeven':
                conditions.append("pnl = 0")

        where_clause = " AND ".join(conditions)

        query = f"""
            SELECT
                exit_time as timestamp,
                symbol,
                position_type as type,
                entry_price as entry,
                exit_price as exit,
                quantity as qty,
                pnl,
                (pnl / (entry_price * quantity) * 100) as pnl_pct,
                EXTRACT(EPOCH FROM (exit_time - entry_time))/3600 as duration_hours,
                exit_reason as reason
            FROM trades
            WHERE {where_clause}
            ORDER BY exit_time DESC
        """

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        # Format duration
        if len(df) > 0:
            df['duration'] = df['duration_hours'].apply(lambda h:
                f"{int(h)}h {int((h % 1) * 60)}m" if h < 24 else f"{int(h/24)} days"
            )
            df = df.drop('duration_hours', axis=1)

        return df

    except Exception as e:
        logger.error(f"Error getting all trades: {e}")
        return pd.DataFrame()


# ========================================
# Positions Data (REAL)
# ========================================

def get_open_positions() -> pd.DataFrame:
    """Get currently open positions from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        # Get positions with current prices from Redis cache
        query = """
            SELECT
                symbol,
                entry_price,
                quantity,
                stop_loss,
                target_price as target,
                entry_time,
                EXTRACT(EPOCH FROM (NOW() - entry_time))/3600 as duration_hours
            FROM positions
            WHERE status = 'OPEN'
            ORDER BY entry_time DESC
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        if len(df) == 0:
            return df

        # Get current prices from Redis cache
        cache = get_cache()

        for idx, row in df.iterrows():
            symbol = row['symbol']

            # Try to get live price from cache
            if cache.is_enabled():
                quote = cache.get_quote(symbol)
                current_price = quote.get('last_price', row['entry_price']) if quote else row['entry_price']
            else:
                current_price = row['entry_price']  # Fallback

            # Calculate metrics
            qty = row['quantity']
            entry_value = row['entry_price'] * qty
            current_value = current_price * qty
            pnl = current_value - entry_value
            pnl_pct = (pnl / entry_value) * 100

            # Stop loss and target distances
            sl_distance_pct = ((row['stop_loss'] - current_price) / current_price) * 100
            target_distance_pct = ((row['target'] - current_price) / current_price) * 100

            # Risk-reward
            risk = abs(row['entry_price'] - row['stop_loss'])
            reward = abs(row['target'] - row['entry_price'])
            risk_reward = reward / risk if risk > 0 else 0

            # Duration
            hours = row['duration_hours']
            duration = f"{int(hours)}h {int((hours % 1) * 60)}m" if hours < 24 else f"{int(hours/24)} days"

            # Update dataframe
            df.at[idx, 'current_price'] = current_price
            df.at[idx, 'entry_value'] = entry_value
            df.at[idx, 'current_value'] = current_value
            df.at[idx, 'pnl'] = pnl
            df.at[idx, 'pnl_pct'] = pnl_pct
            df.at[idx, 'sl_distance_pct'] = sl_distance_pct
            df.at[idx, 'target_distance_pct'] = target_distance_pct
            df.at[idx, 'risk_reward'] = risk_reward
            df.at[idx, 'duration'] = duration

        df = df.drop('duration_hours', axis=1)

        return df

    except Exception as e:
        logger.error(f"Error getting open positions: {e}")
        return pd.DataFrame()


# ========================================
# Signals Data (REAL)
# ========================================

def get_recent_signals(limit: int = 5) -> pd.DataFrame:
    """Get recent trading signals from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        query = """
            SELECT
                timestamp,
                symbol,
                signal_type as signal,
                confidence,
                strength,
                current_price as price,
                bullish_indicators as bullish,
                bearish_indicators as bearish,
                neutral_indicators as neutral,
                reasons as reason
            FROM signals
            ORDER BY timestamp DESC
            LIMIT %s
        """

        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()

        return df

    except Exception as e:
        logger.error(f"Error getting recent signals: {e}")
        return pd.DataFrame()


# ========================================
# Market Data (REAL)
# ========================================

def get_ohlcv_data(symbol: str, timeframe: str = '1d', days: int = 30) -> pd.DataFrame:
    """Get OHLCV data from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = """
            SELECT
                time as timestamp,
                open,
                high,
                low,
                close,
                volume
            FROM market_data_ohlcv
            WHERE symbol = %s
            AND timeframe = %s
            AND time >= %s
            AND time <= %s
            ORDER BY time ASC
        """

        df = pd.read_sql_query(query, conn, params=(symbol, timeframe, start_date, end_date))
        conn.close()

        return df

    except Exception as e:
        logger.error(f"Error getting OHLCV data: {e}")
        return pd.DataFrame()


def get_live_price(symbol: str) -> float:
    """Get live price from Redis cache"""
    try:
        cache = get_cache()
        if cache.is_enabled():
            quote = cache.get_quote(symbol)
            if quote:
                return quote.get('last_price', 0.0)

        # Fallback to database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT close
                FROM market_data_ohlcv
                WHERE symbol = %s
                ORDER BY time DESC
                LIMIT 1
            """, (symbol,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else 0.0

        return 0.0

    except Exception as e:
        logger.error(f"Error getting live price: {e}")
        return 0.0


# ========================================
# Performance Stats (REAL)
# ========================================

def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return {}

        cursor = conn.cursor()

        # Overall statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) as losing_trades,
                COALESCE(AVG(CASE WHEN pnl > 0 THEN pnl END), 0) as avg_win,
                COALESCE(AVG(CASE WHEN pnl < 0 THEN pnl END), 0) as avg_loss,
                COALESCE(MAX(pnl), 0) as largest_win,
                COALESCE(MIN(pnl), 0) as largest_loss,
                COALESCE(SUM(pnl), 0) as total_pnl,
                COALESCE(AVG(EXTRACT(EPOCH FROM (exit_time - entry_time))/3600), 0) as avg_hold_hours
            FROM trades
            WHERE exit_time IS NOT NULL
        """)

        row = cursor.fetchone()

        total_trades = row[0] or 0
        winning_trades = row[1] or 0
        losing_trades = row[2] or 0
        avg_win = row[3] or 0
        avg_loss = row[4] or 0
        largest_win = row[5] or 0
        largest_loss = row[6] or 0
        total_pnl = row[7] or 0
        avg_hold_hours = row[8] or 0

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0

        # Format average hold time
        if avg_hold_hours < 24:
            avg_hold_time = f"{int(avg_hold_hours)}h {int((avg_hold_hours % 1) * 60)}m"
        else:
            avg_hold_time = f"{int(avg_hold_hours / 24)} days"

        # Calculate P&L percentage
        initial_capital = 50000
        total_pnl_pct = (total_pnl / initial_capital) * 100

        cursor.close()
        conn.close()

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_hold_time': avg_hold_time,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'sharpe_ratio': 0,  # Calculate if needed
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'recovery_time': 'N/A'
        }

    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return {}


# ========================================
# Additional helper functions
# ========================================

def get_available_symbols() -> List[str]:
    """Get list of symbols from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return []

        cursor = cursor.execute("""
            SELECT DISTINCT symbol
            FROM market_data_ohlcv
            ORDER BY symbol
        """)

        symbols = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        return symbols

    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS']  # Fallback


def get_indicator_values(symbol: str, timeframe: str = '1d') -> Dict[str, Any]:
    """Get cached indicator values from Redis"""
    try:
        cache = get_cache()
        if cache.is_enabled():
            key = f"indicators:{symbol}:{timeframe}"
            indicators = cache.get(key)
            if indicators:
                return indicators

        # Return empty if not cached
        return {}

    except Exception as e:
        logger.error(f"Error getting indicator values: {e}")
        return {}


def get_risk_metrics() -> Dict[str, Any]:
    """Get risk metrics from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return {}

        # Get current portfolio value
        stats = get_quick_stats()
        portfolio_value = stats['portfolio_value']

        # Get open positions total exposure
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(quantity * entry_price), 0)
            FROM positions
            WHERE status = 'OPEN'
        """)
        portfolio_risk = cursor.fetchone()[0] or 0

        # Max risk limit (configurable)
        max_portfolio_risk = portfolio_value * 0.5  # 50% max exposure
        risk_usage_pct = (portfolio_risk / max_portfolio_risk * 100) if max_portfolio_risk > 0 else 0

        # Get today's P&L for daily loss tracking
        daily_pnl = stats['daily_pnl']
        max_daily_loss = portfolio_value * 0.05  # 5% max daily loss
        daily_loss_usage = (abs(daily_pnl) / max_daily_loss * 100) if daily_pnl < 0 else 0

        cursor.close()
        conn.close()

        return {
            'portfolio_risk': {
                'current': portfolio_risk,
                'max': max_portfolio_risk,
                'usage_pct': risk_usage_pct
            },
            'daily_loss': {
                'current': daily_pnl,
                'max': -max_daily_loss,
                'usage_pct': daily_loss_usage
            },
            'max_drawdown': {
                'current': 0,  # Calculate if needed
                'current_pct': 0,
                'max': portfolio_value * 0.1,
                'max_pct': 10.0
            },
            'var_95': 0,
            'sharpe_ratio': 0,
            'risk_reward_avg': 2.0
        }

    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        return {}


def get_recent_events(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent system events from logs"""
    try:
        # Read from log files
        import re

        events = []
        log_file = 'logs/trading.log'

        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()[-limit*2:]  # Get more to filter

                for line in lines:
                    # Parse log line
                    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\[(.*?)\](.*)', line)
                    if match:
                        timestamp, level, message = match.groups()
                        events.append({
                            'timestamp': timestamp,
                            'level': level.strip(),
                            'message': message.strip()
                        })

        return events[-limit:]  # Return last N events

    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        return []


def get_equity_curve(days: int = 30) -> pd.DataFrame:
    """Get equity curve from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()

        # Calculate daily portfolio value
        query = """
            WITH daily_pnl AS (
                SELECT
                    DATE(exit_time) as date,
                    SUM(pnl) as daily_pnl
                FROM trades
                WHERE exit_time IS NOT NULL
                AND exit_time >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(exit_time)
                ORDER BY DATE(exit_time)
            )
            SELECT
                date,
                daily_pnl,
                SUM(daily_pnl) OVER (ORDER BY date) as cumulative_pnl
            FROM daily_pnl
        """

        df = pd.read_sql_query(query, conn, params=(days,))
        conn.close()

        # Add portfolio value
        initial_capital = 50000
        df['portfolio_value'] = initial_capital + df['cumulative_pnl']

        return df

    except Exception as e:
        logger.error(f"Error getting equity curve: {e}")
        return pd.DataFrame()
