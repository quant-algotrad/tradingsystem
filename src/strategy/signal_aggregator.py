"""
Signal Aggregation Engine
Combines multiple indicator signals into unified trading signals

Pattern: Strategy Pattern + Composite Pattern
- Aggregates signals from multiple sources
- Weights indicators based on reliability
- Provides consensus scoring
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from src.indicators import (
    calculate_indicators,
    IndicatorSignal,
    SignalValue
)
from src.utils import get_logger

logger = get_logger(__name__)


@dataclass
class AggregatedSignal:
    """
    Aggregated trading signal from multiple indicators

    Contains consensus decision and supporting evidence
    """
    symbol: str
    timestamp: datetime

    # Final decision
    signal: SignalValue  # BUY, SELL, NEUTRAL
    confidence: float  # 0-100

    # Supporting data
    bullish_signals: int = 0
    bearish_signals: int = 0
    neutral_signals: int = 0

    # Individual indicator signals
    indicator_signals: Dict[str, IndicatorSignal] = field(default_factory=dict)

    # Scores
    bullish_score: float = 0.0  # Weighted bullish score
    bearish_score: float = 0.0  # Weighted bearish score

    # Reasoning
    reasons: List[str] = field(default_factory=list)

    def get_signal_distribution(self) -> Dict[str, int]:
        """Get distribution of signals"""
        return {
            'bullish': self.bullish_signals,
            'bearish': self.bearish_signals,
            'neutral': self.neutral_signals
        }

    def get_consensus_strength(self) -> float:
        """
        Calculate consensus strength

        Returns:
            Strength of consensus (0-100)
        """
        total = self.bullish_signals + self.bearish_signals + self.neutral_signals
        if total == 0:
            return 0.0

        # Higher consensus when signals agree
        max_agreement = max(self.bullish_signals, self.bearish_signals)
        return (max_agreement / total) * 100.0


class SignalAggregator:
    """
    Aggregates signals from multiple technical indicators

    Pattern: Composite Pattern
    - Combines multiple signals into one
    - Weighted voting system
    - Configurable indicator weights
    """

    def __init__(self, indicator_weights: Optional[Dict[str, float]] = None):
        """
        Initialize aggregator

        Args:
            indicator_weights: Dict of indicator name -> weight (0-1)
        """
        # Default weights (based on reliability)
        self.indicator_weights = indicator_weights or {
            'RSI': 0.25,
            'MACD': 0.25,
            'BB': 0.20,  # Bollinger Bands
            'ADX': 0.15,
            'STOCH': 0.10,  # Stochastic
            'ATR': 0.05,  # Volatility context only
        }

        # Normalize weights to sum to 1.0
        total_weight = sum(self.indicator_weights.values())
        if total_weight > 0:
            self.indicator_weights = {
                k: v / total_weight
                for k, v in self.indicator_weights.items()
            }

        logger.info(f"Signal aggregator initialized with weights: {self.indicator_weights}")

    def aggregate_signals(
        self,
        symbol: str,
        indicator_signals: Dict[str, IndicatorSignal]
    ) -> AggregatedSignal:
        """
        Aggregate multiple indicator signals

        Args:
            symbol: Stock symbol
            indicator_signals: Dict of indicator_name -> IndicatorSignal

        Returns:
            AggregatedSignal with consensus decision
        """
        timestamp = datetime.now()

        # Count signals
        bullish = 0
        bearish = 0
        neutral = 0

        # Weighted scores
        bullish_score = 0.0
        bearish_score = 0.0

        # Reasoning
        reasons = []

        for ind_name, signal in indicator_signals.items():
            # Get weight for this indicator
            weight = self._get_indicator_weight(ind_name)

            if signal.signal == SignalValue.BUY or signal.signal == SignalValue.STRONG_BUY:
                bullish += 1
                bullish_score += weight * (signal.strength / 100.0)
                reasons.append(f"{ind_name}: BUY (strength: {signal.strength:.0f})")

            elif signal.signal == SignalValue.SELL or signal.signal == SignalValue.STRONG_SELL:
                bearish += 1
                bearish_score += weight * (signal.strength / 100.0)
                reasons.append(f"{ind_name}: SELL (strength: {signal.strength:.0f})")

            else:
                neutral += 1
                reasons.append(f"{ind_name}: NEUTRAL")

        # Determine final signal based on weighted scores
        final_signal, confidence = self._determine_final_signal(
            bullish_score, bearish_score, bullish, bearish, neutral
        )

        return AggregatedSignal(
            symbol=symbol,
            timestamp=timestamp,
            signal=final_signal,
            confidence=confidence,
            bullish_signals=bullish,
            bearish_signals=bearish,
            neutral_signals=neutral,
            indicator_signals=indicator_signals,
            bullish_score=bullish_score,
            bearish_score=bearish_score,
            reasons=reasons
        )

    def _get_indicator_weight(self, indicator_name: str) -> float:
        """Get weight for indicator (handle different naming)"""
        # Try exact match
        if indicator_name in self.indicator_weights:
            return self.indicator_weights[indicator_name]

        # Try partial match (e.g., "RSI_14" -> "RSI")
        for key in self.indicator_weights:
            if indicator_name.startswith(key):
                return self.indicator_weights[key]

        # Default weight
        return 0.1

    def _determine_final_signal(
        self,
        bullish_score: float,
        bearish_score: float,
        bullish_count: int,
        bearish_count: int,
        neutral_count: int
    ) -> tuple[SignalValue, float]:
        """
        Determine final signal and confidence

        Args:
            bullish_score: Weighted bullish score
            bearish_score: Weighted bearish score
            bullish_count: Number of bullish signals
            bearish_count: Number of bearish signals
            neutral_count: Number of neutral signals

        Returns:
            (final_signal, confidence)
        """
        total_count = bullish_count + bearish_count + neutral_count

        if total_count == 0:
            return SignalValue.NEUTRAL, 0.0

        # Calculate confidence based on agreement
        if bullish_score > bearish_score:
            # Bullish signal
            score_diff = bullish_score - bearish_score
            agreement_ratio = bullish_count / total_count

            # Confidence is combination of score difference and agreement
            confidence = min(100, (score_diff * 100) + (agreement_ratio * 50))

            if confidence >= 70:
                return SignalValue.STRONG_BUY, confidence
            else:
                return SignalValue.BUY, confidence

        elif bearish_score > bullish_score:
            # Bearish signal
            score_diff = bearish_score - bullish_score
            agreement_ratio = bearish_count / total_count

            confidence = min(100, (score_diff * 100) + (agreement_ratio * 50))

            if confidence >= 70:
                return SignalValue.STRONG_SELL, confidence
            else:
                return SignalValue.SELL, confidence

        else:
            # Neutral (scores equal)
            return SignalValue.NEUTRAL, 50.0


class MultiTimeframeAggregator:
    """
    Aggregates signals across multiple timeframes

    Pattern: Composite Pattern
    - Higher timeframes have more weight
    - Ensures alignment across timeframes
    """

    def __init__(self):
        """Initialize multi-timeframe aggregator"""
        # Timeframe weights (higher timeframes = more weight)
        self.timeframe_weights = {
            '1d': 0.40,   # Daily trend most important
            '1h': 0.30,   # Hour provides direction
            '15m': 0.20,  # 15min for entry timing
            '5m': 0.10,   # 5min for fine-tuning
        }

    def aggregate_timeframes(
        self,
        symbol: str,
        timeframe_signals: Dict[str, AggregatedSignal]
    ) -> AggregatedSignal:
        """
        Aggregate signals across timeframes

        Args:
            symbol: Stock symbol
            timeframe_signals: Dict of timeframe -> AggregatedSignal

        Returns:
            Combined AggregatedSignal
        """
        if not timeframe_signals:
            return AggregatedSignal(
                symbol=symbol,
                timestamp=datetime.now(),
                signal=SignalValue.NEUTRAL,
                confidence=0.0
            )

        # Calculate weighted scores
        total_bullish_score = 0.0
        total_bearish_score = 0.0
        total_weight = 0.0

        reasons = []

        for timeframe, signal in timeframe_signals.items():
            weight = self.timeframe_weights.get(timeframe, 0.1)
            total_weight += weight

            if signal.signal in [SignalValue.BUY, SignalValue.STRONG_BUY]:
                total_bullish_score += weight * (signal.confidence / 100.0)
                reasons.append(f"{timeframe}: BUY ({signal.confidence:.0f}%)")

            elif signal.signal in [SignalValue.SELL, SignalValue.STRONG_SELL]:
                total_bearish_score += weight * (signal.confidence / 100.0)
                reasons.append(f"{timeframe}: SELL ({signal.confidence:.0f}%)")

            else:
                reasons.append(f"{timeframe}: NEUTRAL")

        # Normalize scores
        if total_weight > 0:
            total_bullish_score /= total_weight
            total_bearish_score /= total_weight

        # Determine final signal
        if total_bullish_score > total_bearish_score:
            diff = total_bullish_score - total_bearish_score
            confidence = min(100, diff * 150)  # Scale to 0-100
            signal = SignalValue.STRONG_BUY if confidence >= 70 else SignalValue.BUY

        elif total_bearish_score > total_bullish_score:
            diff = total_bearish_score - total_bullish_score
            confidence = min(100, diff * 150)
            signal = SignalValue.STRONG_SELL if confidence >= 70 else SignalValue.SELL

        else:
            signal = SignalValue.NEUTRAL
            confidence = 50.0

        return AggregatedSignal(
            symbol=symbol,
            timestamp=datetime.now(),
            signal=signal,
            confidence=confidence,
            reasons=reasons
        )


# ========================================
# Convenience Functions
# ========================================

def get_aggregated_signal(
    symbol: str,
    data: pd.DataFrame,
    indicators: List[str] = None
) -> AggregatedSignal:
    """
    Convenience function to get aggregated signal

    Args:
        symbol: Stock symbol
        data: OHLCV DataFrame
        indicators: List of indicators to use (default: all)

    Returns:
        AggregatedSignal
    """
    if indicators is None:
        indicators = ['rsi', 'macd', 'bb', 'adx', 'stochastic']

    # Import indicator factory
    from src.indicators import IndicatorFactory

    # Calculate all indicators and get their signals
    results = calculate_indicators(indicators, data, symbol)

    # Get signals from each indicator using proper interpret_signal method
    indicator_signals = {}

    for ind_name in indicators:
        try:
            # Create indicator instance
            indicator = IndicatorFactory.create(ind_name)
            if indicator is None:
                continue

            # Get the result for this indicator
            ind_result = results.indicators.get(indicator.get_name())
            if ind_result is None:
                continue

            # Use the indicator's interpret_signal method
            signal = indicator.interpret_signal(ind_result)
            indicator_signals[indicator.get_name()] = signal

        except Exception as e:
            logger.error(f"Failed to get signal from {ind_name}: {e}")
            continue

    # Aggregate signals
    aggregator = SignalAggregator()
    return aggregator.aggregate_signals(symbol, indicator_signals)
