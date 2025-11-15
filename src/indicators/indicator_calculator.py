"""
Indicator Calculator
Main facade for calculating multiple indicators

Patterns:
- Facade Pattern: Simplifies indicator calculations
- Factory Pattern: Creates indicators
- Batch optimization: Calculates multiple indicators efficiently
"""

from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

from src.indicators.base_indicator import IIndicator
from src.indicators.models import MultiIndicatorResult, IndicatorResult
from src.indicators.trend_indicators import SMA, EMA, MACD, ADX
from src.indicators.momentum_indicators import RSI, Stochastic
from src.indicators.volatility_indicators import BollingerBands, ATR


# ============================================
# Indicator Factory
# ============================================

class IndicatorFactory:
    """
    Factory for creating indicator instances

    Pattern: Factory Pattern + Registry Pattern
    """

    # Registry of available indicators
    _registry: Dict[str, type] = {
        'sma': SMA,
        'ema': EMA,
        'macd': MACD,
        'adx': ADX,
        'rsi': RSI,
        'stochastic': Stochastic,
        'bollinger_bands': BollingerBands,
        'bb': BollingerBands,  # Alias
        'atr': ATR
    }

    @classmethod
    def create(cls, indicator_name: str, params=None) -> Optional[IIndicator]:
        """
        Create indicator instance

        Args:
            indicator_name: Name of indicator
            params: Indicator parameters

        Returns:
            IIndicator instance or None
        """
        indicator_name_lower = indicator_name.lower()

        if indicator_name_lower not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Indicator '{indicator_name}' not found. "
                f"Available: {available}"
            )

        indicator_class = cls._registry[indicator_name_lower]

        try:
            if params is not None:
                return indicator_class(params)
            else:
                return indicator_class()
        except Exception as e:
            print(f"[ERROR] Failed to create indicator '{indicator_name}': {e}")
            return None

    @classmethod
    def get_available_indicators(cls) -> List[str]:
        """Get list of available indicators"""
        return list(set(cls._registry.keys()))


# ============================================
# Indicator Calculator (Facade)
# ============================================

class IndicatorCalculator:
    """
    Main calculator for technical indicators

    Pattern: Facade Pattern
    - Provides simple interface for complex calculations
    - Handles multiple indicators efficiently
    - Manages batch calculations
    """

    def __init__(self):
        """Initialize calculator"""
        self._indicators: Dict[str, IIndicator] = {}

    def add_indicator(self, name: str, indicator: IIndicator):
        """
        Add indicator to calculator

        Args:
            name: Indicator identifier
            indicator: IIndicator instance
        """
        self._indicators[name] = indicator

    def remove_indicator(self, name: str):
        """Remove indicator from calculator"""
        if name in self._indicators:
            del self._indicators[name]

    def calculate_single(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        params=None
    ) -> IndicatorResult:
        """
        Calculate single indicator

        Args:
            indicator_name: Name of indicator
            data: OHLCV DataFrame
            params: Optional parameters

        Returns:
            IndicatorResult
        """
        # Create indicator
        indicator = IndicatorFactory.create(indicator_name, params)

        if indicator is None:
            raise ValueError(f"Could not create indicator: {indicator_name}")

        # Calculate
        return indicator.calculate(data)

    def calculate_all(
        self,
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        timeframe: str = "1d"
    ) -> MultiIndicatorResult:
        """
        Calculate all registered indicators

        Args:
            data: OHLCV DataFrame
            symbol: Stock symbol
            timeframe: Timeframe

        Returns:
            MultiIndicatorResult with all calculations
        """
        start_time = datetime.now()

        result = MultiIndicatorResult(
            symbol=symbol,
            timeframe=timeframe
        )

        # Calculate each indicator
        for name, indicator in self._indicators.items():
            try:
                ind_result = indicator.calculate(data)
                result.add_indicator(ind_result)
            except Exception as e:
                print(f"[ERROR] Failed to calculate {name}: {e}")

        # Record calculation time
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        result.calculation_time_ms = duration_ms

        return result

    def calculate_batch(
        self,
        indicator_names: List[str],
        data: pd.DataFrame,
        symbol: str = "UNKNOWN",
        timeframe: str = "1d"
    ) -> MultiIndicatorResult:
        """
        Calculate multiple indicators efficiently

        Args:
            indicator_names: List of indicator names
            data: OHLCV DataFrame
            symbol: Stock symbol
            timeframe: Timeframe

        Returns:
            MultiIndicatorResult
        """
        start_time = datetime.now()

        result = MultiIndicatorResult(
            symbol=symbol,
            timeframe=timeframe
        )

        # Create and calculate each indicator
        for ind_name in indicator_names:
            try:
                indicator = IndicatorFactory.create(ind_name)
                if indicator:
                    ind_result = indicator.calculate(data)
                    result.add_indicator(ind_result)
            except Exception as e:
                print(f"[ERROR] Failed to calculate {ind_name}: {e}")

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        result.calculation_time_ms = duration_ms

        return result


# ============================================
# Convenience Functions
# ============================================

# Global calculator instance
_global_calculator: Optional[IndicatorCalculator] = None


def get_indicator_calculator() -> IndicatorCalculator:
    """Get global indicator calculator"""
    global _global_calculator

    if _global_calculator is None:
        _global_calculator = IndicatorCalculator()

    return _global_calculator


def calculate_indicator(
    indicator_name: str,
    data: pd.DataFrame,
    params=None
) -> IndicatorResult:
    """
    Convenience function to calculate single indicator

    Args:
        indicator_name: Indicator name (sma, ema, rsi, macd, etc.)
        data: OHLCV DataFrame
        params: Optional parameters

    Returns:
        IndicatorResult
    """
    calculator = get_indicator_calculator()
    return calculator.calculate_single(indicator_name, data, params)


def calculate_indicators(
    indicator_names: List[str],
    data: pd.DataFrame,
    symbol: str = "UNKNOWN"
) -> MultiIndicatorResult:
    """
    Calculate multiple indicators at once

    Args:
        indicator_names: List of indicator names
        data: OHLCV DataFrame
        symbol: Stock symbol

    Returns:
        MultiIndicatorResult
    """
    calculator = get_indicator_calculator()
    return calculator.calculate_batch(indicator_names, data, symbol)
