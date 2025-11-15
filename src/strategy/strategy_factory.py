"""
Strategy Factory
Creates and manages trading strategy instances

Pattern: Factory Pattern + Registry Pattern
- Centralized strategy creation
- Auto-registration of strategies
- Easy to add new strategies
"""

from typing import Dict, Optional, List
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.utils import get_logger

logger = get_logger(__name__)


class StrategyFactory:
    """
    Factory for creating trading strategy instances

    Pattern: Factory Pattern + Registry Pattern

    Usage:
        # Register a strategy
        StrategyFactory.register('MULTI_INDICATOR', MultiIndicatorStrategy)

        # Create strategy instance
        strategy = StrategyFactory.create('MULTI_INDICATOR')

        # List available strategies
        strategies = StrategyFactory.get_available_strategies()
    """

    # Registry of available strategies
    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, strategy_class: type):
        """
        Register a new strategy

        Args:
            name: Strategy name (e.g., 'MULTI_INDICATOR')
            strategy_class: Strategy class (must inherit from TradingStrategy)
        """
        if not issubclass(strategy_class, TradingStrategy):
            raise TypeError(
                f"Strategy {strategy_class.__name__} must inherit from TradingStrategy"
            )

        cls._registry[name.upper()] = strategy_class
        logger.info(f"Registered strategy: {name}")

    @classmethod
    def create(
        cls,
        name: str,
        config: Optional[StrategyConfig] = None
    ) -> Optional[TradingStrategy]:
        """
        Create strategy instance

        Args:
            name: Strategy name
            config: Optional strategy configuration

        Returns:
            TradingStrategy instance or None if not found
        """
        name_upper = name.upper()

        if name_upper not in cls._registry:
            available = ", ".join(cls._registry.keys())
            logger.error(
                f"Strategy '{name}' not found. Available: {available}"
            )
            return None

        strategy_class = cls._registry[name_upper]

        try:
            if config:
                return strategy_class(config)
            else:
                return strategy_class()
        except Exception as e:
            logger.error(f"Failed to create strategy '{name}': {e}")
            return None

    @classmethod
    def get_available_strategies(cls) -> List[Dict[str, str]]:
        """
        Get list of available strategies with descriptions

        Returns:
            List of dicts with 'name' and 'description' keys
        """
        strategies = []

        for name, strategy_class in cls._registry.items():
            try:
                # Create temporary instance to get description
                temp_instance = strategy_class()
                strategies.append({
                    'name': name,
                    'description': temp_instance.get_description()
                })
            except Exception as e:
                logger.error(f"Error getting info for {name}: {e}")
                strategies.append({
                    'name': name,
                    'description': 'Description unavailable'
                })

        return strategies

    @classmethod
    def exists(cls, name: str) -> bool:
        """Check if strategy exists"""
        return name.upper() in cls._registry


# ========================================
# Auto-register built-in strategies
# ========================================

def _register_built_in_strategies():
    """
    Register all built-in strategies

    To add a new strategy:
    1. Create the strategy class in src/strategy/strategies/
    2. Import it here
    3. Call StrategyFactory.register(name, StrategyClass)
    """
    from src.strategy.strategies import (
        MultiIndicatorStrategy,
        MeanReversionStrategy,
        BreakoutStrategy
    )

    # Register all strategies
    StrategyFactory.register('MULTI_INDICATOR', MultiIndicatorStrategy)
    StrategyFactory.register('DEFAULT', MultiIndicatorStrategy)  # Default alias

    StrategyFactory.register('MEAN_REVERSION', MeanReversionStrategy)
    StrategyFactory.register('BREAKOUT', BreakoutStrategy)

    logger.info(f"Registered {len(StrategyFactory._registry)} built-in strategies")


# Auto-register on import
_register_built_in_strategies()
