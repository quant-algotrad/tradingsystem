"""
Volatility Indicators
Indicators that measure price volatility and range

Includes:
- Bollinger Bands
- ATR (Average True Range)
"""

import pandas as pd

from src.indicators.base_indicator import BaseIndicator, SignalStrengthCalculator
from src.indicators.models import (
    IndicatorResult,
    IndicatorCategory,
    SignalValue,
    IndicatorSignal,
    BollingerBandsParams,
    ATRParams
)


# ============================================
# Bollinger Bands
# ============================================

class BollingerBands(BaseIndicator):
    """
    Bollinger Bands

    Volatility indicator using standard deviations
    Creates dynamic support/resistance levels

    Components:
    - Middle Band: 20-period SMA
    - Upper Band: Middle + (2 * StdDev)
    - Lower Band: Middle - (2 * StdDev)

    Signals:
    - Price touching upper band: Overbought
    - Price touching lower band: Oversold
    - Band squeeze: Low volatility, potential breakout
    - Band expansion: High volatility
    """

    def __init__(self, params: BollingerBandsParams = None):
        """
        Initialize Bollinger Bands

        Args:
            params: BB parameters (period=20, std_dev=2.0)
        """
        if params is None:
            params = BollingerBandsParams()

        super().__init__(params)
        self.params: BollingerBandsParams = params

    def get_name(self) -> str:
        return "BB"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.VOLATILITY

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate Bollinger Bands"""
        close = data['close']

        # Middle band (SMA)
        middle = self._sma(close, self.params.period)

        # Standard deviation
        std = self._std(close, self.params.period)

        # Upper and lower bands
        upper = middle + (self.params.std_dev * std)
        lower = middle - (self.params.std_dev * std)

        # Create indicator values (using middle band as primary)
        values = self._create_indicator_values(data.index, middle.values)

        # Additional lines
        additional_lines = {
            'upper': upper.values.tolist(),
            'lower': lower.values.tolist(),
            'width': (upper - lower).values.tolist()
        }

        return self._create_result(values, additional_lines)

    def interpret_signal(self, result: IndicatorResult, index: int = -1, price: float = None) -> IndicatorSignal:
        """
        Interpret Bollinger Bands signal

        Requires current price for accurate signal
        """
        middle = result.values[index].value
        upper = result.additional_lines['upper'][index]
        lower = result.additional_lines['lower'][index]

        # If no price provided, use middle as estimate
        if price is None:
            price = middle

        # Determine signal
        if price >= upper:
            signal = SignalValue.SELL
            threshold_crossed = "upper_band"
        elif price <= lower:
            signal = SignalValue.BUY
            threshold_crossed = "lower_band"
        elif price > middle:
            signal = SignalValue.NEUTRAL  # Above middle
        else:
            signal = SignalValue.NEUTRAL  # Below middle

        # Calculate strength
        strength = SignalStrengthCalculator.calculate_bb_strength(
            price, upper, lower, middle
        )

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=strength,
            current_value=middle,
            threshold_crossed=threshold_crossed,
            price=price,
            reasoning=f"Price: {price:.2f}, Upper: {upper:.2f}, "
                     f"Middle: {middle:.2f}, Lower: {lower:.2f}"
        )


# ============================================
# ATR (Average True Range)
# ============================================

class ATR(BaseIndicator):
    """
    Average True Range

    Volatility indicator measuring market volatility
    Higher values = higher volatility

    Not directional, but useful for:
    - Stop-loss placement
    - Position sizing
    - Volatility assessment

    Formula:
    TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    ATR = EMA(TR, period)
    """

    def __init__(self, params: ATRParams = None):
        """
        Initialize ATR

        Args:
            params: ATR parameters (period=14)
        """
        if params is None:
            params = ATRParams()

        super().__init__(params)
        self.params: ATRParams = params

    def get_name(self) -> str:
        return f"ATR_{self.params.period}"

    def get_category(self) -> IndicatorCategory:
        return IndicatorCategory.VOLATILITY

    def _get_required_columns(self) -> list:
        return ['high', 'low', 'close']

    def _calculate_values(self, data: pd.DataFrame) -> IndicatorResult:
        """Calculate ATR"""
        high = data['high']
        low = data['low']
        close = data['close']

        # Calculate True Range
        tr = self._true_range(high, low, close)

        # Calculate ATR (EMA of TR)
        atr = tr.ewm(span=self.params.period, adjust=False).mean()

        # Create indicator values
        values = self._create_indicator_values(data.index, atr.values)

        return self._create_result(values)

    def interpret_signal(self, result: IndicatorResult, index: int = -1) -> IndicatorSignal:
        """
        Interpret ATR signal

        ATR doesn't give buy/sell signals directly
        High ATR = High volatility
        Low ATR = Low volatility
        """
        atr_value = result.values[index].value

        # ATR itself doesn't generate buy/sell signals
        signal = SignalValue.NEUTRAL

        # Could compare to historical ATR for volatility assessment
        # For now, simple interpretation
        if index >= 20:
            recent_atr = [result.values[i].value for i in range(index-19, index+1)]
            avg_atr = sum(recent_atr) / len(recent_atr)

            if atr_value > avg_atr * 1.5:
                reasoning = "High volatility - use wider stops"
            elif atr_value < avg_atr * 0.5:
                reasoning = "Low volatility - potential breakout coming"
            else:
                reasoning = "Normal volatility"
        else:
            reasoning = f"ATR: {atr_value:.2f}"

        return IndicatorSignal(
            indicator_name=self.get_name(),
            timestamp=result.values[index].timestamp,
            signal=signal,
            strength=0.0,
            current_value=atr_value,
            reasoning=reasoning
        )
