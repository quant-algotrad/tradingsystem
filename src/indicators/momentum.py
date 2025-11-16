"""
Momentum Indicators
Indicators that measure rate of price change

Includes:
- RSI (Relative Strength Index)
- Stochastic Oscillator
- CCI (Commodity Channel Index)
"""

import pandas as pd
import numpy as np

from src.indicators.base_indicator import BaseIndicator, SignalStrengthCalculator
from src.indicators.models import (
    IndicatorResult,
    IndicatorCategory,
    SignalValue,
    IndicatorSignal,
    RSIParams,
    IndicatorParameters
)


# ============================================
# RSI (Relative Strength Index)
# ============================================

class RSI(BaseIndicator):
    """
    Relative Strength Index

    Momentum oscillator measuring speed and magnitude of price changes
    Range: 0-100

    Interpretation:
    - RSI > 70: Overbought (potential sell)
    - RSI < 30: Oversold (potential buy)
    - RSI 40-60: Neutral zone
    - Divergence: Price vs RSI direction mismatch

    Formula:
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    """

    def __init__(self, params: RSIParams = None):
        """
        Initialize RSI

        Args:
            params: RSI parameters (period=14, overbought=70, oversold=30)
        """
        if params is None:
            params = RSIParams()

        super().__init__(params)
        self.params: RSIParams = params

    def get_name(self) -> str:
        return f"RSI_{self.params.period}"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.MOMENTUM

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate RSI values"""
        close = data['close']

        # Use helper method from base class
        rsi = self._rsi_calculation(close, self.params.period)

        # Create indicator values
        values = self._create_indicator_values(data.index, rsi.values)

        return self._create_result(values)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret RSI signal

        Overbought/Oversold levels determine signal
        """
        rsi_value = result.values[index].value

        # Determine signal
        threshold_crossed = None  # Initialize

        if rsi_value >= self.params.overbought:
            signal = SignalValue.SELL
            threshold_crossed = "overbought"
        elif rsi_value <= self.params.oversold:
            signal = SignalValue.BUY
            threshold_crossed = "oversold"
        elif rsi_value > 60:
            signal = SignalValue.NEUTRAL  # Leaning sell
        elif rsi_value < 40:
            signal = SignalValue.NEUTRAL  # Leaning buy
        else:
            signal = SignalValue.NEUTRAL

        # Calculate strength
        strength = SignalStrengthCalculator.calculate_rsi_strength(
            rsi_value,
            self.params.overbought,
            self.params.oversold
        )

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=strength,
            current_value=rsi_value,
            threshold_crossed=threshold_crossed,
            reasoning=f"RSI at {rsi_value:.1f}"
        )


# ============================================
# Stochastic Oscillator
# ============================================

class Stochastic(BaseIndicator):
    """
    Stochastic Oscillator

    Compares closing price to price range over time
    Shows momentum and identifies overbought/oversold conditions

    Components:
    - %K (Fast): Current close position in range
    - %D (Slow): 3-period SMA of %K

    Formula:
    %K = 100 * (Close - Low14) / (High14 - Low14)
    %D = 3-period SMA of %K
    """

    def __init__(self, params: IndicatorParameters = None):
        """
        Initialize Stochastic

        Args:
            params: Period parameter (default: 14)
        """
        if params is None:
            params = IndicatorParameters(period=14)

        super().__init__(params)
        self.k_period = 14  # %K lookback
        self.d_period = 3   # %D smoothing

    def get_name(self) -> str:
        return "STOCH"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.MOMENTUM

    def _get_required_columns(self) -> list:
        return ['high', 'low', 'close']

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate Stochastic %K and %D"""
        high = data['high']
        low = data['low']
        close = data['close']

        # Calculate %K
        low_min = low.rolling(window=self.k_period).min()
        high_max = high.rolling(window=self.k_period).max()

        k = 100 * ((close - low_min) / (high_max - low_min))

        # Calculate %D (SMA of %K)
        d = k.rolling(window=self.d_period).mean()

        # Create indicator values (using %K as primary)
        values = self._create_indicator_values(data.index, k.values)

        # Additional lines
        additional_lines = {
            'd': d.values.tolist()
        }

        return self._create_result(values, additional_lines)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret Stochastic signal

        %K above 80: Overbought
        %K below 20: Oversold
        %K crosses %D: Trend change
        """
        k_value = result.values[index].value
        d_value = result.additional_lines['d'][index]

        # Determine signal
        if k_value >= 80:
            signal = SignalValue.SELL
            threshold_crossed = "overbought"
        elif k_value <= 20:
            signal = SignalValue.BUY
            threshold_crossed = "oversold"
        else:
            # Check for crossover
            if index > 0 or abs(index) < len(result):
                prev_k = result.values[index - 1].value
                prev_d = result.additional_lines['d'][index - 1]

                if prev_k < prev_d and k_value > d_value:
                    signal = SignalValue.BUY
                    threshold_crossed = "bullish_crossover"
                elif prev_k > prev_d and k_value < d_value:
                    signal = SignalValue.SELL
                    threshold_crossed = "bearish_crossover"
                else:
                    signal = SignalValue.NEUTRAL
                    threshold_crossed = None
            else:
                signal = SignalValue.NEUTRAL
                threshold_crossed = None

        # Strength based on distance from middle
        strength = abs(k_value - 50) * 2  # 0-100 scale

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=strength,
            current_value=k_value,
            threshold_crossed=threshold_crossed,
            reasoning=f"Stoch %K: {k_value:.1f}, %D: {d_value:.1f}"
        )
