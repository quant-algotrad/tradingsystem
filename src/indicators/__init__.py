"""
Technical Indicators Module
Provides technical analysis indicators for trading strategies

Design Patterns Used:
- Strategy Pattern: Interchangeable indicator algorithms
- Factory Pattern: Indicator creation
- Template Method: Common calculation flow
- Facade Pattern: Simplified API

Usage:
    from src.indicators import calculate_indicator, calculate_indicators

    # Single indicator
    rsi_result = calculate_indicator('rsi', data)
    print(f"RSI: {rsi_result.get_latest_value()}")

    # Multiple indicators
    results = calculate_indicators(['rsi', 'macd', 'bb'], data, symbol="RELIANCE.NS")
    df = results.to_dataframe()
"""

# Models
from .models import (
    IndicatorValue,
    IndicatorResult,
    MultiIndicatorResult,
    IndicatorSignal,
    IndicatorCategory,
    SignalValue,
    IndicatorParameters,
    MovingAverageParams,
    RSIParams,
    MACDParams,
    BollingerBandsParams,
    ATRParams
)

# Base classes
from .base_indicator import (
    IIndicator,
    BaseIndicator
)

# Trend indicators
from .trend import (
    SMA,
    EMA,
    MACD,
    ADX
)

# Momentum indicators
from .momentum import (
    RSI,
    Stochastic
)

# Volatility indicators
from .volatility import (
    BollingerBands,
    ATR
)

# Calculator and factory
from .indicator_calculator import (
    IndicatorFactory,
    IndicatorCalculator,
    get_indicator_calculator,
    calculate_indicator,
    calculate_indicators
)

__all__ = [
    # Models
    'IndicatorValue',
    'IndicatorResult',
    'MultiIndicatorResult',
    'IndicatorSignal',
    'IndicatorCategory',
    'SignalValue',
    'IndicatorParameters',
    'MovingAverageParams',
    'RSIParams',
    'MACDParams',
    'BollingerBandsParams',
    'ATRParams',

    # Base
    'IIndicator',
    'BaseIndicator',

    # Trend Indicators
    'SMA',
    'EMA',
    'MACD',
    'ADX',

    # Momentum Indicators
    'RSI',
    'Stochastic',

    # Volatility Indicators
    'BollingerBands',
    'ATR',

    # Calculator
    'IndicatorFactory',
    'IndicatorCalculator',
    'get_indicator_calculator',
    'calculate_indicator',
    'calculate_indicators',
]

__version__ = '1.0.0'
