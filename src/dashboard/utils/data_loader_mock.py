"""
Data Loader Utilities
Load data from Redis, TimescaleDB, and Kafka for dashboard
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

# ========================================
# Quick Stats (Sidebar)
# ========================================

def get_quick_stats() -> Dict[str, Any]:
    """Get quick stats for sidebar"""
    try:
        # For now, return mock data
        # TODO: Replace with actual data from Redis/Database
        return {
            'portfolio_value': 52450,
            'portfolio_change': 4.9,
            'daily_pnl': 1200,
            'daily_pnl_pct': 2.4,
            'open_positions': 4
        }
    except Exception as e:
        logger.error(f"Error getting quick stats: {e}")
        return {
            'portfolio_value': 50000,
            'portfolio_change': 0,
            'daily_pnl': 0,
            'daily_pnl_pct': 0,
            'open_positions': 0
        }


def get_system_status() -> Dict[str, Any]:
    """Get system status for sidebar"""
    try:
        from datetime import datetime

        # Check if market is open (9:15 AM to 3:30 PM IST)
        now = datetime.now()
        market_open_time = now.replace(hour=9, minute=15, second=0)
        market_close_time = now.replace(hour=15, minute=30, second=0)

        market_status = 'OPEN' if market_open_time <= now <= market_close_time else 'CLOSED'

        # Check service status (mock for now)
        # TODO: Actually check Docker containers status
        services = {
            'Kafka': 'running',
            'Redis': 'running',
            'TimescaleDB': 'running',
            'Data Fetcher': 'running',
            'Signal Processor': 'running'
        }

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
# Overview Metrics (Home Page)
# ========================================

def get_overview_metrics() -> Dict[str, Any]:
    """Get overview metrics for home page KPI cards"""
    try:
        # Mock data for now
        # TODO: Calculate from actual trades in database
        return {
            'portfolio_value': 52450,
            'portfolio_gain': 2450,
            'portfolio_gain_pct': 4.9,
            'daily_pnl': 1200,
            'daily_pnl_pct': 2.4,
            'open_positions': 4,
            'total_trades': 35,
            'win_rate': 68.6,
            'wins': 24,
            'losses': 11
        }
    except Exception as e:
        logger.error(f"Error getting overview metrics: {e}")
        return {}


# ========================================
# Trades Data
# ========================================

def get_recent_trades(limit: int = 5) -> pd.DataFrame:
    """Get recent trades"""
    try:
        # Mock data for now
        # TODO: Query from TimescaleDB
        trades_data = [
            {
                'timestamp': '2024-11-15 14:30:00',
                'symbol': 'RELIANCE.NS',
                'type': 'BUY',
                'entry': 2450.00,
                'exit': 2480.00,
                'qty': 10,
                'pnl': 300.00,
                'pnl_pct': 1.22,
                'duration': '2h 35m',
                'reason': 'Target hit'
            },
            {
                'timestamp': '2024-11-15 13:15:00',
                'symbol': 'TCS.NS',
                'type': 'BUY',
                'entry': 3245.00,
                'exit': 3260.00,
                'qty': 5,
                'pnl': 75.00,
                'pnl_pct': 0.46,
                'duration': '1h 20m',
                'reason': 'Target hit'
            },
            {
                'timestamp': '2024-11-15 11:45:00',
                'symbol': 'HDFC.NS',
                'type': 'BUY',
                'entry': 1678.00,
                'exit': 1665.00,
                'qty': 8,
                'pnl': -104.00,
                'pnl_pct': -0.77,
                'duration': '45m',
                'reason': 'Stop loss hit'
            },
            {
                'timestamp': '2024-11-15 10:20:00',
                'symbol': 'INFY.NS',
                'type': 'BUY',
                'entry': 1450.00,
                'exit': 1465.00,
                'qty': 12,
                'pnl': 180.00,
                'pnl_pct': 1.03,
                'duration': '3h 10m',
                'reason': 'Target hit'
            },
            {
                'timestamp': '2024-11-14 15:00:00',
                'symbol': 'WIPRO.NS',
                'type': 'BUY',
                'entry': 445.00,
                'exit': 451.00,
                'qty': 20,
                'pnl': 120.00,
                'pnl_pct': 1.35,
                'duration': '1 day',
                'reason': 'Target hit'
            }
        ]

        df = pd.DataFrame(trades_data)
        return df.head(limit)

    except Exception as e:
        logger.error(f"Error getting recent trades: {e}")
        return pd.DataFrame()


def get_all_trades(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                   symbol: Optional[str] = None, status: Optional[str] = None) -> pd.DataFrame:
    """Get all trades with filters"""
    try:
        # Get base trades
        df = get_recent_trades(limit=100)  # Get more for filtering

        # Apply filters
        if start_date:
            df = df[pd.to_datetime(df['timestamp']) >= start_date]
        if end_date:
            df = df[pd.to_datetime(df['timestamp']) <= end_date]
        if symbol and symbol != 'All':
            df = df[df['symbol'] == symbol]
        if status and status != 'All':
            # Add status filtering logic
            pass

        return df

    except Exception as e:
        logger.error(f"Error getting all trades: {e}")
        return pd.DataFrame()


# ========================================
# Positions Data
# ========================================

def get_open_positions() -> pd.DataFrame:
    """Get currently open positions"""
    try:
        # Mock data
        positions_data = [
            {
                'symbol': 'RELIANCE.NS',
                'entry_price': 2450.00,
                'current_price': 2480.50,
                'qty': 9,
                'entry_value': 22050.00,
                'current_value': 22324.50,
                'pnl': 274.50,
                'pnl_pct': 1.24,
                'stop_loss': 2400.00,
                'target': 2550.00,
                'sl_distance_pct': -3.2,
                'target_distance_pct': 2.8,
                'risk_reward': 2.0,
                'entry_time': '2024-11-15 13:30:00',
                'duration': '1h 30m'
            },
            {
                'symbol': 'TCS.NS',
                'entry_price': 3245.00,
                'current_price': 3238.00,
                'qty': 4,
                'entry_value': 12980.00,
                'current_value': 12952.00,
                'pnl': -28.00,
                'pnl_pct': -0.22,
                'stop_loss': 3210.00,
                'target': 3310.00,
                'sl_distance_pct': -0.86,
                'target_distance_pct': 2.22,
                'risk_reward': 1.86,
                'entry_time': '2024-11-15 14:15:00',
                'duration': '45m'
            },
            {
                'symbol': 'ICICIBANK.NS',
                'entry_price': 945.00,
                'current_price': 952.00,
                'qty': 15,
                'entry_value': 14175.00,
                'current_value': 14280.00,
                'pnl': 105.00,
                'pnl_pct': 0.74,
                'stop_loss': 925.00,
                'target': 975.00,
                'sl_distance_pct': -2.8,
                'target_distance_pct': 2.4,
                'risk_reward': 1.5,
                'entry_time': '2024-11-15 10:00:00',
                'duration': '5h'
            },
            {
                'symbol': 'HINDUNILVR.NS',
                'entry_price': 2310.00,
                'current_price': 2305.00,
                'qty': 6,
                'entry_value': 13860.00,
                'current_value': 13830.00,
                'pnl': -30.00,
                'pnl_pct': -0.22,
                'stop_loss': 2270.00,
                'target': 2380.00,
                'sl_distance_pct': -1.5,
                'target_distance_pct': 3.3,
                'risk_reward': 1.75,
                'entry_time': '2024-11-15 09:30:00',
                'duration': '5h 30m'
            }
        ]

        return pd.DataFrame(positions_data)

    except Exception as e:
        logger.error(f"Error getting open positions: {e}")
        return pd.DataFrame()


# ========================================
# Signals Data
# ========================================

def get_recent_signals(limit: int = 5) -> pd.DataFrame:
    """Get recent trading signals"""
    try:
        signals_data = [
            {
                'timestamp': '2024-11-15 15:00:00',
                'symbol': 'SBIN.NS',
                'signal': 'BUY',
                'confidence': 72.5,
                'strength': 'MEDIUM',
                'price': 598.50,
                'bullish': 4,
                'bearish': 1,
                'neutral': 1,
                'reason': 'RSI oversold, MACD bullish crossover'
            },
            {
                'timestamp': '2024-11-15 14:45:00',
                'symbol': 'AXISBANK.NS',
                'signal': 'SELL',
                'confidence': 68.0,
                'strength': 'WEAK',
                'price': 1025.00,
                'bullish': 1,
                'bearish': 3,
                'neutral': 2,
                'reason': 'RSI overbought, price at upper Bollinger Band'
            },
            {
                'timestamp': '2024-11-15 14:30:00',
                'symbol': 'MARUTI.NS',
                'signal': 'BUY',
                'confidence': 78.3,
                'strength': 'STRONG',
                'price': 9875.00,
                'bullish': 5,
                'bearish': 0,
                'neutral': 1,
                'reason': 'Strong uptrend, all indicators bullish'
            }
        ]

        df = pd.DataFrame(signals_data)
        return df.head(limit)

    except Exception as e:
        logger.error(f"Error getting recent signals: {e}")
        return pd.DataFrame()


# ========================================
# Market Data
# ========================================

def get_ohlcv_data(symbol: str, timeframe: str = '1d', days: int = 30) -> pd.DataFrame:
    """Get OHLCV data for charting"""
    try:
        # For now, generate mock data
        # TODO: Fetch from TimescaleDB or yfinance
        import numpy as np

        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        # Generate random walk price data
        base_price = 2450.00
        returns = np.random.randn(days) * 20  # Random daily changes
        prices = base_price + np.cumsum(returns)

        data = {
            'timestamp': dates,
            'open': prices + np.random.randn(days) * 5,
            'high': prices + np.random.uniform(5, 20, days),
            'low': prices - np.random.uniform(5, 20, days),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, days)
        }

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    except Exception as e:
        logger.error(f"Error getting OHLCV data: {e}")
        return pd.DataFrame()


def get_live_price(symbol: str) -> float:
    """Get live price for a symbol"""
    try:
        cache = get_cache()
        quote = cache.get_quote(symbol)

        if quote:
            return quote.get('last_price', 0.0)

        # Fallback to mock price
        return 2450.50

    except Exception as e:
        logger.error(f"Error getting live price: {e}")
        return 0.0


# ========================================
# Indicators Data
# ========================================

def get_indicator_values(symbol: str, timeframe: str = '1d') -> Dict[str, Any]:
    """Get current indicator values for a symbol"""
    try:
        # Mock data
        return {
            'RSI': {
                'value': 45.2,
                'signal': 'NEUTRAL',
                'description': 'Neither overbought nor oversold'
            },
            'MACD': {
                'macd': 12.5,
                'signal': 10.2,
                'histogram': 2.3,
                'signal_type': 'BUY',
                'description': 'Bullish crossover detected'
            },
            'BB': {
                'upper': 2510.00,
                'middle': 2450.00,
                'lower': 2390.00,
                'current': 2448.00,
                'signal': 'BUY',
                'description': 'Price near lower band'
            },
            'ADX': {
                'value': 28.5,
                'signal': 'STRONG_TREND',
                'description': 'Strong uptrend in progress'
            },
            'STOCH': {
                'k': 35.2,
                'signal': 'NEUTRAL',
                'description': 'Neutral zone'
            },
            'ATR': {
                'value': 42.50,
                'signal': 'MODERATE',
                'description': 'Moderate volatility'
            }
        }

    except Exception as e:
        logger.error(f"Error getting indicator values: {e}")
        return {}


# ========================================
# Risk & Performance Metrics
# ========================================

def get_risk_metrics() -> Dict[str, Any]:
    """Get risk metrics"""
    try:
        return {
            'portfolio_risk': {
                'current': 30000,
                'max': 50000,
                'usage_pct': 60.0
            },
            'daily_loss': {
                'current': -450,
                'max': -2500,
                'usage_pct': 18.0
            },
            'max_drawdown': {
                'current': 1250,
                'current_pct': 2.5,
                'max': 5000,
                'max_pct': 10.0
            },
            'var_95': 1200,  # Value at Risk
            'sharpe_ratio': 1.85,
            'risk_reward_avg': 2.1
        }

    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        return {}


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics"""
    try:
        return {
            'total_trades': 35,
            'winning_trades': 24,
            'losing_trades': 11,
            'win_rate': 68.6,
            'avg_win': 450.00,
            'avg_loss': -180.00,
            'profit_factor': 2.5,
            'largest_win': 850.00,
            'largest_loss': -320.00,
            'avg_hold_time': '2h 15m',
            'total_pnl': 8450.00,
            'total_pnl_pct': 16.9,
            'sharpe_ratio': 1.85,
            'sortino_ratio': 2.45,
            'max_drawdown': 1250.00,
            'max_drawdown_pct': 2.5,
            'recovery_time': '3 days'
        }

    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return {}


