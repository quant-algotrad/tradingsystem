"""
Multi-Indicator Trading Strategy
Uses weighted combination of multiple technical indicators

This is the default strategy that was previously hardcoded in TradeDecisionEngine
"""

from typing import Dict
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.strategy.signal_aggregator import AggregatedSignal
from src.indicators.models import SignalValue


class MultiIndicatorStrategy(TradingStrategy):
    """
    Multi-Indicator Strategy

    Logic:
    - Aggregates signals from RSI, MACD, Bollinger Bands, ADX, Stochastic
    - Uses weighted voting for decision
    - ATR-based stop loss calculation
    - 1:3 risk:reward ratio for targets
    """

    def get_name(self) -> str:
        return "MULTI_INDICATOR"

    def get_description(self) -> str:
        return "Combines multiple technical indicators with weighted voting"

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate entry, stop loss, and target using ATR-based stops

        Uses:
        - Entry: Current market price
        - Stop Loss: 1.5x ATR or 2% (whichever is available)
        - Target: 3x risk (1:3 risk:reward ratio)
        """
        # Extract ATR value if available
        atr_value = self._get_atr_value(signal)

        if action == "BUY":
            entry = current_price

            # Stop loss: 1.5x ATR or 2% below entry
            if atr_value:
                stop_loss = entry - (atr_value * 1.5)
            else:
                stop_loss = entry * 0.98  # 2% stop

            # Target: 3x risk
            risk = entry - stop_loss
            target = entry + (risk * 3.0)

        elif action == "SHORT":
            entry = current_price

            # Stop loss: 1.5x ATR or 2% above entry
            if atr_value:
                stop_loss = entry + (atr_value * 1.5)
            else:
                stop_loss = entry * 1.02  # 2% stop

            # Target: 3x risk
            risk = stop_loss - entry
            target = entry - (risk * 3.0)

        else:  # SELL (close long)
            entry = current_price
            stop_loss = current_price
            target = current_price

        return {
            'entry': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2)
        }

    def _get_atr_value(self, signal: AggregatedSignal) -> float:
        """Extract ATR value from indicator signals"""
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
        Multi-indicator specific trade validation

        Checks:
        1. Confidence threshold (60%)
        2. No conflicting signals
        3. Minimum consensus
        """
        # Check base confidence
        should_trade, reason = super().should_take_trade(signal, current_price, **kwargs)
        if not should_trade:
            return False, reason

        # Check for conflicting signals (unique to multi-indicator)
        if signal.bullish_signals > 0 and signal.bearish_signals > 0:
            # Too much disagreement
            if abs(signal.bullish_signals - signal.bearish_signals) <= 1:
                return False, "Mixed signals - indicators disagree"

        # Check minimum consensus
        consensus = signal.get_consensus_strength()
        if consensus < 60:
            return False, f"Low consensus ({consensus:.0f}%) - indicators not aligned"

        return True, "Multi-indicator criteria met"
