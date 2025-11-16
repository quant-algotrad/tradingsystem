"""
Risk Validators
Concrete risk validation implementations

Pattern: Chain of Responsibility
- Each validator checks one specific risk rule
- Can be combined in any order
- Easy to enable/disable individual rules
"""

from typing import Dict, Any
from src.risk.base_validator import IRiskValidator, RiskValidationResult
from src.utils import get_logger

logger = get_logger(__name__)


class MaxDrawdownValidator(IRiskValidator):
    """Validate daily loss doesn't exceed max drawdown"""

    def __init__(self, max_drawdown_percent: float = 5.0):
        """
        Initialize max drawdown validator

        Args:
            max_drawdown_percent: Max allowed daily loss % (default: 5%)
        """
        super().__init__()
        self.max_drawdown_percent = max_drawdown_percent

    def get_name(self) -> str:
        return "MaxDrawdownValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check if daily loss is within limits"""
        current_drawdown = trade_data.get('current_daily_loss_percent', 0.0)

        if abs(current_drawdown) >= self.max_drawdown_percent:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Daily loss {abs(current_drawdown):.1f}% ≥ max {self.max_drawdown_percent}%",
                severity="CRITICAL",
                details={
                    'current_drawdown': current_drawdown,
                    'max_drawdown': self.max_drawdown_percent
                }
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason=f"Drawdown OK ({abs(current_drawdown):.1f}% < {self.max_drawdown_percent}%)"
        )


class PositionLimitValidator(IRiskValidator):
    """Validate position count limits"""

    def __init__(self, max_positions: int = 5):
        """
        Initialize position limit validator

        Args:
            max_positions: Max number of concurrent positions (default: 5)
        """
        super().__init__()
        self.max_positions = max_positions

    def get_name(self) -> str:
        return "PositionLimitValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check if position count is within limits"""
        current_positions = trade_data.get('current_position_count', 0)

        if current_positions >= self.max_positions:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Position limit reached: {current_positions}/{self.max_positions}",
                severity="WARNING",
                details={
                    'current_positions': current_positions,
                    'max_positions': self.max_positions
                }
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason=f"Positions OK ({current_positions}/{self.max_positions})"
        )


class DuplicatePositionValidator(IRiskValidator):
    """Validate no duplicate positions in same symbol"""

    def __init__(self):
        """Initialize duplicate position validator"""
        super().__init__()

    def get_name(self) -> str:
        return "DuplicatePositionValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check if position already exists in symbol"""
        symbol = trade_data.get('symbol', '')
        existing_positions = trade_data.get('existing_position_symbols', [])

        if symbol in existing_positions:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Already have position in {symbol}",
                severity="WARNING",
                details={'symbol': symbol}
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason="No duplicate position"
        )


class PositionSizeValidator(IRiskValidator):
    """Validate position size limits"""

    def __init__(self, max_position_percent: float = 20.0):
        """
        Initialize position size validator

        Args:
            max_position_percent: Max % of capital per position (default: 20%)
        """
        super().__init__()
        self.max_position_percent = max_position_percent

    def get_name(self) -> str:
        return "PositionSizeValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check if position size is within limits"""
        position_value = trade_data.get('position_value', 0)
        capital = trade_data.get('capital', 1)

        position_percent = (position_value / capital * 100) if capital > 0 else 0

        if position_percent > self.max_position_percent:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Position size {position_percent:.1f}% > max {self.max_position_percent}%",
                severity="WARNING",
                details={
                    'position_percent': position_percent,
                    'max_percent': self.max_position_percent
                }
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason=f"Position size OK ({position_percent:.1f}%)"
        )


