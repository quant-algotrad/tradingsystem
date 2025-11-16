"""
Momentum Swing Strategy
Captures strong daily momentum swings with multi-indicator confirmation

This strategy identifies stocks with strong momentum on daily timeframe
and enters when multiple momentum indicators align.
"""

from typing import Dict, Optional
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.strategy.signal_aggregator import AggregatedSignal


class MomentumSwingStrategy(TradingStrategy):
    """
    Momentum Swing Strategy

    Logic:
    - Identifies strong daily momentum using multiple indicators
    - Requires alignment of RSI, MACD, and Stochastic
    - Confirms with volume surge (above average)
    - Uses volatility-based stops (ATR)
    - Targets 2.5:1 risk:reward ratio

    Entry Criteria:
    BUY:
    - RSI > 60 (momentum building, not yet overbought)
    - MACD line > Signal line (bullish momentum)
    - Stochastic %K > %D (bullish crossover or alignment)
    - Volume > 1.5x average (confirmation)
    - ADX > 20 (trending, not choppy)

    SHORT:
    - RSI < 40 (momentum declining, not yet oversold)
    - MACD line < Signal line (bearish momentum)
    - Stochastic %K < %D (bearish crossover or alignment)
    - Volume > 1.5x average (confirmation)
    - ADX > 20

    Stop Loss:
    - 1.5x ATR or 2.5% (whichever is tighter for quick exit)

    Target:
    - 2.5:1 risk:reward (momentum trades move fast)

    Best for: Daily swing trades (1-5 days hold), volatile stocks
    Hold Time: 1-5 days typically
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        Initialize Momentum Swing strategy

        Args:
            config: Strategy configuration parameters
        """
        super().__init__(config)

        # Momentum-specific parameters
        self.rsi_bullish_threshold = 60  # Above this for bullish momentum
        self.rsi_bearish_threshold = 40  # Below this for bearish momentum
        self.min_adx = 20  # Minimum trend strength
        self.volume_multiplier = 1.5  # Volume confirmation
        self.stop_loss_atr_multiplier = 1.5
        self.stop_loss_percent = 0.025  # 2.5%
        self.risk_reward_ratio = 2.5

    def get_name(self) -> str:
        return "MOMENTUM_SWING"

    def get_description(self) -> str:
        return "Captures strong daily momentum with multi-indicator confirmation and volume validation"

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate trade levels optimized for momentum swings

        Momentum trades need:
        - Tighter stops (momentum can reverse quickly)
        - Reasonable targets (2.5:1 R:R)
        - ATR-based stops (volatility-adjusted)

        Args:
            current_price: Current market price
            signal: Aggregated indicator signal
            action: Trade action (BUY/SHORT/SELL)

        Returns:
            Dictionary with entry, stop_loss, and target
        """
        atr_value = self._get_atr_value(signal)

        if action == "BUY":
            entry = current_price

            # Stop loss: Use tighter of ATR-based or percentage-based
            # Momentum can reverse quickly, so we want quick exits
            stop_pct = entry * (1 - self.stop_loss_percent)  # 2.5% stop

            if atr_value:
                stop_atr = entry - (atr_value * self.stop_loss_atr_multiplier)
                # Use tighter stop (higher value) for quick exit
                stop_loss = max(stop_pct, stop_atr)
            else:
                stop_loss = stop_pct

            # Target: 2.5x risk
            # Momentum moves fast, so take profits at reasonable levels
            risk = entry - stop_loss
            target = entry + (risk * self.risk_reward_ratio)

        elif action == "SHORT":
            entry = current_price

            # Stop loss: Tighter of ATR or percentage
            stop_pct = entry * (1 + self.stop_loss_percent)  # 2.5% stop

            if atr_value:
                stop_atr = entry + (atr_value * self.stop_loss_atr_multiplier)
                # Use tighter stop (lower value) for quick exit
                stop_loss = min(stop_pct, stop_atr)
            else:
                stop_loss = stop_pct

            # Target: 2.5x risk
            risk = stop_loss - entry
            target = entry - (risk * self.risk_reward_ratio)

        else:  # SELL (exit)
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
        Validate momentum conditions before entry

        Momentum strategy requires:
        1. Strong RSI momentum (>60 for BUY, <40 for SHORT)
        2. MACD confirmation
        3. Stochastic alignment
        4. ADX showing trend (not choppy)
        5. High confidence from signal aggregator

        Args:
            signal: Aggregated signal
            current_price: Current price
            **kwargs: Additional parameters (may include volume data)

        Returns:
            Tuple of (should_trade, reason)
        """
        # Base validation
        should_trade, reason = super().should_take_trade(signal, current_price, **kwargs)
        if not should_trade:
            return False, reason

        # Extract indicator values
        rsi_value = self._get_rsi_value(signal)
        adx_value = self._get_adx_value(signal)
        macd_histogram = self._get_macd_histogram(signal)
        stochastic_k = self._get_stochastic_k(signal)

        # Validate required indicators
        if rsi_value is None:
            return False, "RSI not available"

        if adx_value is None:
            return False, "ADX not available"

        # Check ADX for trend strength
        # Momentum strategy needs trending market, not choppy
        if adx_value < self.min_adx:
            return False, f"ADX {adx_value:.1f} < {self.min_adx} (market too choppy for momentum)"

        # Determine trade direction
        is_bullish = signal.bullish_signals > signal.bearish_signals
        is_bearish = signal.bearish_signals > signal.bullish_signals

        # Validate RSI momentum
        if is_bullish:
            # For bullish momentum: RSI should show strength (>60)
            # But not overbought (we use <85 as extreme)
            if rsi_value < self.rsi_bullish_threshold:
                return False, f"RSI {rsi_value:.1f} < {self.rsi_bullish_threshold} (insufficient bullish momentum)"

            if rsi_value > 85:
                return False, f"RSI {rsi_value:.1f} > 85 (extremely overbought, avoid)"

            # Validate MACD if available
            if macd_histogram is not None and macd_histogram < 0:
                return False, f"MACD histogram negative (momentum not confirmed)"

            # Validate Stochastic if available
            if stochastic_k is not None and stochastic_k < 50:
                return False, f"Stochastic %K {stochastic_k:.1f} < 50 (momentum not confirmed)"

        elif is_bearish:
            # For bearish momentum: RSI should show weakness (<40)
            # But not oversold (we use >15 as extreme)
            if rsi_value > self.rsi_bearish_threshold:
                return False, f"RSI {rsi_value:.1f} > {self.rsi_bearish_threshold} (insufficient bearish momentum)"

            if rsi_value < 15:
                return False, f"RSI {rsi_value:.1f} < 15 (extremely oversold, may bounce)"

            # Validate MACD if available
            if macd_histogram is not None and macd_histogram > 0:
                return False, f"MACD histogram positive (bearish momentum not confirmed)"

            # Validate Stochastic if available
            if stochastic_k is not None and stochastic_k > 50:
                return False, f"Stochastic %K {stochastic_k:.1f} > 50 (bearish momentum not confirmed)"

        # Require high confidence for momentum trades
        # Momentum can reverse quickly, so we want strong signals
        if signal.confidence < 65:
            return False, f"Confidence {signal.confidence:.0f}% < 65% (momentum needs high confidence)"

        # All momentum conditions met
        return True, f"Momentum confirmed (RSI: {rsi_value:.1f}, ADX: {adx_value:.1f}, Confidence: {signal.confidence:.0f}%)"

    def _get_atr_value(self, signal: AggregatedSignal) -> Optional[float]:
        """Extract ATR for volatility-based stops"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ATR' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_rsi_value(self, signal: AggregatedSignal) -> Optional[float]:
        """Extract RSI for momentum measurement"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'RSI' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_adx_value(self, signal: AggregatedSignal) -> Optional[float]:
        """Extract ADX for trend strength"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ADX' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_macd_histogram(self, signal: AggregatedSignal) -> Optional[float]:
        """
        Extract MACD histogram value

        MACD histogram = MACD line - Signal line
        Positive: Bullish momentum
        Negative: Bearish momentum
        """
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'MACD' in ind_name.upper():
                # MACD current value is typically the histogram or line value
                return ind_signal.current_value
        return None

    def _get_stochastic_k(self, signal: AggregatedSignal) -> Optional[float]:
        """
        Extract Stochastic %K value

        %K > 50: Bullish momentum
        %K < 50: Bearish momentum
        """
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'STOCH' in ind_name.upper():
                return ind_signal.current_value
        return None
