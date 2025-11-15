"""
Base Trading Strategy Interface
Defines the contract for all trading strategies

Pattern: Strategy Pattern
- All strategies implement this interface
- Allows easy swapping of strategies
- Each strategy can have different logic
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass

from src.strategy.signal_aggregator import AggregatedSignal
from src.strategy.decision_engine import TradeRecommendation


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy"""
    name: str
    description: str
    min_confidence: float = 60.0  # Minimum signal confidence to trade
    min_risk_reward: float = 1.5  # Minimum risk:reward ratio
    position_sizing_method: str = "FIXED_RISK"  # FIXED_RISK, FIXED_SIZE, KELLY
    risk_per_trade_percent: float = 1.0  # % of capital to risk per trade

    # Strategy-specific parameters (each strategy can define its own)
    params: Dict[str, Any] = None

    def __post_init__(self):
        if self.params is None:
            self.params = {}


class TradingStrategy(ABC):
    """
    Abstract base class for all trading strategies

    Pattern: Strategy Pattern
    - Defines common interface for all strategies
    - Allows runtime strategy switching
    - Each strategy implements its own logic

    To create a new strategy:
    1. Inherit from this class
    2. Implement calculate_trade_levels()
    3. Optionally override should_take_trade()
    4. Register in StrategyFactory
    """

    def __init__(self, config: StrategyConfig = None):
        """
        Initialize strategy

        Args:
            config: Strategy configuration
        """
        self.config = config or StrategyConfig(
            name=self.get_name(),
            description=self.get_description()
        )

    @abstractmethod
    def get_name(self) -> str:
        """Return strategy name (e.g., 'MULTI_INDICATOR')"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return strategy description"""
        pass

    @abstractmethod
    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate entry, stop loss, and target levels

        Args:
            current_price: Current market price
            signal: Aggregated signal from indicators
            action: Trade action (BUY, SELL, SHORT, etc.)

        Returns:
            Dict with 'entry', 'stop_loss', 'target' keys
        """
        pass

    def should_take_trade(
        self,
        signal: AggregatedSignal,
        current_price: float,
        **kwargs
    ) -> tuple[bool, str]:
        """
        Determine if strategy should take the trade

        Can be overridden by specific strategies for custom logic

        Args:
            signal: Aggregated signal
            current_price: Current price
            **kwargs: Additional context

        Returns:
            (should_trade: bool, reason: str)
        """
        # Default implementation - check confidence
        if signal.confidence < self.config.min_confidence:
            return False, f"Confidence {signal.confidence:.0f}% < {self.config.min_confidence}%"

        return True, "Signal meets criteria"

    def get_config(self) -> StrategyConfig:
        """Get strategy configuration"""
        return self.config

    def update_config(self, **kwargs):
        """
        Update strategy configuration

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                # Add to params dict
                self.config.params[key] = value
