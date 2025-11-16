"""
Position Sizing Strategies
Strategy Pattern implementation for position sizing

Available Strategies:
- FixedRiskSizer: Risk fixed % of capital (most common)
- KellyCriterionSizer: Optimal growth sizing
- VolatilityAdjustedSizer: ATR-based sizing

Pattern: Strategy Pattern
- Easy to switch between sizing methods
- Each strategy optimized for different scenarios
- Consistent interface

Usage:
    from src.strategy.position_sizing import FixedRiskSizer

    sizer = FixedRiskSizer(risk_percent=1.0)
    result = sizer.calculate_position_size(
        capital=50000,
        entry_price=100.0,
        stop_loss=98.0
    )
    print(f"Buy {result.quantity} shares")
"""

from .base_sizer import IPositionSizer, PositionSizeResult
from .fixed_risk_sizer import FixedRiskSizer
from .kelly_sizer import KellyCriterionSizer
from .volatility_sizer import VolatilityAdjustedSizer

__all__ = [
    'IPositionSizer',
    'PositionSizeResult',
    'FixedRiskSizer',
    'KellyCriterionSizer',
    'VolatilityAdjustedSizer',
]

__version__ = '1.0.0'
