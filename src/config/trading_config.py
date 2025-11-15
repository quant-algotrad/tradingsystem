"""
Trading Configuration
Defines trading rules, position limits, and execution parameters
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.config.base_config import BaseConfig, ValidationMixin
from src.config.constants import (
    PositionType, OrderType, Timeframe, StrategyName,
    RiskDefaults, MarketHours
)


@dataclass
class PositionLimits(ValidationMixin):
    """Position sizing and limits configuration"""

    # Capital allocation
    initial_capital: float = RiskDefaults.INITIAL_CAPITAL
    max_position_size_percent: float = RiskDefaults.MAX_POSITION_PERCENT
    max_deployed_capital_percent: float = RiskDefaults.MAX_DEPLOYED_PERCENT
    cash_buffer_percent: float = RiskDefaults.CASH_BUFFER_PERCENT

    # Position counts
    max_swing_positions: int = RiskDefaults.MAX_SWING_POSITIONS
    max_intraday_positions: int = RiskDefaults.MAX_INTRADAY_POSITIONS
    max_options_positions: int = RiskDefaults.MAX_OPTIONS_POSITIONS
    max_positions_per_sector: int = RiskDefaults.MAX_SECTOR_POSITIONS
    min_sectors_required: int = RiskDefaults.MIN_SECTORS

    # Options limits
    max_options_capital_percent: float = RiskDefaults.MAX_OPTIONS_CAPITAL_PERCENT
    max_option_premium_per_trade: float = RiskDefaults.MAX_OPTION_PREMIUM
    min_days_to_expiry: int = RiskDefaults.MIN_DAYS_TO_EXPIRY

    def validate(self) -> tuple[bool, List[str]]:
        """Validate position limits"""
        errors = []

        # Validate capital
        if error := self.validate_positive(self.initial_capital, "initial_capital"):
            errors.append(error)

        # Validate percentages
        for field_name in ['max_position_size_percent', 'max_deployed_capital_percent',
                          'cash_buffer_percent', 'max_options_capital_percent']:
            value = getattr(self, field_name)
            if error := self.validate_percentage(value, field_name):
                errors.append(error)

        # Validate position counts
        if self.max_swing_positions < 1:
            errors.append("max_swing_positions must be at least 1")

        if self.max_intraday_positions < 1:
            errors.append("max_intraday_positions must be at least 1")

        # Logical validations
        if self.max_deployed_capital_percent + self.cash_buffer_percent > 100:
            errors.append("Deployed capital + cash buffer cannot exceed 100%")

        return (len(errors) == 0, errors)


@dataclass
class TradingHours:
    """Market timing configuration"""

    market_open: str = MarketHours.MARKET_OPEN
    market_close: str = MarketHours.MARKET_CLOSE
    intraday_entry_cutoff: str = MarketHours.INTRADAY_CUTOFF
    auto_square_time: str = MarketHours.AUTO_SQUARE_TIME
    post_market_start: str = MarketHours.POST_MARKET_START

    # Trading windows
    avoid_first_n_minutes: int = 15  # Skip first 15 min (9:15-9:30)
    avoid_last_n_minutes: int = 15   # Skip last 15 min (3:15-3:30)


@dataclass
class OrderExecutionConfig(ValidationMixin):
    """Order execution preferences"""

    # Default order types
    default_entry_order_type: OrderType = OrderType.MARKET
    default_exit_order_type: OrderType = OrderType.MARKET
    use_bracket_orders: bool = False

    # Slippage and costs
    expected_slippage_percent: float = 0.1  # 0.1% expected slippage
    max_acceptable_slippage_percent: float = 0.5  # 0.5% max acceptable

    # Execution timing
    order_timeout_seconds: int = 30
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 2

    # Partial fills
    allow_partial_fills: bool = True
    min_fill_percent: float = 80.0  # Accept if >= 80% filled

    def validate(self) -> tuple[bool, List[str]]:
        """Validate execution config"""
        errors = []

        if error := self.validate_percentage(self.expected_slippage_percent, "expected_slippage_percent"):
            errors.append(error)

        if error := self.validate_percentage(self.max_acceptable_slippage_percent, "max_acceptable_slippage_percent"):
            errors.append(error)

        if self.expected_slippage_percent > self.max_acceptable_slippage_percent:
            errors.append("Expected slippage cannot exceed max acceptable slippage")

        if self.order_timeout_seconds < 5:
            errors.append("Order timeout must be at least 5 seconds")

        return (len(errors) == 0, errors)


@dataclass
class StrategyConfig:
    """Strategy enablement and weights"""

    # Enable/disable strategies
    enabled_strategies: List[str] = field(default_factory=lambda: [
        StrategyName.TREND_RSI.value,
        StrategyName.MEAN_REVERSION.value,
        StrategyName.BREAKOUT.value,
        StrategyName.MOMENTUM.value,
    ])

    # Strategy weights for capital allocation
    strategy_weights: Dict[str, float] = field(default_factory=lambda: {
        StrategyName.TREND_RSI.value: 0.30,
        StrategyName.MEAN_REVERSION.value: 0.25,
        StrategyName.BREAKOUT.value: 0.25,
        StrategyName.MOMENTUM.value: 0.20,
    })

    # Min signal strength to execute
    min_signal_strength: float = 60.0  # 0-100 scale

    # Multi-timeframe requirements
    require_timeframe_alignment: bool = True
    min_alignment_score: float = 70.0  # 70% alignment required


@dataclass
class TimeframeConfig:
    """Multi-timeframe analysis configuration"""

    # Primary timeframe for each trading style
    swing_primary_timeframe: Timeframe = Timeframe.DAILY
    intraday_primary_timeframe: Timeframe = Timeframe.MINUTE_15

    # Timeframes to analyze
    enabled_timeframes: List[str] = field(default_factory=lambda: [
        Timeframe.DAILY.value,
        Timeframe.HOUR_1.value,
        Timeframe.MINUTE_15.value,
        Timeframe.MINUTE_5.value,
    ])

    # Timeframe weights for alignment scoring
    timeframe_weights: Dict[str, float] = field(default_factory=lambda: {
        Timeframe.DAILY.value: 0.40,     # Highest weight to trend
        Timeframe.HOUR_1.value: 0.30,    # Medium-term
        Timeframe.MINUTE_15.value: 0.20, # Entry timing
        Timeframe.MINUTE_5.value: 0.10,  # Fine-tuning
    })

    # Historical data requirements
    min_daily_bars: int = 500        # ~2 years
    min_hourly_bars: int = 1000      # ~6 months
    min_15min_bars: int = 2000       # ~3 months


@dataclass
class TradingConfig(BaseConfig, ValidationMixin):
    """
    Main Trading Configuration

    Aggregates all trading-related settings
    Follows Single Responsibility Principle by composing smaller configs
    """

    # Sub-configurations (Composition over Inheritance)
    position_limits: PositionLimits = field(default_factory=PositionLimits)
    trading_hours: TradingHours = field(default_factory=TradingHours)
    order_execution: OrderExecutionConfig = field(default_factory=OrderExecutionConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    timeframes: TimeframeConfig = field(default_factory=TimeframeConfig)

    # Trading mode
    paper_trading_mode: bool = True  # Start with paper trading
    allow_short_selling: bool = True
    allow_options_trading: bool = False  # Start False, enable after testing

    # Stock universe
    watchlist_symbols: List[str] = field(default_factory=lambda: [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"
    ])
    max_watchlist_size: int = 50

    # Data refresh
    price_update_interval_seconds: int = 5  # Real-time updates every 5s
    eod_data_fetch_time: str = "15:45"      # Fetch EOD data at 3:45 PM

    def validate(self) -> tuple[bool, List[str]]:
        """Validate trading configuration"""
        errors = []

        # Validate sub-configurations
        is_valid, sub_errors = self.position_limits.validate()
        errors.extend(sub_errors)

        is_valid, sub_errors = self.order_execution.validate()
        errors.extend(sub_errors)

        # Validate watchlist
        if len(self.watchlist_symbols) == 0:
            errors.append("Watchlist cannot be empty")

        if len(self.watchlist_symbols) > self.max_watchlist_size:
            errors.append(f"Watchlist exceeds max size of {self.max_watchlist_size}")

        # Validate price update interval
        if self.price_update_interval_seconds < 1:
            errors.append("Price update interval must be at least 1 second")

        # Validate strategy weights sum to ~1.0
        if self.strategy.strategy_weights:
            total_weight = sum(self.strategy.strategy_weights.values())
            if not (0.99 <= total_weight <= 1.01):  # Allow small floating point error
                errors.append(f"Strategy weights must sum to 1.0, got {total_weight}")

        return (len(errors) == 0, errors)

    def from_dict(self, data: Dict[str, Any]) -> 'TradingConfig':
        """Create from dictionary"""
        # Convert nested dicts to dataclasses
        if 'position_limits' in data:
            data['position_limits'] = PositionLimits(**data['position_limits'])
        if 'trading_hours' in data:
            data['trading_hours'] = TradingHours(**data['trading_hours'])
        if 'order_execution' in data:
            data['order_execution'] = OrderExecutionConfig(**data['order_execution'])
        if 'strategy' in data:
            data['strategy'] = StrategyConfig(**data['strategy'])
        if 'timeframes' in data:
            data['timeframes'] = TimeframeConfig(**data['timeframes'])

        return TradingConfig(**data)

    def get_summary(self) -> str:
        """Human-readable summary"""
        return f"""
Trading Configuration Summary:
- Mode: {'Paper Trading' if self.paper_trading_mode else 'Live Trading'}
- Initial Capital: ₹{self.position_limits.initial_capital:,.0f}
- Max Swing Positions: {self.position_limits.max_swing_positions}
- Max Intraday Positions: {self.position_limits.max_intraday_positions}
- Enabled Strategies: {len(self.strategy.enabled_strategies)}
- Watchlist Size: {len(self.watchlist_symbols)}
- Short Selling: {'Enabled' if self.allow_short_selling else 'Disabled'}
- Options Trading: {'Enabled' if self.allow_options_trading else 'Disabled'}
        """.strip()

    def get_max_position_capital(self) -> float:
        """Calculate maximum capital per position"""
        return (self.position_limits.initial_capital *
                self.position_limits.max_position_size_percent / 100.0)

    def get_total_deployable_capital(self) -> float:
        """Calculate total deployable capital"""
        return (self.position_limits.initial_capital *
                self.position_limits.max_deployed_capital_percent / 100.0)

    def get_cash_reserve(self) -> float:
        """Calculate required cash reserve"""
        return (self.position_limits.initial_capital *
                self.position_limits.cash_buffer_percent / 100.0)
