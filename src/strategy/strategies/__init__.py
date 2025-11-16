"""
Trading Strategies

All concrete trading strategy implementations.

To add a new strategy:
1. Create a new file (e.g., scalping.py)
2. Inherit from TradingStrategy
3. Implement get_name(), get_description(), calculate_trade_levels()
4. Import here and register in strategy_factory.py (auto-registration section)
"""

from .multi_indicator import MultiIndicatorStrategy
from .mean_reversion import MeanReversionStrategy
from .breakout import BreakoutStrategy

__all__ = [
    'MultiIndicatorStrategy',
    'MeanReversionStrategy',
    'BreakoutStrategy',
]
