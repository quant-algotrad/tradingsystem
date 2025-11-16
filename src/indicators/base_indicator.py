"""
Base Indicator Classes
Abstract base classes and interfaces for all indicators

Patterns:
- Strategy Pattern: Different calculation algorithms
- Template Method: Common calculation flow
- Factory Pattern: Indicator creation
"""

from abc import ABC, abstractmethod
from typing import Optional, List
import pandas as pd
import numpy as np
from datetime import datetime

from src.indicators.models import (
    IndicatorResult,
    IndicatorValue,
    IndicatorParameters,
    IndicatorCategory,
    SignalValue,
    IndicatorSignal
)


# ============================================
# INTERFACE: Indicator Contract
# ============================================

class IIndicator(ABC):
    """
    Interface for all technical indicators

    SOLID Principles:
    - Interface Segregation: Specific interface for indicators
    - Dependency Inversion: Depend on abstraction

    Pattern: Strategy Pattern
    - Different indicators implement same interface
    - Can be swapped at runtime
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get indicator name"""
        pass

    @abstractmethod
    def get_category(self) -> IndicatorCategory:
        """Get indicator category"""
        pass

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        """
        Calculate indicator values

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume

        Returns:
            IndicatorResult with calculated values
        """
        pass

    @abstractmethod
    def get_required_periods(self) -> int:
        """
        Get minimum number of periods required for calculation

        Returns:
            Minimum bars needed
        """
        pass

    @abstractmethod
    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret indicator value as trading signal

        Args:
            result: Indicator calculation result
            index: Index of value to interpret (-1 for latest)

        Returns:
            IndicatorSignal with interpretation
        """
        pass


# ============================================
# ABSTRACT BASE: Indicator Implementation
# ============================================

class BaseIndicator(IIndicator, ABC):
    """
    Abstract base class for all indicators

    Provides:
    - Parameter management
    - Data validation
    - Result creation helpers
    - Common calculations

    SOLID Principles:
    - Single Responsibility: Base functionality only
    - Open/Closed: Open for extension, closed for modification

    Pattern: Template Method
    - Defines calculation algorithm skeleton
    - Subclasses implement specific steps
    """

    def __init__(self, params: IndicatorParameters):
        """
        Initialize indicator

        Args:
            params: Indicator parameters
        """
        self.params = params

        # Validate parameters
        is_valid, errors = params.validate()
        if not is_valid:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

    def get_name(self) -> str:
        """Get indicator name (default implementation)"""
        return self.__class__.__name__

    def get_required_periods(self) -> int:
        """Default implementation uses period parameter"""
        return getattr(self.params, 'period', 14)

    # ========================================
    # Template Method Pattern
    # ========================================

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        """
        Template method for indicator calculation

        Pattern: Template Method
        - Defines skeleton of calculation
        - Subclasses implement _calculate_values
        """
        # Validate data
        self._validate_data(data)

        # Check minimum periods
        if len(data) < self.get_required_periods():
            raise ValueError(
                f"{self.get_name()} requires at least {self.get_required_periods()} "
                f"periods, got {len(data)}"
            )

        # Delegate to concrete implementation
        try:
            result = self._calculate_values(data)
            return result

        except Exception as e:
            raise RuntimeError(f"Indicator calculation failed: {e}") from e

    @abstractmethod
    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """
        Calculate indicator values (implemented by subclasses)

        Args:
            data: Validated OHLCV DataFrame

        Returns:
            IndicatorResult
        """
        pass

    # ========================================
    # Helper Methods
    # ========================================

    def _validate_data(self, data: pd.DataFrame):
        """Validate input data"""
        if data is None or data.empty:
            raise ValueError("Data cannot be empty")

        # Check for required columns
        required_columns = self._get_required_columns()
        missing = set(required_columns) - set(data.columns)

        if missing:
            raise ValueError(
                f"Missing required columns: {missing}. "
                f"Available: {list(data.columns)}"
            )

        # Check for NaN values
        if data[required_columns].isnull().any().any():
            raise ValueError("Data contains NaN values")

    def _get_required_columns(self) -> List[str]:
        """Get required DataFrame columns (can be overridden)"""
        return ['close']  # Most indicators only need close

    def _create_result(
        self,
        values: List[IndicatorValue],
        additional_lines: Optional[dict] = None
    ) -> IndicatorResult:
        """
        Create indicator result

        Args:
            values: List of indicator values
            additional_lines: Optional additional data lines

        Returns:
            IndicatorResult
        """
        return IndicatorResult(
            indicator_name=self.get_name(),
            category=self.get_category(),
            values=values,
            additional_lines=additional_lines or {},
            parameters=self.params.to_dict()
        )

    def _create_indicator_values(
        self,
        timestamps: pd.DatetimeIndex,
        values: np.ndarray
    ) -> List[IndicatorValue]:
        """
        Create list of IndicatorValue objects

        Args:
            timestamps: Timestamp index
            values: Numpy array of values

        Returns:
            List of IndicatorValue
        """
        result = []

        for timestamp, value in zip(timestamps, values):
            if not np.isnan(value):
                result.append(IndicatorValue(
                    timestamp=timestamp,
                    value=float(value)
                ))

        return result

    # ========================================
    # Common Calculations
    # ========================================

    @staticmethod
    def _sma(data: pd.Series, period: int) -> pd.Series:
        """
        Simple Moving Average

        Args:
            data: Price series
            period: SMA period

        Returns:
            SMA series
        """
        return data.rolling(window=period).mean()

    @staticmethod
    def _ema(data: pd.Series, period: int) -> pd.Series:
        """
        Exponential Moving Average

        Args:
            data: Price series
            period: EMA period

        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _std(data: pd.Series, period: int) -> pd.Series:
        """
        Standard Deviation

        Args:
            data: Price series
            period: Period

        Returns:
            Standard deviation series
        """
        return data.rolling(window=period).std()

    @staticmethod
    def _rsi_calculation(data: pd.Series, period: int) -> pd.Series:
        """
        RSI calculation helper

        Args:
            data: Price series
            period: RSI period

        Returns:
            RSI series (0-100)
        """
        # Calculate price changes
        delta = data.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # Calculate average gains and losses
        avg_gains = gains.ewm(span=period, adjust=False).mean()
        avg_losses = losses.ewm(span=period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        True Range calculation

        Args:
            high: High prices
            low: Low prices
            close: Close prices

        Returns:
            True Range series
        """
        hl = high - low
        hc = abs(high - close.shift())
        lc = abs(low - close.shift())

        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return tr


# ============================================
# INTERFACE: Signal Generator
# ============================================

class ISignalGenerator(ABC):
    """
    Interface for generating trading signals from indicators
    """

    @abstractmethod
    def generate_signal(
        self,
        indicator_result: IndicatorResult,
        price: float
    ) -> IndicatorSignal:
        """Generate trading signal from indicator"""
        pass


# ============================================
# HELPER: Signal Strength Calculator
# ============================================

class SignalStrengthCalculator:
    """
    Utility class for calculating signal strength

    Pattern: Strategy Pattern for strength calculation
    """

    @staticmethod
    def calculate_rsi_strength(rsi_value: float, overbought: float = 70, oversold: float = 30) -> float:
        """
        Calculate signal strength from RSI

        Args:
            rsi_value: RSI value (0-100)
            overbought: Overbought threshold
            oversold: Oversold threshold

        Returns:
            Strength (0-100)
        """
        if rsi_value >= overbought:
            # Sell signal strength
            return min(100, (rsi_value - overbought) / (100 - overbought) * 100)
        elif rsi_value <= oversold:
            # Buy signal strength
            return min(100, (oversold - rsi_value) / oversold * 100)
        else:
            # Neutral zone
            return 0.0

    @staticmethod
    def calculate_macd_strength(macd: float, signal: float) -> float:
        """
        Calculate signal strength from MACD

        Args:
            macd: MACD line value
            signal: Signal line value

        Returns:
            Strength (0-100)
        """
        diff = abs(macd - signal)

        # Normalize to 0-100 (using typical MACD range)
        # This is simplified - could be improved with historical context
        strength = min(100, diff * 10)

        return strength

    @staticmethod
    def calculate_bb_strength(price: float, upper: float, lower: float, middle: float) -> float:
        """
        Calculate signal strength from Bollinger Bands

        Args:
            price: Current price
            upper: Upper band
            lower: Lower band
            middle: Middle band (SMA)

        Returns:
            Strength (0-100)
        """
        band_width = upper - lower

        if price >= upper:
            # Above upper band - sell signal
            excess = price - upper
            return min(100, (excess / band_width) * 100)
        elif price <= lower:
            # Below lower band - buy signal
            excess = lower - price
            return min(100, (excess / band_width) * 100)
        else:
            # Within bands
            return 0.0