class RiskPerTradeValidator(IRiskValidator):
    """Validate risk per trade limits"""

    def __init__(self, max_risk_percent: float = 2.0):
        """
        Initialize risk per trade validator

        Args:
            max_risk_percent: Max % risk per trade (default: 2%)
        """
        super().__init__()
        self.max_risk_percent = max_risk_percent

    def get_name(self) -> str:
        return "RiskPerTradeValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check if risk per trade is within limits"""
        risk_percent = trade_data.get('risk_percent', 0)

        if risk_percent > self.max_risk_percent:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Risk {risk_percent:.1f}% > max {self.max_risk_percent}%",
                severity="WARNING",
                details={
                    'risk_percent': risk_percent,
                    'max_risk_percent': self.max_risk_percent
                }
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason=f"Risk per trade OK ({risk_percent:.1f}%)"
        )


class CapitalValidator(IRiskValidator):
    """Validate sufficient capital available"""

    def __init__(self, min_capital_reserve: float = 1000.0):
        """
        Initialize capital validator

        Args:
            min_capital_reserve: Min capital to keep in reserve (default: ₹1000)
        """
        super().__init__()
        self.min_capital_reserve = min_capital_reserve

    def get_name(self) -> str:
        return "CapitalValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check if sufficient capital available"""
        capital = trade_data.get('capital', 0)
        position_value = trade_data.get('position_value', 0)

        remaining_capital = capital - position_value

        if remaining_capital < self.min_capital_reserve:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Insufficient capital: ₹{remaining_capital:.0f} < ₹{self.min_capital_reserve:.0f}",
                severity="CRITICAL",
                details={
                    'remaining_capital': remaining_capital,
                    'min_reserve': self.min_capital_reserve
                }
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason=f"Capital OK (₹{remaining_capital:.0f} remaining)"
        )


class MarketHoursValidator(IRiskValidator):
    """Validate trading within market hours"""

    def __init__(self, market_open_hour: int = 9, market_open_minute: int = 15,
                 market_close_hour: int = 15, market_close_minute: int = 30):
        """
        Initialize market hours validator

        Args:
            market_open_hour: Market open hour (default: 9)
            market_open_minute: Market open minute (default: 15)
            market_close_hour: Market close hour (default: 15)
            market_close_minute: Market close minute (default: 30)
        """
        super().__init__()
        self.market_open = (market_open_hour, market_open_minute)
        self.market_close = (market_close_hour, market_close_minute)

    def get_name(self) -> str:
        return "MarketHoursValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check if within market hours"""
        from datetime import datetime

        now = datetime.now()
        current_time = (now.hour, now.minute)

        # Skip check for swing/positional trades
        position_type = trade_data.get('position_type', 'SWING')
        if position_type != 'INTRADAY':
            return RiskValidationResult(
                passed=True,
                validator_name=self.get_name(),
                reason="Market hours check skipped for swing trade"
            )

        # Check if within market hours
        if not (self.market_open <= current_time <= self.market_close):
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Outside market hours ({now.hour}:{now.minute:02d})",
                severity="WARNING",
                details={'current_time': f"{now.hour}:{now.minute:02d}"}
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason="Within market hours"
        )


class ConcentrationValidator(IRiskValidator):
    """Validate portfolio concentration limits"""

    def __init__(self, max_sector_concentration: float = 40.0):
        """
        Initialize concentration validator

        Args:
            max_sector_concentration: Max % in single sector (default: 40%)
        """
        super().__init__()
        self.max_sector_concentration = max_sector_concentration

    def get_name(self) -> str:
        return "ConcentrationValidator"

    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """Check portfolio concentration"""
        sector = trade_data.get('sector', 'UNKNOWN')
        sector_exposure = trade_data.get('sector_exposure_percent', 0)

        if sector_exposure > self.max_sector_concentration:
            return RiskValidationResult(
                passed=False,
                validator_name=self.get_name(),
                reason=f"Sector concentration {sector_exposure:.1f}% > max {self.max_sector_concentration}%",
                severity="WARNING",
                details={
                    'sector': sector,
                    'exposure_percent': sector_exposure
                }
            )

        return RiskValidationResult(
            passed=True,
            validator_name=self.get_name(),
            reason=f"Concentration OK ({sector}: {sector_exposure:.1f}%)"
        )
