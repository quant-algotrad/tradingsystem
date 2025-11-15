"""
Risk Manager
Centralized risk management using Chain of Responsibility

Pattern: Chain of Responsibility + Facade
- Manages all risk validators
- Provides simple interface for risk checks
- Easy to configure risk rules
"""

from typing import List, Dict, Any, Optional
from src.risk.base_validator import IRiskValidator, RiskValidationResult
from src.risk.validators import (
    MaxDrawdownValidator,
    PositionLimitValidator,
    DuplicatePositionValidator,
    PositionSizeValidator,
    RiskPerTradeValidator,
    CapitalValidator,
    MarketHoursValidator,
    ConcentrationValidator
)
from src.utils import get_logger

logger = get_logger(__name__)


class RiskManager:
    """
    Centralized risk management system

    Pattern: Facade Pattern
    - Simple interface for complex risk validation
    - Hides validator chain complexity

    Pattern: Chain of Responsibility
    - Runs trade through chain of validators
    - Each validator checks one specific risk rule

    Usage:
        manager = RiskManager()
        passed, results = manager.validate_trade(trade_data)
        if not passed:
            print("Trade rejected:", results[0].reason)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize risk manager

        Args:
            config: Risk configuration dict
        """
        self.config = config or {}
        self._validators: List[IRiskValidator] = []

        # Initialize default validators
        self._init_default_validators()

        logger.info(f"Risk Manager initialized with {len(self._validators)} validators")

    def _init_default_validators(self):
        """Initialize default risk validators"""
        # Max drawdown check
        self.add_validator(
            MaxDrawdownValidator(
                max_drawdown_percent=self.config.get('max_drawdown_percent', 5.0)
            )
        )

        # Position limit check
        self.add_validator(
            PositionLimitValidator(
                max_positions=self.config.get('max_positions', 5)
            )
        )

        # No duplicate positions
        self.add_validator(DuplicatePositionValidator())

        # Position size check
        self.add_validator(
            PositionSizeValidator(
                max_position_percent=self.config.get('max_position_percent', 20.0)
            )
        )

        # Risk per trade check
        self.add_validator(
            RiskPerTradeValidator(
                max_risk_percent=self.config.get('max_risk_percent', 2.0)
            )
        )

        # Capital check
        self.add_validator(
            CapitalValidator(
                min_capital_reserve=self.config.get('min_capital_reserve', 1000.0)
            )
        )

        # Market hours check
        self.add_validator(MarketHoursValidator())

        # Concentration check
        self.add_validator(
            ConcentrationValidator(
                max_sector_concentration=self.config.get('max_sector_concentration', 40.0)
            )
        )

    def add_validator(self, validator: IRiskValidator):
        """
        Add a risk validator

        Args:
            validator: Validator to add
        """
        self._validators.append(validator)
        logger.debug(f"Added validator: {validator.get_name()}")

    def remove_validator(self, validator_name: str):
        """
        Remove a risk validator

        Args:
            validator_name: Name of validator to remove
        """
        self._validators = [
            v for v in self._validators
            if v.get_name() != validator_name
        ]
        logger.debug(f"Removed validator: {validator_name}")

    def validate_trade(
        self,
        trade_data: Dict[str, Any],
        stop_on_first_failure: bool = True
    ) -> tuple[bool, List[RiskValidationResult]]:
        """
        Validate trade against all risk rules

        Args:
            trade_data: Trade data to validate
            stop_on_first_failure: Stop on first failed check (default: True)

        Returns:
            (passed: bool, results: List[RiskValidationResult])
        """
        results = []
        all_passed = True

        for validator in self._validators:
            result = validator.validate(trade_data)
            results.append(result)

            if not result.passed:
                all_passed = False

                # Log failure
                logger.warning(
                    f"Risk check failed: {validator.get_name()} - {result.reason}"
                )

                # Stop on first failure if configured
                if stop_on_first_failure:
                    break

        if all_passed:
            logger.info("✅ All risk checks passed")
        else:
            failed_checks = [r for r in results if not r.passed]
            logger.warning(
                f"❌ {len(failed_checks)} risk check(s) failed: "
                f"{', '.join(r.validator_name for r in failed_checks)}"
            )

        return all_passed, results

    def get_summary(self, results: List[RiskValidationResult]) -> Dict[str, Any]:
        """
        Get summary of validation results

        Args:
            results: Validation results

        Returns:
            Summary dict
        """
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        return {
            'total_checks': len(results),
            'passed': len(passed),
            'failed': len(failed),
            'all_passed': len(failed) == 0,
            'failed_checks': [
                {
                    'validator': r.validator_name,
                    'reason': r.reason,
                    'severity': r.severity
                }
                for r in failed
            ],
            'passed_checks': [r.validator_name for r in passed]
        }

    def get_active_validators(self) -> List[str]:
        """Get list of active validator names"""
        return [v.get_name() for v in self._validators]

    def update_config(self, **kwargs):
        """
        Update risk configuration

        Args:
            **kwargs: Configuration parameters to update
        """
        self.config.update(kwargs)

        # Re-initialize validators with new config
        self._validators.clear()
        self._init_default_validators()

        logger.info("Risk configuration updated")


# ========================================
# Global Instance
# ========================================

_risk_manager: Optional[RiskManager] = None


def get_risk_manager(config: Dict[str, Any] = None) -> RiskManager:
    """
    Get global risk manager instance

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        RiskManager instance
    """
    global _risk_manager

    if _risk_manager is None:
        _risk_manager = RiskManager(config)

    return _risk_manager


# ========================================
# Convenience Functions
# ========================================

def validate_trade(trade_data: Dict[str, Any]) -> tuple[bool, List[RiskValidationResult]]:
    """
    Convenience function to validate trade

    Args:
        trade_data: Trade data

    Returns:
        (passed, results)
    """
    manager = get_risk_manager()
    return manager.validate_trade(trade_data)
