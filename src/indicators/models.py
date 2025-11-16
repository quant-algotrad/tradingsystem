"""
Indicator Result Models
Data transfer objects for indicator calculations
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import pandas as pd


# ============================================
# ENUMS
# ============================================

class IndicatorCategory(Enum):
    """Indicator categories"""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    SUPPORT_RESISTANCE = "support_resistance"


class SignalValue(Enum):
    """Indicator signal interpretations"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


# ============================================
# INDICATOR RESULT MODELS
# ============================================

@dataclass
class IndicatorValue:
    """
    Single indicator value at a point in time

    Represents one calculated value from an indicator
    """
    timestamp: datetime
    value: float

    # Optional metadata
    signal: Optional[SignalValue] = None
    confidence: Optional[float] = None  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'value': self.value,
            'signal': self.signal.value if self.signal else None,
            'confidence': self.confidence
        }


@dataclass
class IndicatorResult:
    """
    Complete indicator calculation result

    Contains all values calculated by an indicator
    Can represent single-line or multi-line indicators
    """
    indicator_name: str
    category: IndicatorCategory

    # Primary values (for single-line indicators like RSI, SMA)
    values: List[IndicatorValue] = field(default_factory=list)

    # Additional lines (for multi-line indicators like MACD, Bollinger Bands)
    additional_lines: Dict[str, List[float]] = field(default_factory=dict)

    # Metadata
    parameters: Dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.now)

    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def __post_init__(self):
        """Initialize date range"""
        if self.values:
            timestamps = [v.timestamp for v in self.values]
            self.start_date = min(timestamps)
            self.end_date = max(timestamps)

    def __len__(self) -> int:
        """Number of values"""
        return len(self.values)

    def __getitem__(self, index: int) -> IndicatorValue:
        """Get value by index"""
        return self.values[index]

    def get_latest(self, n: int = 1) -> List[IndicatorValue]:
        """Get latest n values"""
        return self.values[-n:] if self.values else []

    def get_latest_value(self) -> Optional[float]:
        """Get latest single value"""
        return self.values[-1].value if self.values else None

    def get_values_list(self) -> List[float]:
        """Get list of all values"""
        return [v.value for v in self.values]

    def to_series(self) -> pd.Series:
        """
        Convert to pandas Series

        Returns:
            Series with timestamp index
        """
        if not self.values:
            return pd.Series(dtype=float)

        data = {v.timestamp: v.value for v in self.values}
        series = pd.Series(data)
        series.name = self.indicator_name
        return series

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert to pandas DataFrame (for multi-line indicators)

        Returns:
            DataFrame with timestamp index and value columns
        """
        if not self.values:
            return pd.DataFrame()

        # Primary values
        data = {
            'timestamp': [v.timestamp for v in self.values],
            self.indicator_name: [v.value for v in self.values]
        }

        # Additional lines
        for line_name, line_values in self.additional_lines.items():
            data[line_name] = line_values

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df


@dataclass
class MultiIndicatorResult:
    """
    Result containing multiple indicators calculated together

    Used when calculating multiple indicators on same data
    for optimization
    """
    symbol: str
    timeframe: str

    # Dictionary of indicator results
    indicators: Dict[str, IndicatorResult] = field(default_factory=dict)

    # Metadata
    calculated_at: datetime = field(default_factory=datetime.now)
    calculation_time_ms: Optional[float] = None

    def add_indicator(self, result: IndicatorResult):
        """Add an indicator result"""
        self.indicators[result.indicator_name] = result

    def get_indicator(self, name: str) -> Optional[IndicatorResult]:
        """Get specific indicator result"""
        return self.indicators.get(name)

    def get_latest_values(self) -> Dict[str, float]:
        """Get latest value for each indicator"""
        return {
            name: result.get_latest_value()
            for name, result in self.indicators.items()
            if result.get_latest_value() is not None
        }

    def to_dataframe(self) -> pd.DataFrame:
        """
        Combine all indicators into single DataFrame

        Returns:
            DataFrame with all indicator columns
        """
        if not self.indicators:
            return pd.DataFrame()

        # Collect all series
        series_list = []
        for result in self.indicators.values():
            series = result.to_series()
            series_list.append(series)

        # Combine
        df = pd.concat(series_list, axis=1)
        return df


@dataclass
class IndicatorSignal:
    """
    Trading signal derived from indicator

    Interprets indicator values into actionable signals
    """
    indicator_name: str
    timestamp: datetime
    signal: SignalValue
    strength: float  # 0-100

    # Supporting data
    current_value: float
    threshold_crossed: Optional[str] = None
    divergence_detected: bool = False

    # Context
    price: Optional[float] = None
    reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'indicator_name': self.indicator_name,
            'timestamp': self.timestamp,
            'signal': self.signal.value,
            'strength': self.strength,
            'current_value': self.current_value,
            'threshold_crossed': self.threshold_crossed,
            'divergence_detected': self.divergence_detected,
            'price': self.price,
            'reasoning': self.reasoning
        }


# ============================================
# INDICATOR PARAMETERS
# ============================================

@dataclass
class IndicatorParameters:
    """
    Base class for indicator parameters

    Encapsulates all configuration for an indicator
    """
    # Common parameters
    period: int = 14

    def validate(self) -> tuple[bool, List[str]]:
        """Validate parameters"""
        errors = []

        if self.period < 1:
            errors.append("Period must be at least 1")

        if self.period > 500:
            errors.append("Period cannot exceed 500")

        return (len(errors) == 0, errors)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'period': self.period
        }


@dataclass
class MovingAverageParams(IndicatorParameters):
    """Parameters for moving averages"""
    period: int = 20
    ma_type: str = "SMA"  # SMA, EMA, WMA

    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': self.period,
            'ma_type': self.ma_type
        }


@dataclass
class RSIParams(IndicatorParameters):
    """Parameters for RSI"""
    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0

    def validate(self) -> tuple[bool, List[str]]:
        is_valid, errors = super().validate()

        if not (0 < self.overbought <= 100):
            errors.append("Overbought must be between 0 and 100")

        if not (0 <= self.oversold < 100):
            errors.append("Oversold must be between 0 and 100")

        if self.oversold >= self.overbought:
            errors.append("Oversold must be less than overbought")

        return (len(errors) == 0, errors)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': self.period,
            'overbought': self.overbought,
            'oversold': self.oversold
        }


@dataclass
class MACDParams(IndicatorParameters):
    """Parameters for MACD"""
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9

    def validate(self) -> tuple[bool, List[str]]:
        errors = []

        if self.fast_period >= self.slow_period:
            errors.append("Fast period must be less than slow period")

        if self.signal_period < 1:
            errors.append("Signal period must be at least 1")

        return (len(errors) == 0, errors)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fast_period': self.fast_period,
            'slow_period': self.slow_period,
            'signal_period': self.signal_period
        }


@dataclass
class BollingerBandsParams(IndicatorParameters):
    """Parameters for Bollinger Bands"""
    period: int = 20
    std_dev: float = 2.0

    def validate(self) -> tuple[bool, List[str]]:
        is_valid, errors = super().validate()

        if self.std_dev <= 0:
            errors.append("Standard deviation must be positive")

        if self.std_dev > 5:
            errors.append("Standard deviation typically should not exceed 5")

        return (len(errors) == 0, errors)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': self.period,
            'std_dev': self.std_dev
        }


@dataclass
class ATRParams(IndicatorParameters):
    """Parameters for ATR (Average True Range)"""
    period: int = 14

    def to_dict(self) -> Dict[str, Any]:
        return {'period': self.period}
