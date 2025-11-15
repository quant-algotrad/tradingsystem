"""
Utilities Module
Common utilities and helper functions

Includes:
- Logging system
- Performance tracking
- Helper decorators
"""

from .logger import (
    TradingLogger,
    get_trading_logger,
    get_logger,
    log_trade,
    log_signal,
    log_performance,
    log_method,
    PERFORMANCE,
    TRADE
)

__all__ = [
    'TradingLogger',
    'get_trading_logger',
    'get_logger',
    'log_trade',
    'log_signal',
    'log_performance',
    'log_method',
    'PERFORMANCE',
    'TRADE',
]

__version__ = '1.0.0'
