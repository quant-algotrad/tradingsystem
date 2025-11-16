"""
Trend Indicators
Indicators that identify market trends

Includes:
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- MACD (Moving Average Convergence Divergence)
"""

import pandas as pd
import numpy as np
from datetime import datetime

from src.indicators.base_indicator import BaseIndicator, SignalStrengthCalculator
from src.indicators.models import (
    IndicatorResult,
    IndicatorValue,
    IndicatorCategory,
    SignalValue,
    IndicatorSignal,
    MovingAverageParams,
    MACDParams,
    IndicatorParameters
)


# ============================================
# SMA (Simple Moving Average)
# ============================================

class SMA(BaseIndicator):
    """
    Simple Moving Average

    Calculates arithmetic mean of prices over a period
    Used for trend identification and support/resistance

    Formula: SMA = Sum(Close, N) / N
    """

    def __init__(self, params: MovingAverageParams = None):
        """
        Initialize SMA

        Args:
            params: MA parameters (period, default: 20)
        """
        if params is None:
            params = MovingAverageParams(period=20)

        super().__init__(params)
        self.params: MovingAverageParams = params

    def get_name(self) -> str:
        return f"SMA_{self.params.period}"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate SMA values"""
        close = data['close']

        # Calculate SMA
        sma = self._sma(close, self.params.period)

        # Create indicator values
        values = self._create_indicator_values(data.index, sma.values)

        return self._create_result(values)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret SMA signal

        Buy when price crosses above SMA
        Sell when price crosses below SMA
        """
        if abs(index) > len(result):
            raise ValueError(f"Index {index} out of range")

        current = result.values[index]
        prev = result.values[index - 1] if index > 0 or abs(index) < len(result) else None

        # Need price for crossover detection (would be passed in real implementation)
        # For now, simplified interpretation
        signal = SignalValue.NEUTRAL
        strength = 0.0

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=current.timestamp,
            signal=signal,
            strength=strength,
            current_value=current.value
        )


# ============================================
# EMA (Exponential Moving Average)
# ============================================

class EMA(BaseIndicator):
    """
    Exponential Moving Average

    Weighted moving average that gives more weight to recent prices
    More responsive to recent price changes than SMA

    Formula: EMA = Price(t) * k + EMA(y) * (1 – k)
    where k = 2 / (N + 1)
    """

    def __init__(self, params: MovingAverageParams = None):
        """
        Initialize EMA

        Args:
            params: MA parameters (period, default: 20)
        """
        if params is None:
            params = MovingAverageParams(period=20, ma_type="EMA")

        super().__init__(params)
        self.params: MovingAverageParams = params

    def get_name(self) -> str:
        return f"EMA_{self.params.period}"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate EMA values"""
        close = data['close']

        # Calculate EMA
        ema = self._ema(close, self.params.period)

        # Create indicator values
        values = self._create_indicator_values(data.index, ema.values)

        return self._create_result(values)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret EMA signal

        Similar to SMA - crossovers indicate trend changes
        """
        current = result.values[index]

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=current.timestamp,
            signal=SignalValue.NEUTRAL,
            strength=0.0,
            current_value=current.value
        )


# ============================================
# MACD (Moving Average Convergence Divergence)
# ============================================

