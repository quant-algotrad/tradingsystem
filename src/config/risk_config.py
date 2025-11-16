"""
Risk Management Configuration
Defines all risk limits, stop-loss rules, and circuit breakers
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.config.base_config import BaseConfig, ValidationMixin
from src.config.constants import StopLossType, RiskDefaults


@dataclass
class LossLimits(ValidationMixin):
    """
    Loss limit configuration
    Implements progressive risk controls
    """

    # Per-trade risk
    risk_per_trade_percent: float = RiskDefaults.RISK_PER_TRADE_PERCENT
    max_risk_per_trade_amount: float = 500.0  # ₹500 for ₹50k capital

    # Daily limits
    max_daily_loss_percent: float = RiskDefaults.MAX_DAILY_LOSS_PERCENT
    max_daily_loss_amount: float = 1500.0  # ₹1,500

    # Weekly limits
    max_weekly_loss_percent: float = RiskDefaults.MAX_WEEKLY_LOSS_PERCENT
    max_weekly_loss_amount: float = 3000.0  # ₹3,000

    # Monthly limits
    max_monthly_drawdown_percent: float = RiskDefaults.MAX_MONTHLY_DRAWDOWN_PERCENT
    max_monthly_drawdown_amount: float = 5000.0  # ₹5,000

    # Intraday-specific
    max_intraday_loss_percent: float = RiskDefaults.MAX_INTRADAY_LOSS_PERCENT
    max_intraday_loss_amount: float = 1000.0  # ₹1,000

    # Consecutive losses
    max_consecutive_losses: int = 3
    cooldown_after_consecutive_losses_minutes: int = 60

    def validate(self) -> tuple[bool, List[str]]:
        """Validate loss limits"""
        errors = []

        # Validate percentages
        for field_name in ['risk_per_trade_percent', 'max_daily_loss_percent',
                          'max_weekly_loss_percent', 'max_monthly_drawdown_percent',
                          'max_intraday_loss_percent']:
            value = getattr(self, field_name)
            if error := self.validate_percentage(value, field_name):
                errors.append(error)

        # Validate amounts
        for field_name in ['max_risk_per_trade_amount', 'max_daily_loss_amount',
                          'max_weekly_loss_amount', 'max_monthly_drawdown_amount',
                          'max_intraday_loss_amount']:
            value = getattr(self, field_name)
            if error := self.validate_positive(value, field_name):
                errors.append(error)

        # Logical validations (progressive limits)
        if self.max_daily_loss_percent > self.max_weekly_loss_percent:
            errors.append("Daily loss limit cannot exceed weekly limit")

        if self.max_weekly_loss_percent > self.max_monthly_drawdown_percent:
            errors.append("Weekly loss limit cannot exceed monthly limit")

        if self.risk_per_trade_percent > self.max_daily_loss_percent:
            errors.append("Per-trade risk cannot exceed daily loss limit")

        return (len(errors) == 0, errors)


@dataclass
class StopLossConfig(ValidationMixin):
    """Stop-loss configuration for different strategies"""

    # Default stop-loss type
    default_stop_type: StopLossType = StopLossType.PERCENTAGE

    # Fixed stop-loss (absolute price)
    fixed_sl_enabled: bool = True

    # Percentage-based stop-loss
    percentage_sl_enabled: bool = True
    default_sl_percent: float = 2.0  # 2% from entry
    max_sl_percent: float = 5.0      # Never wider than 5%

    # Trailing stop-loss
    trailing_sl_enabled: bool = True
    trailing_activation_percent: float = 2.0  # Activate after 2% profit
    trailing_distance_percent: float = 1.0    # Trail by 1%

    # ATR-based stop-loss (volatility-adjusted)
    atr_sl_enabled: bool = True
    atr_multiplier: float = 2.0  # SL = Entry - (2 * ATR)

    # Time-based stop-loss
    time_based_sl_enabled: bool = True
    max_hold_hours_intraday: int = 4
    max_hold_days_swing: int = 10

    # Auto-tightening
    tighten_sl_on_profit: bool = True
    tighten_threshold_percent: float = 3.0  # After 3% profit
    tighten_to_percent: float = 1.0         # Move to 1% SL

    def validate(self) -> tuple[bool, List[str]]:
        """Validate stop-loss config"""
        errors = []

        # At least one SL type must be enabled
        if not any([self.fixed_sl_enabled, self.percentage_sl_enabled,
                   self.trailing_sl_enabled, self.atr_sl_enabled,
                   self.time_based_sl_enabled]):
            errors.append("At least one stop-loss type must be enabled")

        # Validate percentages
        if error := self.validate_percentage(self.default_sl_percent, "default_sl_percent"):
            errors.append(error)

        if error := self.validate_percentage(self.max_sl_percent, "max_sl_percent"):
            errors.append(error)

        if self.default_sl_percent > self.max_sl_percent:
            errors.append("Default SL cannot exceed max SL")

        # Validate trailing stop logic
        if self.trailing_sl_enabled:
            if self.trailing_distance_percent <= 0:
                errors.append("Trailing distance must be positive")
            if self.trailing_activation_percent <= self.trailing_distance_percent:
                errors.append("Trailing activation must be greater than trailing distance")

        # Validate ATR multiplier
        if self.atr_multiplier <= 0:
            errors.append("ATR multiplier must be positive")

        return (len(errors) == 0, errors)


@dataclass
class TargetConfig(ValidationMixin):
    """Profit target configuration"""

    # Default target type
    use_targets: bool = True

    # Risk-reward ratio
    min_risk_reward_ratio: float = RiskDefaults.MIN_RISK_REWARD_RATIO
    default_risk_reward_ratio: float = 2.5  # Target 2.5x the risk

    # Partial exits
    enable_partial_exits: bool = True
    first_target_percent: float = 3.0   # Exit 50% at 3% profit
    first_target_exit_size: float = 50.0  # Exit 50% of position

    second_target_percent: float = 5.0  # Exit 25% at 5% profit
    second_target_exit_size: float = 50.0  # Exit 50% of remainder

    # Trailing for remainder
    trail_remainder: bool = True

    def validate(self) -> tuple[bool, List[str]]:
        """Validate target config"""
        errors = []

        if error := self.validate_positive(self.min_risk_reward_ratio, "min_risk_reward_ratio"):
            errors.append(error)

        if self.default_risk_reward_ratio < self.min_risk_reward_ratio:
            errors.append("Default R:R cannot be less than minimum R:R")

        if self.first_target_percent >= self.second_target_percent:
            errors.append("First target must be less than second target")

        if error := self.validate_percentage(self.first_target_exit_size, "first_target_exit_size"):
            errors.append(error)

        if error := self.validate_percentage(self.second_target_exit_size, "second_target_exit_size"):
            errors.append(error)

        return (len(errors) == 0, errors)


@dataclass
class CircuitBreaker(ValidationMixin):
    """
    Circuit breaker configuration
    Automatic trading halts on extreme conditions
    """

    enabled: bool = True

    # Drawdown-based circuit breakers
    halt_on_5_percent_drawdown: bool = True
    reduce_size_on_5_percent: bool = True
    size_reduction_percent: float = 50.0  # Reduce to 50%

    halt_on_10_percent_drawdown: bool = True
    stop_new_trades_on_10_percent: bool = True

    halt_on_15_percent_drawdown: bool = True
    close_all_positions_on_15_percent: bool = True

    # Consecutive loss circuit breaker
    halt_after_consecutive_losses: int = 3
    halt_duration_minutes: int = 60

    # Daily loss circuit breaker
    halt_on_daily_limit: bool = True

    # System error circuit breaker
    halt_on_api_failures: bool = True
    max_api_failures: int = 3

    # Manual override
    allow_manual_override: bool = True
    require_password_for_override: bool = True

    def validate(self) -> tuple[bool, List[str]]:
        """Validate circuit breaker config"""
        errors = []

        if error := self.validate_percentage(self.size_reduction_percent, "size_reduction_percent"):
            errors.append(error)

        if self.halt_after_consecutive_losses < 2:
            errors.append("Consecutive loss threshold must be at least 2")

        if self.max_api_failures < 1:
            errors.append("Max API failures must be at least 1")

        return (len(errors) == 0, errors)


@dataclass
class PositionRiskRules(ValidationMixin):
    """Position-level risk rules"""

    # Correlation limits
    max_correlated_positions: int = 2
    correlation_threshold: float = 0.7  # 0.7 = highly correlated

    # Sector concentration
    max_sector_exposure_percent: float = 40.0  # Max 40% in one sector

    # Volatility limits
    avoid_high_volatility_stocks: bool = True
    max_daily_volatility_percent: float = 5.0  # Skip if daily ATR > 5%

    # Liquidity requirements
    min_daily_volume: int = 100000  # Min 100k shares daily volume
    min_market_cap_crores: float = 1000.0  # ₹1000 crore min

    def validate(self) -> tuple[bool, List[str]]:
        """Validate position risk rules"""
        errors = []

        if error := self.validate_range(self.correlation_threshold, 0.0, 1.0, "correlation_threshold"):
            errors.append(error)

        if error := self.validate_percentage(self.max_sector_exposure_percent, "max_sector_exposure_percent"):
            errors.append(error)

        if error := self.validate_positive(self.min_daily_volume, "min_daily_volume"):
            errors.append(error)

        return (len(errors) == 0, errors)


@dataclass
class RiskConfig(BaseConfig, ValidationMixin):
    """
    Main Risk Management Configuration

    Aggregates all risk-related settings
    Implements Defense-in-Depth strategy with multiple layers
    """

    # Sub-configurations (Composition Pattern)
    loss_limits: LossLimits = field(default_factory=LossLimits)
    stop_loss: StopLossConfig = field(default_factory=StopLossConfig)
    targets: TargetConfig = field(default_factory=TargetConfig)
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    position_rules: PositionRiskRules = field(default_factory=PositionRiskRules)

    # Global risk switch
    risk_management_enabled: bool = True
    strict_mode: bool = True  # No override allowed in strict mode

    # Risk reporting
    daily_risk_report: bool = True
    alert_on_limit_approach: bool = True
    alert_threshold_percent: float = 80.0  # Alert at 80% of limit

    def validate(self) -> tuple[bool, List[str]]:
        """Validate risk configuration"""
        errors = []

        # Validate all sub-configurations
        for sub_config in [self.loss_limits, self.stop_loss, self.targets,
                          self.circuit_breaker, self.position_rules]:
            is_valid, sub_errors = sub_config.validate()
            errors.extend(sub_errors)

        # Validate alert threshold
        if error := self.validate_percentage(self.alert_threshold_percent, "alert_threshold_percent"):
            errors.append(error)

        return (len(errors) == 0, errors)

    def from_dict(self, data: Dict[str, Any]) -> 'RiskConfig':
        """Create from dictionary"""
        if 'loss_limits' in data:
            data['loss_limits'] = LossLimits(**data['loss_limits'])
        if 'stop_loss' in data:
            data['stop_loss'] = StopLossConfig(**data['stop_loss'])
        if 'targets' in data:
            data['targets'] = TargetConfig(**data['targets'])
        if 'circuit_breaker' in data:
            data['circuit_breaker'] = CircuitBreaker(**data['circuit_breaker'])
        if 'position_rules' in data:
            data['position_rules'] = PositionRiskRules(**data['position_rules'])

        return RiskConfig(**data)

    def get_summary(self) -> str:
        """Human-readable summary"""
        return f"""
