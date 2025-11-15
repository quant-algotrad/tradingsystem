"""
Strategy Module
Trading strategies, signal aggregation, and trade decision logic

Components:
- Signal Aggregation: Combine multiple indicator signals
- Multi-timeframe Analysis: Cross-timeframe confirmation
- Trade Decision Engine: Convert signals to actionable trades

Patterns:
- Composite Pattern: Multi-indicator aggregation
- Strategy Pattern: Different trading strategies
- Chain of Responsibility: Multi-timeframe filtering
"""

from .signal_aggregator import (
    AggregatedSignal,
    SignalAggregator,
    MultiTimeframeAggregator,
    get_aggregated_signal
)

from .decision_engine import (
    TradeAction,
    TradeRecommendation,
    TradeDecision,
    TradeDecisionEngine,
    RejectionReason,
    get_trade_decision_engine,
    evaluate_trade_opportunity
)

__all__ = [
    # Signal Aggregation
    'AggregatedSignal',
    'SignalAggregator',
    'MultiTimeframeAggregator',
    'get_aggregated_signal',

    # Trade Decision
    'TradeAction',
    'TradeRecommendation',
    'TradeDecision',
    'TradeDecisionEngine',
    'RejectionReason',
    'get_trade_decision_engine',
    'evaluate_trade_opportunity'
]

__version__ = '1.0.0'
