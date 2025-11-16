"""
Base Risk Validator
Chain of Responsibility pattern for risk validation

Pattern: Chain of Responsibility
- Each validator checks one specific risk rule
- Validators can be chained together
- Easy to add/remove risk rules
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class RiskValidationResult:
    """Result of risk validation"""
    passed: bool
    validator_name: str
    reason: str = ""
    severity: str = "INFO"  # INFO, WARNING, CRITICAL
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class IRiskValidator(ABC):
    """
    Abstract base class for risk validators

    Pattern: Chain of Responsibility
    - Each validator checks one aspect of risk
    - Can be chained with other validators
    - Returns validation result
    """

    def __init__(self):
        """Initialize risk validator"""
        self._next_validator: Optional[IRiskValidator] = None

    @abstractmethod
    def get_name(self) -> str:
        """Return validator name"""
        pass

    @abstractmethod
    def validate(self, trade_data: Dict[str, Any]) -> RiskValidationResult:
        """
        Validate trade against risk rule

        Args:
            trade_data: Dict containing trade information
                Required keys: symbol, quantity, entry_price, stop_loss, etc.

        Returns:
            RiskValidationResult
        """
        pass

    def set_next(self, validator: 'IRiskValidator') -> 'IRiskValidator':
        """
        Set next validator in chain

        Args:
            validator: Next validator

        Returns:
            The next validator (for method chaining)
        """
        self._next_validator = validator
        return validator

    def validate_chain(self, trade_data: Dict[str, Any]) -> list[RiskValidationResult]:
        """
        Validate through entire chain

        Args:
            trade_data: Trade data to validate

        Returns:
            List of validation results from all validators
        """
        results = []

        # Validate this validator
        result = self.validate(trade_data)
        results.append(result)

        # Continue chain if not blocked
        if self._next_validator:
            next_results = self._next_validator.validate_chain(trade_data)
            results.extend(next_results)

        return results