Risk Management Configuration Summary:
- Risk Management: {'Enabled' if self.risk_management_enabled else 'DISABLED'}
- Strict Mode: {'ON' if self.strict_mode else 'OFF'}
- Per-Trade Risk: {self.loss_limits.risk_per_trade_percent}%
- Daily Loss Limit: {self.loss_limits.max_daily_loss_percent}%
- Monthly Drawdown Limit: {self.loss_limits.max_monthly_drawdown_percent}%
- Default Stop-Loss: {self.stop_loss.default_sl_percent}%
- Min Risk:Reward: {self.targets.min_risk_reward_ratio}:1
- Circuit Breakers: {'Enabled' if self.circuit_breaker.enabled else 'Disabled'}
- Trailing Stops: {'Enabled' if self.stop_loss.trailing_sl_enabled else 'Disabled'}
        """.strip()

    def get_max_risk_amount(self, capital: float) -> float:
        """Calculate maximum risk amount per trade"""
        return capital * self.loss_limits.risk_per_trade_percent / 100.0

    def calculate_position_size(self, capital: float, entry_price: float,
                               stop_loss_price: float) -> int:
        """
        Calculate position size based on risk

        Formula: Position Size = Risk Amount / (Entry - Stop Loss)
        """
        risk_amount = self.get_max_risk_amount(capital)
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            return 0

        position_size = int(risk_amount / risk_per_share)
        return max(1, position_size)  # At least 1 share
