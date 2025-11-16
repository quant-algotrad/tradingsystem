"""
Trend Following RSI Strategy
Combines trend indicators (EMA) with RSI confirmation

This strategy rides strong trends with RSI confirmation to avoid
entering overbought/oversold conditions during trend.
"""

from typing import Dict, Optional
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.strategy.signal_aggregator import AggregatedSignal


class TrendFollowingStrategy(TradingStrategy):
    """
    Trend Following + RSI Strategy

    Logic:
    - Identifies strong trends using EMA crossovers (20/50 EMA)
    - Confirms with RSI in healthy range (40-60 for uptrend, 40-60 for downtrend)
    - ADX > 20 for trend strength confirmation
    - 2% stop loss with 3:1 risk:reward ratio

    Entry Criteria:
    BUY:
    - Fast EMA (20) > Slow EMA (50) - Uptrend confirmed
    - RSI between 40-70 (not overbought, still has room)
    - ADX > 20 (trend has strength)
    - Price above 50 EMA

    SELL/SHORT:
    - Fast EMA (20) < Slow EMA (50) - Downtrend confirmed
    - RSI between 30-60 (not oversold, still has room to fall)
    - ADX > 20 (trend has strength)
    - Price below 50 EMA

    Best for: Trending markets, swing trading (2-10 days hold)
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        Initialize Trend Following strategy

        Args:
            config: Strategy configuration parameters
        """
        super().__init__(config)

        # Trend Following specific parameters
        self.fast_ema_period = 20
        self.slow_ema_period = 50
        self.rsi_buy_min = 40
        self.rsi_buy_max = 70
        self.rsi_sell_min = 30
        self.rsi_sell_max = 60
        self.min_adx = 20

    def get_name(self) -> str:
        return "TREND_FOLLOWING"

    def get_description(self) -> str:
        return "Trend following strategy using EMA crossover with RSI confirmation for swing trades"

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate entry, stop loss, and target levels for trend following

        Trend following uses:
        - Entry: Current market price
        - Stop Loss: 2% or 1.5x ATR (whichever is wider to avoid noise)
        - Target: 3:1 risk:reward ratio (riding the trend)

        Args:
            current_price: Current market price
            signal: Aggregated signal from indicators
            action: Trade action (BUY/SHORT/SELL)

        Returns:
            Dictionary with entry, stop_loss, and target prices
        """
        # Get ATR for volatility-adjusted stops
        atr_value = self._get_atr_value(signal)

        if action == "BUY":
            # Long position: Ride the uptrend
            entry = current_price

            # Stop loss: 2% or 1.5x ATR (use wider for less noise)
            # Trend following needs room to breathe
            stop_pct = entry * 0.98  # 2% stop
            if atr_value:
                stop_atr = entry - (atr_value * 1.5)
                # Use whichever gives more room (lower stop)
                stop_loss = min(stop_pct, stop_atr)
            else:
                stop_loss = stop_pct

            # Target: 3x risk for trend riding
            # Let winners run in a strong trend
            risk = entry - stop_loss
            target = entry + (risk * 3.0)

        elif action == "SHORT":
            # Short position: Ride the downtrend
            entry = current_price

            # Stop loss: 2% or 1.5x ATR (use wider)
            stop_pct = entry * 1.02  # 2% stop
            if atr_value:
                stop_atr = entry + (atr_value * 1.5)
                # Use whichever gives more room (higher stop)
                stop_loss = max(stop_pct, stop_atr)
            else:
                stop_loss = stop_pct

            # Target: 3x risk
            risk = stop_loss - entry
            target = entry - (risk * 3.0)

        else:  # SELL (exit long)
            # Exit at market price
            entry = current_price
            stop_loss = current_price
            target = current_price

        return {
            'entry': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2)
        }

    def should_take_trade(
        self,
        signal: AggregatedSignal,
        current_price: float,
        **kwargs
    ) -> tuple[bool, str]:
        """
        Validate trend following conditions before taking trade

        Checks:
        1. Base validation (from parent class)
        2. EMA alignment (fast > slow for BUY, fast < slow for SHORT)
        3. RSI in healthy range (not overbought for BUY, not oversold for SHORT)
        4. ADX shows trend strength (> 20)
        5. Price position relative to EMAs

        Args:
            signal: Aggregated signal with indicator data
            current_price: Current market price
            **kwargs: Additional parameters

        Returns:
            Tuple of (should_trade: bool, reason: str)
        """
        # Check base criteria from parent class
        should_trade, reason = super().should_take_trade(signal, current_price, **kwargs)
        if not should_trade:
            return False, reason

        # Extract indicator values
        rsi_value = self._get_rsi_value(signal)
        adx_value = self._get_adx_value(signal)
        ema_20 = self._get_ema_value(signal, 20)
        ema_50 = self._get_ema_value(signal, 50)

        # Validate required indicators
        if rsi_value is None:
            return False, "RSI data not available"

        if adx_value is None:
            return False, "ADX data not available for trend strength"

        # Check ADX for trend strength
        # ADX < 20 means weak/no trend - not suitable for trend following
        if adx_value < self.min_adx:
            return False, f"ADX {adx_value:.1f} < {self.min_adx} (trend too weak)"

        # Determine if signal is bullish or bearish
        is_bullish_signal = signal.bullish_signals > signal.bearish_signals
        is_bearish_signal = signal.bearish_signals > signal.bullish_signals

        # Validate EMA crossover if available
        if ema_20 is not None and ema_50 is not None:
            ema_bullish = ema_20 > ema_50  # Fast above slow = uptrend
            ema_bearish = ema_20 < ema_50  # Fast below slow = downtrend

            if is_bullish_signal and not ema_bullish:
                return False, f"Bullish signal but EMA bearish (EMA20: {ema_20:.2f} < EMA50: {ema_50:.2f})"

            if is_bearish_signal and not ema_bearish:
                return False, f"Bearish signal but EMA bullish (EMA20: {ema_20:.2f} > EMA50: {ema_50:.2f})"

        # Validate RSI for healthy trend conditions
        if is_bullish_signal:
            # For uptrend: RSI should be 40-70
            # Below 40: might still be in downtrend
            # Above 70: overbought, likely to reverse soon
            if rsi_value < self.rsi_buy_min:
                return False, f"RSI {rsi_value:.1f} < {self.rsi_buy_min} (uptrend not confirmed)"

            if rsi_value > self.rsi_buy_max:
                return False, f"RSI {rsi_value:.1f} > {self.rsi_buy_max} (overbought, trend may reverse)"

        elif is_bearish_signal:
            # For downtrend: RSI should be 30-60
            # Above 60: might still be in uptrend
            # Below 30: oversold, might bounce
            if rsi_value < self.rsi_sell_min:
                return False, f"RSI {rsi_value:.1f} < {self.rsi_sell_min} (oversold, may bounce)"

            if rsi_value > self.rsi_sell_max:
                return False, f"RSI {rsi_value:.1f} > {self.rsi_sell_max} (downtrend not confirmed)"

        # All trend following conditions met
        return True, f"Trend confirmed (ADX: {adx_value:.1f}, RSI: {rsi_value:.1f})"

    def _get_atr_value(self, signal: AggregatedSignal) -> Optional[float]:
        """
        Extract ATR (Average True Range) value from indicator signals

        ATR measures volatility for adaptive stop losses
        """
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ATR' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_rsi_value(self, signal: AggregatedSignal) -> Optional[float]:
        """
        Extract RSI (Relative Strength Index) value

        RSI shows momentum and overbought/oversold conditions
        """
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'RSI' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_adx_value(self, signal: AggregatedSignal) -> Optional[float]:
        """
        Extract ADX (Average Directional Index) value

        ADX measures trend strength (not direction)
        > 25: Strong trend
        20-25: Moderate trend
        < 20: Weak/no trend
        """
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ADX' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_ema_value(self, signal: AggregatedSignal, period: int) -> Optional[float]:
        """
        Extract EMA (Exponential Moving Average) value for specific period

        EMA is used to identify trend direction
        Fast EMA (20) > Slow EMA (50) = Uptrend
        Fast EMA (20) < Slow EMA (50) = Downtrend

        Args:
            signal: Aggregated signal
            period: EMA period (e.g., 20, 50)

        Returns:
            EMA value or None if not found
        """
        for ind_name, ind_signal in signal.indicator_signals.items():
            if f'EMA_{period}' in ind_name.upper():
                return ind_signal.current_value
        return None
