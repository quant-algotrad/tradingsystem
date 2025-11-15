"""
Breakout Trading Strategy
Trades breakouts above resistance or below support

Example strategy to demonstrate Strategy Pattern extensibility
"""

from typing import Dict
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.strategy.signal_aggregator import AggregatedSignal


class BreakoutStrategy(TradingStrategy):
    """
    Breakout Strategy

    Logic:
    - Identifies strong directional moves (ADX > 25)
    - Enters on breakout confirmation from multiple indicators
    - Wider stops to avoid premature exit (3% stop)
    - Aggressive targets (1:4 risk:reward)

    Best for: Trending markets, momentum stocks
    """

    def get_name(self) -> str:
        return "BREAKOUT"

    def get_description(self) -> str:
        return "Trades breakouts with strong directional momentum (ADX-based)"

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate levels for breakout

        Entry: Current price (breakout point)
        Stop: Wider stop (3%) to allow consolidation
        Target: Aggressive 1:4 risk:reward
        """
        # Get ATR for dynamic stops
        atr_value = self._get_atr_value(signal)

        if action == "BUY":
            entry = current_price

            # Wider stop for breakout (3% or 2x ATR)
            if atr_value:
                stop_loss = entry - (atr_value * 2.0)
            else:
                stop_loss = entry * 0.97  # 3% stop

            # Aggressive target: 4x risk
            risk = entry - stop_loss
            target = entry + (risk * 4.0)

        elif action == "SHORT":
            entry = current_price

            # Wider stop (3% or 2x ATR)
            if atr_value:
                stop_loss = entry + (atr_value * 2.0)
            else:
                stop_loss = entry * 1.03  # 3% stop

            # Aggressive target: 4x risk
            risk = stop_loss - entry
            target = entry - (risk * 4.0)

        else:
            entry = current_price
            stop_loss = current_price
            target = current_price

        return {
            'entry': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2)
        }

    def _get_atr_value(self, signal: AggregatedSignal) -> float:
        """Extract ATR value"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ATR' in ind_name:
                return ind_signal.current_value
        return None

    def should_take_trade(
        self,
        signal: AggregatedSignal,
        current_price: float,
        **kwargs
    ) -> tuple[bool, str]:
        """
        Breakout specific validation

        Requirements:
        - ADX > 25 (strong trend)
        - High confidence (>70%)
        - Strong consensus (all indicators agree)
        """
        # Check base criteria
        should_trade, reason = super().should_take_trade(signal, current_price, **kwargs)
        if not should_trade:
            return False, reason

        # Breakout requires higher confidence
        if signal.confidence < 70:
            return False, f"Confidence {signal.confidence:.0f}% < 70% (breakout needs high confidence)"

        # Check ADX for trend strength
        adx_value = self._get_adx_value(signal)
        if adx_value is not None:
            if adx_value < 25:
                return False, f"ADX {adx_value:.0f} < 25 (weak trend, not suitable for breakout)"

        # Check for strong consensus
        consensus = signal.get_consensus_strength()
        if consensus < 80:
            return False, f"Consensus {consensus:.0f}% < 80% (breakout needs strong agreement)"

        return True, "Breakout conditions met"

    def _get_adx_value(self, signal: AggregatedSignal) -> float:
        """Extract ADX value"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ADX' in ind_name:
                return ind_signal.current_value
        return None
