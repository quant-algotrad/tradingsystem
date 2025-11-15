# How to Add a New Trading Strategy

This guide shows you how to add a custom trading strategy to the system. It's as simple as creating **ONE file** and adding **TWO lines** of code!

## Overview

The system now uses the **Strategy Pattern** with a **Factory**. This means:
- ✅ Each strategy is a separate, self-contained class
- ✅ No need to modify existing code
- ✅ Strategies auto-register on startup
- ✅ Switch strategies from the dashboard

---

## 3 Steps to Add a New Strategy

### Step 1: Create Your Strategy File

Create a new file in `src/strategy/strategies/` (e.g., `scalping.py`)

```python
"""
Scalping Strategy
Quick in-and-out trades for small profits
"""

from typing import Dict
from src.strategy.base_strategy import TradingStrategy, StrategyConfig
from src.strategy.signal_aggregator import AggregatedSignal


class ScalpingStrategy(TradingStrategy):
    """
    Scalping Strategy

    Logic:
    - Very tight stops (0.5%)
    - Quick targets (1:1 risk:reward)
    - High frequency, small profits
    - Requires very high confidence (>80%)
    """

    def get_name(self) -> str:
        return "SCALPING"

    def get_description(self) -> str:
        return "High-frequency scalping with tight stops and quick profits"

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate ultra-tight levels for scalping

        Entry: Current price
        Stop: 0.5% (very tight)
        Target: 0.5% profit (1:1 ratio)
        """
        if action == "BUY":
            entry = current_price
            stop_loss = entry * 0.995  # 0.5% stop
            target = entry * 1.005     # 0.5% profit

        elif action == "SHORT":
            entry = current_price
            stop_loss = entry * 1.005  # 0.5% stop
            target = entry * 0.995     # 0.5% profit

        else:
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
        Scalping requires VERY high confidence
        """
        # Check base criteria
        should_trade, reason = super().should_take_trade(signal, current_price, **kwargs)
        if not should_trade:
            return False, reason

        # Scalping needs higher confidence
        if signal.confidence < 80:
            return False, f"Confidence {signal.confidence:.0f}% < 80% (scalping needs very high confidence)"

        # Need strong consensus
        consensus = signal.get_consensus_strength()
        if consensus < 90:
            return False, f"Consensus {consensus:.0f}% < 90% (scalping needs near-perfect agreement)"

        return True, "Scalping criteria met"
```

### Step 2: Import in `__init__.py`

Edit `src/strategy/strategies/__init__.py`:

```python
from .multi_indicator import MultiIndicatorStrategy
from .mean_reversion import MeanReversionStrategy
from .breakout import BreakoutStrategy
from .scalping import ScalpingStrategy  # ← ADD THIS

__all__ = [
    'MultiIndicatorStrategy',
    'MeanReversionStrategy',
    'BreakoutStrategy',
    'ScalpingStrategy',  # ← AND THIS
]
```

### Step 3: Register in Factory

Edit `src/strategy/strategy_factory.py` in the `_register_built_in_strategies()` function:

```python
def _register_built_in_strategies():
    from src.strategy.strategies import (
        MultiIndicatorStrategy,
        MeanReversionStrategy,
        BreakoutStrategy,
        ScalpingStrategy  # ← ADD THIS
    )

    StrategyFactory.register('MULTI_INDICATOR', MultiIndicatorStrategy)
    StrategyFactory.register('DEFAULT', MultiIndicatorStrategy)
    StrategyFactory.register('MEAN_REVERSION', MeanReversionStrategy)
    StrategyFactory.register('BREAKOUT', BreakoutStrategy)
    StrategyFactory.register('SCALPING', ScalpingStrategy)  # ← AND THIS

    logger.info(f"Registered {len(StrategyFactory._registry)} built-in strategies")
```

**That's it!** 🎉 Your new strategy is now available in the system.

---

## Using Your Strategy

### From Python Code

```python
from src.strategy import StrategyFactory

# List all available strategies
strategies = StrategyFactory.get_available_strategies()
print(strategies)
# [
#   {'name': 'MULTI_INDICATOR', 'description': '...'},
#   {'name': 'MEAN_REVERSION', 'description': '...'},
#   {'name': 'BREAKOUT', 'description': '...'},
#   {'name': 'SCALPING', 'description': '...'}
# ]

# Create strategy instance
strategy = StrategyFactory.create('SCALPING')

# Use the strategy
levels = strategy.calculate_trade_levels(current_price=100.0, signal=..., action='BUY')
print(levels)  # {'entry': 100.0, 'stop_loss': 99.5, 'target': 100.5}
```

### From Dashboard

The dashboard will automatically detect all registered strategies. Users can:
1. Go to the Strategy Configuration page
2. Select strategy from dropdown (populated from `StrategyFactory.get_available_strategies()`)
3. Configure strategy parameters
4. Changes apply after market close (4pm)

---

## Available Strategies