class MACD(BaseIndicator):
    """
    Moving Average Convergence Divergence

    Trend-following momentum indicator
    Shows relationship between two moving averages

    Components:
    - MACD Line: 12-EMA - 26-EMA
    - Signal Line: 9-EMA of MACD Line
    - Histogram: MACD Line - Signal Line

    Signals:
    - MACD crosses above Signal: Buy
    - MACD crosses below Signal: Sell
    - Histogram expansion: Trend strengthening
    - Histogram contraction: Trend weakening
    """

    def __init__(self, params: MACDParams = None):
        """
        Initialize MACD

        Args:
            params: MACD parameters (fast=12, slow=26, signal=9)
        """
        if params is None:
            params = MACDParams()

        super().__init__(params)
        self.params: MACDParams = params

    def get_name(self) -> str:
        return "MACD"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def get_required_periods(self) -> int:
        """MACD needs slow_period + signal_period"""
        return self.params.slow_period + self.params.signal_period

    def _get_required_columns(self) -> list:
        return ['close']

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate MACD, Signal, and Histogram"""
        close = data['close']

        # Calculate EMAs
        ema_fast = self._ema(close, self.params.fast_period)
        ema_slow = self._ema(close, self.params.slow_period)

        # MACD Line
        macd_line = ema_fast - ema_slow

        # Signal Line (EMA of MACD)
        signal_line = macd_line.ewm(span=self.params.signal_period, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        # Create indicator values (using MACD line as primary)
        values = self._create_indicator_values(data.index, macd_line.values)

        # Additional lines
        additional_lines = {
            'signal': signal_line.values.tolist(),
            'histogram': histogram.values.tolist()
        }

        return self._create_result(values, additional_lines)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret MACD signal

        Buy: MACD crosses above Signal
        Sell: MACD crosses below Signal
        """
        if abs(index) > len(result):
            raise ValueError(f"Index {index} out of range")

        # Get current values
        macd_value = result.values[index].value
        signal_value = result.additional_lines['signal'][index]
        histogram_value = result.additional_lines['histogram'][index]

        # Determine signal based on crossover
        if histogram_value > 0:
            signal = SignalValue.BUY if histogram_value > 0.5 else SignalValue.NEUTRAL
        elif histogram_value < 0:
            signal = SignalValue.SELL if histogram_value < -0.5 else SignalValue.NEUTRAL
        else:
            signal = SignalValue.NEUTRAL

        # Calculate strength
        strength = SignalStrengthCalculator.calculate_macd_strength(
            macd_value,
            signal_value
        )

        # Check for crossover
        threshold_crossed = None
        if index > 0 or abs(index) < len(result):
            prev_hist = result.additional_lines['histogram'][index - 1]
            if prev_hist < 0 and histogram_value > 0:
                threshold_crossed = "bullish_crossover"
            elif prev_hist > 0 and histogram_value < 0:
                threshold_crossed = "bearish_crossover"

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=strength,
            current_value=macd_value,
            threshold_crossed=threshold_crossed,
            reasoning=f"MACD: {macd_value:.2f}, Signal: {signal_value:.2f}, "
                     f"Histogram: {histogram_value:.2f}"
        )


# ============================================
# ADX (Average Directional Index)
# ============================================

class ADX(BaseIndicator):
    """
    Average Directional Index

    Measures trend strength (not direction)
    Values range from 0-100

    Interpretation:
    - ADX < 20: Weak or no trend
    - ADX 20-25: Emerging trend
    - ADX 25-50: Strong trend
    - ADX > 50: Very strong trend

    Also calculates +DI and -DI for trend direction
    """

    def __init__(self, params: IndicatorParameters = None):
        """
        Initialize ADX

        Args:
            params: Period parameter (default: 14)
        """
        if params is None:
            params = IndicatorParameters(period=14)

        super().__init__(params)

    def get_name(self) -> str:
        return f"ADX_{self.params.period}"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def _get_required_columns(self) -> list:
        return ['high', 'low', 'close']

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate ADX, +DI, -DI"""
        high = data['high']
        low = data['low']
        close = data['close']

        # Calculate True Range
        tr = self._true_range(high, low, close)

        # Calculate Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()

        # Zero out negative movements
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # When both are positive, only count the larger one
        plus_dm[(plus_dm > 0) & (minus_dm > 0) & (plus_dm < minus_dm)] = 0
        minus_dm[(plus_dm > 0) & (minus_dm > 0) & (minus_dm < plus_dm)] = 0

        # Smooth the values
        period = self.params.period
        atr = tr.ewm(span=period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)

        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # Calculate ADX (smoothed DX)
        adx = dx.ewm(span=period, adjust=False).mean()

        # Create indicator values
        values = self._create_indicator_values(data.index, adx.values)

        # Additional lines
        additional_lines = {
            'plus_di': plus_di.values.tolist(),
            'minus_di': minus_di.values.tolist()
        }

        return self._create_result(values, additional_lines)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret ADX signal

        Strong trend if ADX > 25
        Direction from +DI and -DI
        """
        adx_value = result.values[index].value
        plus_di = result.additional_lines['plus_di'][index]
        minus_di = result.additional_lines['minus_di'][index]

        # Determine signal
        if adx_value < 20:
            signal = SignalValue.NEUTRAL
            reasoning = "Weak trend, avoid trading"
        elif plus_di > minus_di:
            signal = SignalValue.BUY if adx_value > 25 else SignalValue.NEUTRAL
            reasoning = f"Uptrend (ADX: {adx_value:.1f})"
        else:
            signal = SignalValue.SELL if adx_value > 25 else SignalValue.NEUTRAL
            reasoning = f"Downtrend (ADX: {adx_value:.1f})"

        # Strength based on ADX value
        strength = min(100, adx_value)

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=strength,
            current_value=adx_value,
            reasoning=reasoning
        )


