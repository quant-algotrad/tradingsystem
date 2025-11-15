# Design Patterns Implementation Guide

This document describes all design patterns implemented in the trading system, why they were chosen, and how to use them.

---

## 📋 Table of Contents

1. [Observer Pattern - Notifications](#1-observer-pattern---notifications)
2. [Strategy Pattern - Trading Strategies](#2-strategy-pattern---trading-strategies)
3. [Strategy Pattern - Position Sizing](#3-strategy-pattern---position-sizing)
4. [Chain of Responsibility - Risk Management](#4-chain-of-responsibility---risk-management)
5. [Factory Pattern - Component Creation](#5-factory-pattern---component-creation)
6. [Facade Pattern - Simplified Interfaces](#6-facade-pattern---simplified-interfaces)
7. [Quick Reference](#7-quick-reference)

---

## 1. Observer Pattern - Notifications

**Location:** `src/notifications/`

**Problem Solved:**
- Need to notify multiple channels (WebSocket, Email, Discord) when events occur
- Don't want tight coupling between event sources and notification channels
- Want to easily add/remove notification channels

**Solution:**
```
Subject (NotificationManager) → Observers (WebSocket, Email, Discord)
                                ↓
                            All get notified when event occurs
```

### Components

| Component | Role | Status |
|-----------|------|--------|
| `INotifier` | Observer interface | Base class |
| `WebSocketNotifier` | Real-time dashboard updates | ✅ Enabled |
| `EmailNotifier` | Critical email alerts | 🔒 Disabled (configurable) |
| `DiscordNotifier` | Mobile notifications | 🔒 Disabled (needs webhook) |
| `NotificationManager` | Subject that manages observers | Singleton |

### Usage

**Simple notifications:**
```python
from src.notifications import notify_trade, notify_signal, notify_risk

# Auto priority determination
notify_trade(trade_event)       # Sends to all enabled channels
notify_signal(signal_event)     # High confidence → high priority
notify_risk(risk_event)         # Critical risks → critical priority
```

**Advanced control:**
```python
from src.notifications import get_notification_manager, NotificationPriority

manager = get_notification_manager()

# Send with specific priority
manager.notify(event, priority=NotificationPriority.CRITICAL)

# Send to specific channels only
manager.notify(event, channels=['Discord', 'Email'])

# Configure priority routing
manager.set_priority_routing('Email', [NotificationPriority.CRITICAL])

# Enable/disable channels
manager.enable_channel('Discord')
manager.disable_channel('Email')

# Get status
status = manager.get_status()
print(f"Active channels: {status['total_channels']}")
```

### Adding a New Notification Channel

**Example: Adding SMS notifications**

```python
# 1. Create notifier class
from src.notifications.base_notifier import INotifier, NotificationPriority

class SMSNotifier(INotifier):
    def get_name(self) -> str:
        return "SMS"

    def send(self, event: BaseEvent, priority: NotificationPriority) -> bool:
        # Send SMS using Twilio
        pass

# 2. Register with manager
from src.notifications import get_notification_manager

manager = get_notification_manager()
manager.register(SMSNotifier(enabled=True))
```

**That's it!** No modification to existing code needed.

### Configuration

**Email Setup:**
```bash
# .env file
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECIPIENT_EMAILS=recipient1@email.com,recipient2@email.com
```

**Discord Setup:**
```bash
# 1. Go to Discord Server Settings → Integrations → Webhooks
# 2. Create New Webhook, copy URL
# 3. Set environment variable
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## 2. Strategy Pattern - Trading Strategies

**Location:** `src/strategy/strategies/`

**Problem Solved:**
- Different trading approaches need different logic (trend following, mean reversion, breakout)
- Hardcoded strategy logic makes it impossible to add new strategies
- Can't switch strategies without code changes

**Solution:**
```
TradingStrategy (interface)
    ↓
    ├── MultiIndicatorStrategy (default)
    ├── MeanReversionStrategy
    └── BreakoutStrategy
```

### Available Strategies

| Strategy | Best For | Risk:Reward | Stop Loss | Key Logic |
|----------|----------|-------------|-----------|-----------|
| **MULTI_INDICATOR** | General trading | 1:3 | 2% or 1.5×ATR | Weighted voting from multiple indicators |
| **MEAN_REVERSION** | Range-bound markets | 1:1.5 | 1.5% | RSI <30 or >70, BB extremes |
| **BREAKOUT** | Trending markets | 1:4 | 3% or 2×ATR | ADX >25, high confidence required |

### Usage

```python
from src.strategy import StrategyFactory

# List all strategies
strategies = StrategyFactory.get_available_strategies()
for s in strategies:
    print(f"{s['name']}: {s['description']}")

# Create strategy instance
strategy = StrategyFactory.create('BREAKOUT')

# Calculate trade levels
levels = strategy.calculate_trade_levels(
    current_price=1500.0,
    signal=aggregated_signal,
    action='BUY'
)
print(f"Entry: {levels['entry']}, Stop: {levels['stop_loss']}, Target: {levels['target']}")

# Check if should take trade
should_trade, reason = strategy.should_take_trade(signal, current_price)
if not should_trade:
    print(f"Trade rejected: {reason}")
```

### Adding a New Strategy

See `HOW_TO_ADD_STRATEGY.md` for detailed guide.

**Quick example:**
```python
# src/strategy/strategies/scalping.py
from src.strategy.base_strategy import TradingStrategy

class ScalpingStrategy(TradingStrategy):
    def get_name(self) -> str:
        return "SCALPING"

    def get_description(self) -> str:
        return "Quick in-out trades with tight stops"

    def calculate_trade_levels(self, current_price, signal, action):
        # Ultra-tight stops and targets
        return {
            'entry': current_price,
            'stop_loss': current_price * 0.995,  # 0.5% stop
            'target': current_price * 1.005      # 0.5% target
        }
```

---

## 3. Strategy Pattern - Position Sizing

**Location:** `src/strategy/position_sizing/`

**Problem Solved:**
- Hardcoded 1% risk doesn't fit all strategies
- Need Kelly Criterion for optimal growth
- Want volatility-adjusted sizing for risk management

**Solution:**
```
IPositionSizer (interface)
    ↓
    ├── FixedRiskSizer (most common)
    ├── KellyCriterionSizer (optimal growth)
    └── VolatilityAdjustedSizer (ATR-based)
```

### Available Sizing Methods

| Method | When to Use | Pros | Cons |
|--------|-------------|------|------|
| **FixedRiskSizer** | Default choice | Simple, safe | Doesn't adapt to conditions |
| **KellyCriterionSizer** | Have win rate data | Mathematically optimal | Can be aggressive |
| **VolatilityAdjustedSizer** | Varying volatility | Adapts to market conditions | Needs ATR data |

### Usage

**Fixed Risk (default):**
```python
from src.strategy.position_sizing import FixedRiskSizer

sizer = FixedRiskSizer(risk_percent=1.0, max_position_percent=20.0)

result = sizer.calculate_position_size(
    capital=50000,
    entry_price=100.0,
    stop_loss=98.0
)

print(f"Buy {result.quantity} shares")
print(f"Position value: ₹{result.position_value:.2f}")
print(f"Risk: ₹{result.risk_amount:.2f} ({result.risk_percent:.2f}%)")
```

**Kelly Criterion:**
```python
from src.strategy.position_sizing import KellyCriterionSizer

sizer = KellyCriterionSizer(
    win_rate=0.55,          # 55% win rate
    avg_win=6.0,            # Average 6% wins
    avg_loss=3.0,           # Average 3% losses
    kelly_fraction=0.25     # Use 25% of full Kelly (safer)
)

result = sizer.calculate_position_size(
    capital=50000,
    entry_price=100.0,
    stop_loss=98.0
)
```

**Volatility-Adjusted:**
```python
from src.strategy.position_sizing import VolatilityAdjustedSizer

sizer = VolatilityAdjustedSizer(
    risk_percent=1.0,
    atr_multiplier=2.0
)

result = sizer.calculate_position_size(
    capital=50000,
    entry_price=100.0,
    stop_loss=98.0,
    atr=5.0  # ATR value from indicator
)
```

### Implementing in Trading Strategies

Strategies can specify their preferred position sizing:

```python
class BreakoutStrategy(TradingStrategy):
    def __init__(self):
        super().__init__()
        # Breakout uses volatility-adjusted sizing
        self.position_sizer = VolatilityAdjustedSizer(
            risk_percent=1.5,  # Slightly more aggressive
            atr_multiplier=2.5
        )

    def calculate_position_size(self, capital, entry, stop, atr):
        return self.position_sizer.calculate_position_size(
            capital, entry, stop, atr=atr
        )
```

---

## 4. Chain of Responsibility - Risk Management

**Location:** `src/risk/`

**Problem Solved:**
- Risk checks scattered throughout codebase
- Hard to add/remove risk rules
- Can't customize risk per strategy
- Mixed business logic with risk logic

**Solution:**
```
Trade Data
    ↓
MaxDrawdownValidator → PositionLimitValidator → CapitalValidator → ... → ✅/❌
```

### Available Risk Validators

| Validator | Checks | Configurable | Default |
|-----------|--------|--------------|---------|
| `MaxDrawdownValidator` | Daily loss % | ✅ | 5% |
| `PositionLimitValidator` | Max concurrent positions | ✅ | 5 |
| `DuplicatePositionValidator` | No duplicate symbols | ❌ | - |
| `PositionSizeValidator` | Max position size % | ✅ | 20% |
| `RiskPerTradeValidator` | Max risk % per trade | ✅ | 2% |
| `CapitalValidator` | Min capital reserve | ✅ | ₹1,000 |
| `MarketHoursValidator` | Trading hours | ✅ | 9:15-15:30 |
| `ConcentrationValidator` | Sector concentration | ✅ | 40% |

### Usage

**Simple validation:**
```python
from src.risk import get_risk_manager

manager = get_risk_manager()

trade_data = {
    'symbol': 'RELIANCE.NS',
    'quantity': 100,
    'entry_price': 2500,
    'stop_loss': 2450,
    'position_value': 250000,
    'risk_percent': 2.0,
    'capital': 500000,
    'current_position_count': 3,
    'existing_position_symbols': ['TCS.NS', 'INFY.NS'],
    'position_type': 'SWING'
}

passed, results = manager.validate_trade(trade_data)

if not passed:
    for result in results:
        if not result.passed:
            print(f"❌ {result.validator_name}: {result.reason}")
else:
    print("✅ All risk checks passed - trade approved")
```

**Get summary:**
```python
summary = manager.get_summary(results)
print(f"Passed: {summary['passed']}/{summary['total_checks']}")
print(f"Failed checks: {summary['failed_checks']}")
```

**Configure risk parameters:**
```python
from src.risk import RiskManager

manager = RiskManager(config={
    'max_drawdown_percent': 3.0,      # Stricter drawdown
    'max_positions': 10,               # More positions allowed
    'max_risk_percent': 1.5,          # Lower risk per trade
    'max_sector_concentration': 30.0  # Stricter concentration
})
```

### Adding Custom Risk Validator

```python
from src.risk.base_validator import IRiskValidator, RiskValidationResult

class CustomRiskValidator(IRiskValidator):
    def get_name(self) -> str:
        return "CustomRiskValidator"

    def validate(self, trade_data):
        # Your custom logic
        if some_condition:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason="Custom risk rule violated",
                severity="WARNING"
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason="Custom check passed"
        )

# Add to manager
from src.risk import get_risk_manager

manager = get_risk_manager()
manager.add_validator(CustomRiskValidator())
```

---

## 5. Factory Pattern - Component Creation

**Already Implemented:**

| Factory | Location | Purpose |
|---------|----------|---------|
| `IndicatorFactory` | `src/indicators/indicator_calculator.py` | Create indicator instances |
| `StrategyFactory` | `src/strategy/strategy_factory.py` | Create trading strategies |
| `DataSourceFactory` | `src/data/data_source_factory.py` | Create data sources |

**Benefits:**
- Centralized object creation
- Easy to add new types
- Registry pattern for auto-discovery

---

## 6. Facade Pattern - Simplified Interfaces

**Already Implemented:**

| Facade | Location | Simplifies |
|--------|----------|------------|
| `DataFetcher` | `src/data/data_fetcher.py` | Complex data fetching, fallback, caching |
| `TradingPipeline` | `src/integration/trading_pipeline.py` | End-to-end trading workflow |
| `NotificationManager` | `src/notifications/notification_manager.py` | Multi-channel notifications |
| `RiskManager` | `src/risk/risk_manager.py` | Complex risk validation chain |

**Benefits:**
- Simple API for complex operations
- Hides implementation details
- Single entry point

---

## 7. Quick Reference

### When to Use Which Pattern

| Need | Pattern | Implementation |
|------|---------|----------------|
| Notify multiple channels | Observer | `NotificationManager` |
| Switch trading logic | Strategy | `TradingStrategy` + `StrategyFactory` |
| Different position sizing | Strategy | `IPositionSizer` implementations |
| Multiple risk checks | Chain of Responsibility | `IRiskValidator` chain |
| Create objects centrally | Factory | `StrategyFactory`, etc. |
| Simplify complex operations | Facade | `DataFetcher`, `TradingPipeline` |

### Code Examples

**Comprehensive trading flow with all patterns:**

```python
from src.strategy import StrategyFactory
from src.strategy.position_sizing import KellyCriterionSizer
from src.risk import get_risk_manager
from src.notifications import notify_trade, NotificationPriority

# 1. Select strategy (Strategy Pattern)
strategy = StrategyFactory.create('BREAKOUT')

# 2. Calculate trade levels
levels = strategy.calculate_trade_levels(
    current_price=1500,
    signal=aggregated_signal,
    action='BUY'
)

# 3. Calculate position size (Strategy Pattern)
sizer = KellyCriterionSizer(win_rate=0.60, kelly_fraction=0.25)
size_result = sizer.calculate_position_size(
    capital=100000,
    entry_price=levels['entry'],
    stop_loss=levels['stop_loss']
)

# 4. Validate risk (Chain of Responsibility)
trade_data = {
    'symbol': 'RELIANCE.NS',
    'quantity': size_result.quantity,
    'position_value': size_result.position_value,
    'risk_percent': size_result.risk_percent,
    'capital': 100000,
    # ... other data
}

risk_manager = get_risk_manager()
passed, risk_results = risk_manager.validate_trade(trade_data)

if not passed:
    print("Trade rejected by risk management")
    for result in risk_results:
        if not result.passed:
            print(f"  - {result.reason}")
else:
    # 5. Execute trade and notify (Observer Pattern)
    execute_trade(trade_data)
    notify_trade(trade_event, priority=NotificationPriority.HIGH)
```

---

## Benefits Summary

### Maintainability
- ✅ Easy to add new strategies (just one file)
- ✅ Easy to add new notification channels
- ✅ Easy to add/remove risk rules
- ✅ No modification to existing code

### Testability
- ✅ Each component can be tested independently
- ✅ Mock validators, strategies easily
- ✅ Clear interfaces

### Flexibility
- ✅ Switch strategies at runtime
- ✅ Enable/disable notification channels
- ✅ Customize risk rules per strategy
- ✅ Different position sizing per strategy

### Scalability
- ✅ Add notification channels without limits
- ✅ Add risk validators without limits
- ✅ Add strategies without limits
- ✅ Clean separation of concerns

---

## Additional Resources

- `HOW_TO_ADD_STRATEGY.md` - Detailed strategy creation guide
- `src/notifications/` - Observer pattern implementation
- `src/strategy/position_sizing/` - Position sizing strategies
- `src/risk/` - Risk management chain

**Questions?** Each module has comprehensive docstrings and examples!
