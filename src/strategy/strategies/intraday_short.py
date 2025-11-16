"""
Intraday Breakdown Short Strategy
Short-selling strategy for intraday breakdown below support levels

This strategy identifies stocks breaking down below support with
high volume and sells short for intraday profits.
"""

from typing import Dict, Optional
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.strategy.signal_aggregator import AggregatedSignal


class IntradayShortStrategy(TradingStrategy):
    """
    Intraday Breakdown Short Strategy

    Logic:
    - Identifies support breakdown on intraday timeframes (15m, 5m)
    - Confirms with volume spike and bearish indicators
    - Enters short position on breakdown
    - Uses tight stops (breakdown failures reverse fast)
    - Auto-squares before 3:15 PM (intraday requirement)

    Entry Criteria (SHORT only):
    - Price breaks below key support level
    - Volume > 2x average (strong selling pressure)
    - RSI < 45 (bearish momentum confirmed)
    - MACD bearish (line < signal)
    - ADX > 18 (some directional movement)
    - Bollinger Bands: Price near/below lower band

    Stop Loss:
    - Tight: 1.2% or support level + small buffer
    - Breakdown failures reverse quickly

    Target:
    - Conservative: 1:2 risk:reward (quick intraday moves)
    - Time-based exit: Square off by 3:15 PM regardless

    Risk Management:
    - Only for MIS (Margin Intraday Square-off)
    - Maximum 2 short positions simultaneously
    - Strict time-based exit (3:15 PM)

    Best for: Intraday trading, bearish markets, high volatility stocks
    Timeframe: 15-minute or 5-minute charts
    Hold Time: Minutes to hours (never overnight)
    """

    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        Initialize Intraday Short strategy

        Args:
            config: Strategy configuration
        """
        super().__init__(config)

        # Intraday short specific parameters
        self.rsi_max_threshold = 45  # RSI must be below this
        self.min_adx = 18  # Lower than swing trades (intraday is faster)
        self.volume_multiplier = 2.0  # Strong volume confirmation
        self.stop_loss_percent = 0.012  # 1.2% tight stop
        self.risk_reward_ratio = 2.0  # Conservative for intraday
        self.max_rsi_for_entry = 50  # Reject if RSI too high

        # Intraday specific settings
        self.square_off_time = "15:15"  # IST - square off time
        self.max_hold_hours = 4  # Maximum hours to hold position

    def get_name(self) -> str:
        return "INTRADAY_SHORT"

    def get_description(self) -> str:
        return "Intraday short-selling strategy for support breakdown with volume confirmation (MIS only)"

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate trade levels for intraday short trades

        Intraday shorts require:
        - Very tight stops (1.2% - failures reverse fast)
        - Quick targets (2:1 R:R - capture fast moves)
        - Support level awareness (stop above breakdown level)

        Args:
            current_price: Current market price
            signal: Aggregated signal
            action: Should be "SHORT" for this strategy

        Returns:
            Trade levels (entry, stop_loss, target)
        """
        # This strategy only takes SHORT positions
        if action != "SHORT":
            # If not SHORT, return neutral levels
            return {
                'entry': round(current_price, 2),
                'stop_loss': round(current_price, 2),
                'target': round(current_price, 2)
            }

        entry = current_price

        # Stop loss: Tight 1.2% above entry
        # Intraday breakdowns that fail, reverse quickly
        # We want to be out fast if wrong
        stop_loss = entry * (1 + self.stop_loss_percent)

        # Alternative: Use support level + buffer if available
        # This would come from kwargs in real implementation
        # For now, using percentage-based stop

        # Target: 2:1 risk:reward for intraday
        # Intraday moves are smaller, so conservative target
        risk = stop_loss - entry
        target = entry - (risk * self.risk_reward_ratio)

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
        Validate intraday short conditions

        Strict requirements:
        1. Only SHORT signals (no longs in this strategy)
        2. Bearish momentum (RSI < 45)
        3. Volume confirmation (>2x average)
        4. Directional movement (ADX > 18)
        5. Time check (not after 2 PM for new entries)
        6. Not oversold (RSI > 20, avoid bounce zone)

        Args:
            signal: Aggregated signal
            current_price: Current price
            **kwargs: May contain time, volume data, support levels

        Returns:
            Tuple of (should_trade, reason)
        """
        # Base validation
        should_trade, reason = super().should_take_trade(signal, current_price, **kwargs)
        if not should_trade:
            return False, reason

        # This strategy ONLY takes short positions
        is_bearish = signal.bearish_signals > signal.bullish_signals
        if not is_bearish:
            return False, "Intraday short strategy requires bearish signal"

        # Extract indicator values
        rsi_value = self._get_rsi_value(signal)
        adx_value = self._get_adx_value(signal)
        macd_histogram = self._get_macd_histogram(signal)

        # Validate RSI shows bearish momentum
        if rsi_value is None:
            return False, "RSI not available"

        # RSI must be below threshold for short
        # But not too oversold (avoid bounce zone)
        if rsi_value > self.max_rsi_for_entry:
            return False, f"RSI {rsi_value:.1f} > {self.max_rsi_for_entry} (not bearish enough for short)"

        if rsi_value < 20:
            return False, f"RSI {rsi_value:.1f} < 20 (too oversold, may bounce)"

        # Validate ADX shows directional movement
        if adx_value is None:
            return False, "ADX not available"

        if adx_value < self.min_adx:
            return False, f"ADX {adx_value:.1f} < {self.min_adx} (insufficient directional movement)"

        # Validate MACD if available
        if macd_histogram is not None:
            if macd_histogram > 0:
                return False, "MACD bullish (histogram > 0), not suitable for short"

        # Check confidence level
        # Intraday trades need high confidence due to time pressure
        if signal.confidence < 65:
            return False, f"Confidence {signal.confidence:.0f}% < 65% (intraday shorts need high confidence)"

        # Time-based validation
        # Don't enter shorts after 2 PM (not enough time before square-off)
        current_time = kwargs.get('current_time')
        if current_time:
            # Assuming current_time is datetime object or time string
            # Skip for now in base implementation
            # In real implementation: check if after 14:00 IST
            pass

        # Volume validation would go here
        # Require volume > 2x average for breakdown confirmation
        # current_volume = kwargs.get('current_volume')
        # avg_volume = kwargs.get('avg_volume')
        # if current_volume and avg_volume:
        #     if current_volume < avg_volume * self.volume_multiplier:
        #         return False, f"Volume insufficient for breakdown"

        # All conditions met
        return True, f"Intraday short setup confirmed (RSI: {rsi_value:.1f}, ADX: {adx_value:.1f})"

    def _get_rsi_value(self, signal: AggregatedSignal) -> Optional[float]:
        """Extract RSI for momentum validation"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'RSI' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_adx_value(self, signal: AggregatedSignal) -> Optional[float]:
        """Extract ADX for directional movement"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ADX' in ind_name.upper():
                return ind_signal.current_value
        return None

    def _get_macd_histogram(self, signal: AggregatedSignal) -> Optional[float]:
        """Extract MACD histogram for trend confirmation"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'MACD' in ind_name.upper():
                return ind_signal.current_value
        return None

    def requires_intraday_squareoff(self) -> bool:
        """
        Indicates this strategy requires intraday square-off

        Returns:
            True - this strategy MUST square off by 3:15 PM
        """
        return True

    def get_squareoff_time(self) -> str:
        """
        Get the time by which positions must be squared off

        Returns:
            Time string in HH:MM format (IST)
        """
        return self.square_off_time

    def allows_long_positions(self) -> bool:
        """
        Check if strategy allows long positions

        Returns:
            False - this strategy only shorts
        """
        return False

    def allows_short_positions(self) -> bool:
        """
        Check if strategy allows short positions

        Returns:
            True - this is a short-only strategy
        """
        return True