# ============================================
# Supertrend Indicator
# ============================================

class Supertrend(BaseIndicator):
    """
    Supertrend Indicator

    Advanced trend-following indicator that provides dynamic support/resistance levels
    based on ATR (Average True Range) for volatility adaptation.

    Formula:
    Basic Upperband = (HIGH + LOW) / 2 + (Multiplier × ATR)
    Basic Lowerband = (HIGH + LOW) / 2 - (Multiplier × ATR)

    Final Bands adjust based on price action to create smooth support/resistance

    Signals:
    - Price above Supertrend (green): Uptrend, BUY signal
    - Price below Supertrend (red): Downtrend, SELL signal
    - Supertrend flip: Strong trend change signal

    Advantages:
    - Volatility-adjusted (uses ATR)
    - Clear visual trend identification
    - Combines trend direction and stop-loss level
    - Reduces whipsaws compared to simple moving averages

    Best for: Trending markets, swing trading
    """

    def __init__(self, params: IndicatorParameters = None):
        """
        Initialize Supertrend

        Args:
            params: Parameters (period=10, multiplier=3.0)
        """
        if params is None:
            params = IndicatorParameters(period=10)

        super().__init__(params)
        self.multiplier = 3.0  # ATR multiplier for band calculation

    def get_name(self) -> str:
        return f"SUPERTREND_{self.params.period}"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def _get_required_columns(self) -> list:
        return ['high', 'low', 'close']

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """
        Calculate Supertrend values

        Steps:
        1. Calculate ATR for volatility
        2. Calculate basic upper and lower bands
        3. Apply trend-following logic to finalize bands
        4. Determine Supertrend line based on price position
        """
        high = data['high']
        low = data['low']
        close = data['close']

        # Step 1: Calculate ATR
        atr = self._atr_calculation(high, low, close, self.params.period)

        # Step 2: Calculate basic bands
        # HL2 = (High + Low) / 2
        hl2 = (high + low) / 2

        basic_upperband = hl2 + (self.multiplier * atr)
        basic_lowerband = hl2 - (self.multiplier * atr)

        # Step 3: Apply trend-following logic
        # Final bands adjust based on previous values and price action
        final_upperband = pd.Series(index=data.index, dtype=float)
        final_lowerband = pd.Series(index=data.index, dtype=float)
        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=int)  # 1=up, -1=down

        # Initialize first values
        final_upperband.iloc[0] = basic_upperband.iloc[0]
        final_lowerband.iloc[0] = basic_lowerband.iloc[0]
        supertrend.iloc[0] = basic_upperband.iloc[0]
        direction.iloc[0] = -1  # Start bearish

        # Calculate for each subsequent bar
        for i in range(1, len(data)):
            # Upper band adjustment
            if basic_upperband.iloc[i] < final_upperband.iloc[i-1] or close.iloc[i-1] > final_upperband.iloc[i-1]:
                final_upperband.iloc[i] = basic_upperband.iloc[i]
            else:
                final_upperband.iloc[i] = final_upperband.iloc[i-1]

            # Lower band adjustment
            if basic_lowerband.iloc[i] > final_lowerband.iloc[i-1] or close.iloc[i-1] < final_lowerband.iloc[i-1]:
                final_lowerband.iloc[i] = basic_lowerband.iloc[i]
            else:
                final_lowerband.iloc[i] = final_lowerband.iloc[i-1]

            # Determine Supertrend and direction based on band crossovers
            # Compare with PREVIOUS bands to detect crossovers
            if close.iloc[i] > final_upperband.iloc[i-1]:
                # Price crossed above upper band -> Switch to uptrend
                direction.iloc[i] = 1
            elif close.iloc[i] < final_lowerband.iloc[i-1]:
                # Price crossed below lower band -> Switch to downtrend
                direction.iloc[i] = -1
            else:
                # Price between bands -> Maintain previous direction
                direction.iloc[i] = direction.iloc[i-1]

            # Set Supertrend line based on current direction
            if direction.iloc[i] == 1:
                # Uptrend: Supertrend acts as support (lower band)
                supertrend.iloc[i] = final_lowerband.iloc[i]
            else:
                # Downtrend: Supertrend acts as resistance (upper band)
                supertrend.iloc[i] = final_upperband.iloc[i]

        # Create indicator values (use Supertrend line)
        values = self._create_indicator_values(data.index, supertrend.values)

        # Store additional lines
        additional_lines = {
            'upperband': final_upperband.values.tolist(),
            'lowerband': final_lowerband.values.tolist(),
            'direction': direction.values.tolist()
        }

        return self._create_result(values, additional_lines)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret Supertrend signal

        Buy: Price above Supertrend (uptrend)
        Sell: Price below Supertrend (downtrend)
        Strong signal on trend flip
        """
        supertrend_value = result.values[index].value
        direction = result.additional_lines['direction'][index]

        # Determine signal based on direction
        if direction == 1:
            signal = SignalValue.BUY
            reasoning = "Price above Supertrend (uptrend)"
        else:
            signal = SignalValue.SELL
            reasoning = "Price below Supertrend (downtrend)"

        # Check for trend flip (strong signal)
        threshold_crossed = None
        if index > 0 or abs(index) < len(result):
            prev_direction = result.additional_lines['direction'][index - 1]
            if prev_direction == -1 and direction == 1:
                threshold_crossed = "bullish_flip"
                reasoning += " [TREND FLIP]"
            elif prev_direction == 1 and direction == -1:
                threshold_crossed = "bearish_flip"
                reasoning += " [TREND FLIP]"

        # Strength: 100 for clear trend, reduce if no flip
        strength = 100.0 if threshold_crossed else 75.0

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=strength,
            current_value=supertrend_value,
            threshold_crossed=threshold_crossed,
            reasoning=reasoning
        )


# ============================================
# Parabolic SAR (Stop and Reverse)
# ============================================

class ParabolicSAR(BaseIndicator):
    """
    Parabolic SAR (Stop and Reverse)

    Trend-following indicator that provides trailing stop-loss levels
    SAR dots appear below price in uptrend, above price in downtrend

    Formula:
    SAR(tomorrow) = SAR(today) + AF × (EP - SAR(today))

    Where:
    - SAR: Stop and Reverse price
    - AF: Acceleration Factor (starts at 0.02, increases by 0.02, max 0.20)
    - EP: Extreme Point (highest high in uptrend, lowest low in downtrend)

    Signals:
    - SAR below price: Uptrend, hold long
    - SAR above price: Downtrend, hold short
    - SAR flip: Strong reversal signal

    Advantages:
    - Provides automatic trailing stop levels
    - Clear trend direction
    - Accelerates with trend strength
    - Objective exit points

    Best for: Trending markets, trailing stops
    """

    def __init__(self, params: IndicatorParameters = None):
        """
        Initialize Parabolic SAR

        Args:
            params: Not used much, but kept for consistency
        """
        if params is None:
            params = IndicatorParameters(period=1)  # Not really used

        super().__init__(params)

        # Parabolic SAR parameters
        self.af_start = 0.02  # Initial acceleration factor
        self.af_increment = 0.02  # AF increment on new extreme
        self.af_max = 0.20  # Maximum acceleration factor

    def get_name(self) -> str:
        return "PSAR"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.TREND

    def _get_required_columns(self) -> list:
        return ['high', 'low', 'close']

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """
        Calculate Parabolic SAR values

        Complex algorithm that tracks trend and accelerates SAR movement
        """
        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        n = len(data)

        # Initialize arrays
        sar = np.zeros(n)
        trend = np.zeros(n, dtype=int)  # 1=up, -1=down
        af = np.zeros(n)
        ep = np.zeros(n)  # Extreme point

        # Initialize first values
        # Start with uptrend assumption
        sar[0] = low[0]
        trend[0] = 1
        af[0] = self.af_start
        ep[0] = high[0]

        # Calculate SAR for each bar
        for i in range(1, n):
            # Calculate new SAR
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])

            # Check for trend reversal
            if trend[i-1] == 1:  # Was in uptrend
                # Ensure SAR doesn't go above last two lows
                sar[i] = min(sar[i], low[i-1], low[i-2] if i >= 2 else low[i-1])

                # Check if trend reversed (price went below SAR)
                if low[i] < sar[i]:
                    trend[i] = -1  # Switch to downtrend
                    sar[i] = ep[i-1]  # SAR jumps to previous EP (high)
                    ep[i] = low[i]  # New EP is current low
                    af[i] = self.af_start  # Reset AF
                else:
                    trend[i] = 1  # Continue uptrend
                    ep[i] = max(ep[i-1], high[i])  # Update EP if new high

                    # Increment AF if new extreme point
                    if ep[i] > ep[i-1]:
                        af[i] = min(af[i-1] + self.af_increment, self.af_max)
                    else:
                        af[i] = af[i-1]

            else:  # Was in downtrend
                # Ensure SAR doesn't go below last two highs
                sar[i] = max(sar[i], high[i-1], high[i-2] if i >= 2 else high[i-1])

                # Check if trend reversed (price went above SAR)
                if high[i] > sar[i]:
                    trend[i] = 1  # Switch to uptrend
                    sar[i] = ep[i-1]  # SAR jumps to previous EP (low)
                    ep[i] = high[i]  # New EP is current high
                    af[i] = self.af_start  # Reset AF
                else:
                    trend[i] = -1  # Continue downtrend
                    ep[i] = min(ep[i-1], low[i])  # Update EP if new low

                    # Increment AF if new extreme point
                    if ep[i] < ep[i-1]:
                        af[i] = min(af[i-1] + self.af_increment, self.af_max)
                    else:
                        af[i] = af[i-1]

        # Create indicator values
        values = self._create_indicator_values(data.index, sar)

        # Additional lines
        additional_lines = {
            'trend': trend.tolist(),
            'af': af.tolist(),
            'ep': ep.tolist()
        }

        return self._create_result(values, additional_lines)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret Parabolic SAR signal

        Buy: Uptrend (SAR below price)
        Sell: Downtrend (SAR above price)
        Strong signal on SAR flip
        """
        sar_value = result.values[index].value
        trend = result.additional_lines['trend'][index]

        # Determine signal
        if trend == 1:
            signal = SignalValue.BUY
            reasoning = "PSAR below price (uptrend)"
        else:
            signal = SignalValue.SELL
            reasoning = "PSAR above price (downtrend)"

        # Check for SAR flip (reversal)
        threshold_crossed = None
        if index > 0 or abs(index) < len(result):
            prev_trend = result.additional_lines['trend'][index - 1]
            if prev_trend == -1 and trend == 1:
                threshold_crossed = "bullish_reversal"
                reasoning += " [SAR FLIP]"
            elif prev_trend == 1 and trend == -1:
                threshold_crossed = "bearish_reversal"
                reasoning += " [SAR FLIP]"

        # Strength: 100 on flip, 80 otherwise
        strength = 100.0 if threshold_crossed else 80.0

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=strength,
            current_value=sar_value,
            threshold_crossed=threshold_crossed,
            reasoning=reasoning
        )
