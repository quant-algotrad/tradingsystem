"""
Strategy Module
Trading strategies, signal aggregation, and trade decision logic

Components:
- Signal Aggregation: Combine multiple indicator signals
- Multi-timeframe Analysis: Cross-timeframe confirmation
- Trade Decision Engine: Convert signals to actionable trades
- Strategy Pattern: Pluggable trading strategies (NEW!)

Patterns:
- Composite Pattern: Multi-indicator aggregation
- Strategy Pattern: Different trading strategies
- Factory Pattern: Strategy creation and management
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

from .base_strategy import (
    TradingStrategy,
    StrategyConfig
)

from .strategy_factory import (
    StrategyFactory
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
    'evaluate_trade_opportunity',

    # Strategy Pattern (NEW)
    'TradingStrategy',
    'StrategyConfig',
    'StrategyFactory',
]

__version__ = '2.0.0'  # Bumped for Strategy Pattern implementation
