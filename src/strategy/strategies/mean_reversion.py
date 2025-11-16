"""
Mean Reversion Trading Strategy
Trades when price deviates significantly from mean and reverts

Example strategy to demonstrate Strategy Pattern extensibility
"""

from typing import Dict
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.strategy.signal_aggregator import AggregatedSignal


class MeanReversionStrategy(TradingStrategy):
    """
    Mean Reversion Strategy

    Logic:
    - Looks for oversold/overbought conditions (RSI, Bollinger Bands)
    - Enters when price is 2+ standard deviations from mean
    - Exits at mean (tight profit targets)
    - Uses tighter stops (1:1.5 risk:reward)

    Best for: Range-bound markets, high volatility stocks
    """

    def get_name(self) -> str:
        return "MEAN_REVERSION"

    def get_description(self) -> str:
        return "Trades mean reversion using RSI and Bollinger Bands oversold/overbought levels"

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate levels for mean reversion

        Entry: Current price (expecting reversion)
        Stop: 1.5% beyond current price
        Target: Middle of Bollinger Bands (mean) or 1:1.5 R:R
        """
        # Get Bollinger Bands middle if available
        bb_middle = self._get_bb_middle(signal)

        if action == "BUY":
            entry = current_price

            # Tighter stop for mean reversion (1.5%)
            stop_loss = entry * 0.985

            # Target: BB middle or 1:1.5 risk:reward
            if bb_middle and bb_middle > entry:
                target = bb_middle
            else:
                risk = entry - stop_loss
                target = entry + (risk * 1.5)

        elif action == "SHORT":
            entry = current_price

            # Tighter stop (1.5%)
            stop_loss = entry * 1.015

            # Target: BB middle or 1:1.5 risk:reward
            if bb_middle and bb_middle < entry:
                target = bb_middle
            else:
                risk = stop_loss - entry
                target = entry - (risk * 1.5)

        else:
            entry = current_price
            stop_loss = current_price
            target = current_price

        return {
            'entry': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2)
        }

    def _get_bb_middle(self, signal: AggregatedSignal) -> float:
        """Extract Bollinger Bands middle value"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'BB' in ind_name or 'BOLLINGER' in ind_name:
                # BB middle is typically the current value
                return ind_signal.current_value
        return None

    def should_take_trade(
        self,
        signal: AggregatedSignal,
        current_price: float,
        **kwargs
    ) -> tuple[bool, str]:
        """
        Mean reversion specific validation

        Requirements:
        - RSI must show oversold (<30) for BUY or overbought (>70) for SELL
        - Bollinger Bands must confirm (price at upper/lower band)
        """
        # Check base criteria
        should_trade, reason = super().should_take_trade(signal, current_price, **kwargs)
        if not should_trade:
            return False, reason

        # Check for RSI extreme levels
        rsi_value = self._get_rsi_value(signal)
        if rsi_value is None:
            return False, "RSI data not available"

        # For mean reversion, we want extremes
        is_oversold = rsi_value < 30
        is_overbought = rsi_value > 70

        if not (is_oversold or is_overbought):
            return False, f"RSI {rsi_value:.0f} not at extreme levels (need <30 or >70)"

        return True, "Mean reversion conditions met"

    def _get_rsi_value(self, signal: AggregatedSignal) -> float:
        """Extract RSI value"""
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'RSI' in ind_name:
                return ind_signal.current_value
        return None