| Strategy | Best For | Risk:Reward | Stop Loss | When to Use |
|----------|----------|-------------|-----------|-------------|
| **MULTI_INDICATOR** | General purpose | 1:3 | 2% or 1.5×ATR | Balanced trading, multiple signals |
| **MEAN_REVERSION** | Range-bound markets | 1:1.5 | 1.5% | Oversold/overbought extremes |
| **BREAKOUT** | Trending markets | 1:4 | 3% or 2×ATR | Strong directional moves, high ADX |
| **SCALPING** | Intraday quick trades | 1:1 | 0.5% | Very high confidence, liquid stocks |

---

## Strategy Interface

Every strategy MUST implement these methods:

```python
class YourStrategy(TradingStrategy):

    def get_name(self) -> str:
        """Return unique strategy name (e.g., 'YOUR_STRATEGY')"""
        pass

    def get_description(self) -> str:
        """Return human-readable description"""
        pass

    def calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: str
    ) -> Dict[str, float]:
        """
        Calculate entry, stop_loss, and target prices

        MUST return: {'entry': float, 'stop_loss': float, 'target': float}
        """
        pass
```

**Optional** override:

```python
def should_take_trade(
    self,
    signal: AggregatedSignal,
    current_price: float,
    **kwargs
) -> tuple[bool, str]:
    """
    Add custom validation logic

    Returns: (should_trade: bool, reason: str)
    """
    pass
```

---

## Strategy Configuration

You can customize strategy parameters:

```python
from src.strategy import StrategyConfig, StrategyFactory

# Create custom config
config = StrategyConfig(
    name="SCALPING",
    description="My custom scalping setup",
    min_confidence=85.0,      # Higher confidence threshold
    min_risk_reward=1.2,      # Custom R:R ratio
    risk_per_trade_percent=0.5,  # Lower risk per trade
    params={
        'max_trades_per_day': 10,
        'stop_multiplier': 0.003  # 0.3% stop
    }
)

# Create strategy with custom config
strategy = StrategyFactory.create('SCALPING', config)
```

---

## Best Practices

### 1. **Name Your Strategy Clearly**
```python
def get_name(self) -> str:
    return "DESCRIPTIVE_NAME"  # Use UPPERCASE with underscores
```

### 2. **Write Good Descriptions**
```python
def get_description(self) -> str:
    return "Clear description of when to use this strategy"
```

### 3. **Extract Helper Methods**
```python
def _get_atr_value(self, signal: AggregatedSignal) -> float:
    """Extract ATR from signal indicators"""
    for ind_name, ind_signal in signal.indicator_signals.items():
        if 'ATR' in ind_name:
            return ind_signal.current_value
    return None
```

### 4. **Add Validation**
```python
def should_take_trade(self, signal, current_price, **kwargs):
    # Always call super() first
    should_trade, reason = super().should_trade(signal, current_price, **kwargs)
    if not should_trade:
        return False, reason

    # Add your custom checks
    if some_condition:
        return False, "Reason for rejection"

    return True, "All checks passed"
```

### 5. **Use Type Hints**
```python
def calculate_trade_levels(
    self,
    current_price: float,  # ← Type hints
    signal: AggregatedSignal,
    action: str
) -> Dict[str, float]:  # ← Return type
    pass
```

---

## Testing Your Strategy

```python
# Test imports
from src.strategy.strategies import ScalpingStrategy
from src.strategy import StrategyFactory

# Test instantiation
strategy = ScalpingStrategy()
assert strategy.get_name() == "SCALPING"

# Test factory creation
strategy2 = StrategyFactory.create('SCALPING')
assert strategy2 is not None

# Test trade level calculation
levels = strategy.calculate_trade_levels(
    current_price=100.0,
    signal=mock_signal,
    action='BUY'
)
assert 'entry' in levels
assert 'stop_loss' in levels
assert 'target' in levels
```

---

## Real-World Example: Adding Options Strategy

Want to trade options? Here's how:

```python
class OptionsWheelStrategy(TradingStrategy):
    """Sell cash-secured puts, if assigned sell covered calls"""

    def get_name(self) -> str:
        return "OPTIONS_WHEEL"

    def get_description(self) -> str:
        return "Sell puts, get assigned, sell calls (The Wheel)"

    def calculate_trade_levels(self, current_price, signal, action):
        # For options, we might return strike prices instead
        return {
            'entry': current_price * 0.95,  # Sell put at 95% of current
            'stop_loss': current_price * 0.85,  # Stop if drops 15%
            'target': current_price * 1.05  # Target if assigned + call premium
        }

    def should_take_trade(self, signal, current_price, **kwargs):
        # Options-specific: only trade if IV rank > 50
        iv_rank = kwargs.get('iv_rank', 0)
        if iv_rank < 50:
            return False, f"IV Rank {iv_rank} < 50 (need high premium)"

        return True, "High IV - good premium available"
```

---

## Questions?

- Strategy not showing up? → Check `strategy_factory.py` registration
- Import errors? → Verify all methods are implemented
- Strategy behaving oddly? → Add logging and test with mock data first

---

**Remember**: You can have as many strategies as you want. The system will manage them all automatically!
