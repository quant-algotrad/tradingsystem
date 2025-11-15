"""
Risk Management System
Chain of Responsibility pattern for modular risk checks

Components:
- Base Validator: Abstract risk validator interface
- Concrete Validators: Specific risk checks
- Risk Manager: Coordinates all validators

Pattern: Chain of Responsibility
- Each validator handles one risk aspect
- Easy to add/remove/reorder validators
- Clear separation of concerns

Available Validators:
- MaxDrawdownValidator: Daily loss limits
- PositionLimitValidator: Max concurrent positions
- DuplicatePositionValidator: No duplicate positions
- PositionSizeValidator: Max position size %
- RiskPerTradeValidator: Max risk % per trade
- CapitalValidator: Minimum capital reserve
- MarketHoursValidator: Trading hours check
- ConcentrationValidator: Sector concentration limits

Usage:
    from src.risk import get_risk_manager

    manager = get_risk_manager()
    passed, results = manager.validate_trade(trade_data)

    if not passed:
        print("Rejected:", results[0].reason)
"""

from .base_validator import IRiskValidator, RiskValidationResult
from .validators import (
    MaxDrawdownValidator,
    PositionLimitValidator,
    DuplicatePositionValidator,
    PositionSizeValidator,
    RiskPerTradeValidator,
    CapitalValidator,
    MarketHoursValidator,
    ConcentrationValidator
)
from .risk_manager import RiskManager, get_risk_manager, validate_trade

__all__ = [
    # Base
    'IRiskValidator',
    'RiskValidationResult',

    # Validators
    'MaxDrawdownValidator',
    'PositionLimitValidator',
    'DuplicatePositionValidator',
    'PositionSizeValidator',
    'RiskPerTradeValidator',
    'CapitalValidator',
    'MarketHoursValidator',
    'ConcentrationValidator',

    # Manager
    'RiskManager',
    'get_risk_manager',
    'validate_trade',
]

__version__ = '1.0.0'