# ========================================
# System Events & Logs
# ========================================

def get_recent_events(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent system events"""
    try:
        events = [
            {
                'timestamp': '2024-11-15 15:05:00',
                'level': 'INFO',
                'message': 'Trade executed: BUY RELIANCE @ ₹2480.50'
            },
            {
                'timestamp': '2024-11-15 15:00:00',
                'level': 'INFO',
                'message': 'Signal generated: BUY SBIN (Confidence: 72.5%)'
            },
            {
                'timestamp': '2024-11-15 14:55:00',
                'level': 'WARNING',
                'message': 'Position limit approaching for RELIANCE (98%)'
            },
            {
                'timestamp': '2024-11-15 14:30:00',
                'level': 'INFO',
                'message': 'Target hit: RELIANCE position closed with profit ₹300'
            },
            {
                'timestamp': '2024-11-15 14:00:00',
                'level': 'ERROR',
                'message': 'Failed to fetch data for AXISBANK (retry in 30s)'
            }
        ]

        return events[:limit]

    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        return []


# ========================================
# Portfolio & Equity Curve
# ========================================

def get_equity_curve(days: int = 30) -> pd.DataFrame:
    """Get equity curve (portfolio value over time)"""
    try:
        import numpy as np

        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        base_value = 50000
        daily_returns = np.random.randn(days) * 200  # Random daily P&L
        portfolio_values = base_value + np.cumsum(daily_returns)

        df = pd.DataFrame({
            'date': dates,
            'portfolio_value': portfolio_values,
            'daily_pnl': daily_returns,
            'cumulative_pnl': np.cumsum(daily_returns)
        })

        return df

    except Exception as e:
        logger.error(f"Error getting equity curve: {e}")
        return pd.DataFrame()


# ========================================
# Symbols & Watchlist
# ========================================

def get_available_symbols() -> List[str]:
    """Get list of available symbols"""
    return [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS',
        'ICICIBANK.NS', 'KOTAKBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS',
        'LT.NS', 'ASIANPAINT.NS', 'AXISBANK.NS', 'MARUTI.NS', 'SUNPHARMA.NS'
    ]
