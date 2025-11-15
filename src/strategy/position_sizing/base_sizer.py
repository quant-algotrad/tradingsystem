"""
Base Position Sizer Interface
Defines the contract for position sizing strategies

Pattern: Strategy Pattern
- Different position sizing algorithms
- Easy to switch between methods
- Each strategy has its own risk management approach
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class PositionSizeResult:
    """Result of position sizing calculation"""
    quantity: int  # Number of shares/contracts
    position_value: float  # Total position value
    risk_amount: float  # Amount at risk
    risk_percent: float  # % of capital at risk
    method: str  # Sizing method used
    confidence: float = 100.0  # Confidence in this sizing (0-100)

    # Metadata
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class IPositionSizer(ABC):
    """
    Abstract base class for position sizing strategies

    Pattern: Strategy Pattern
    - Each sizer implements different sizing logic
    - Can be swapped at runtime
    - Consistent interface

    Common position sizing methods:
    - Fixed Risk: Risk fixed % of capital per trade
    - Kelly Criterion: Optimal bet sizing based on win rate
    - Fixed Size: Always buy same number of shares
    - Percent Capital: Use fixed % of capital
    - Volatility Adjusted: Size based on ATR/volatility
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return position sizer name"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return position sizer description"""
        pass

    @abstractmethod
    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        **kwargs
    ) -> PositionSizeResult:
        """
        Calculate position size

        Args:
            capital: Available trading capital
            entry_price: Entry price per share
            stop_loss: Stop loss price
            **kwargs: Additional parameters (ATR, win_rate, etc.)

        Returns:
            PositionSizeResult with quantity and risk metrics
        """
        pass

    def validate_inputs(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float
    ) -> tuple[bool, str]:
        """
        Validate input parameters

        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price

        Returns:
            (is_valid, error_message)
        """
        if capital <= 0:
            return False, "Capital must be positive"

        if entry_price <= 0:
            return False, "Entry price must be positive"

        if stop_loss <= 0:
            return False, "Stop loss must be positive"

        # Check stop loss is on correct side
        # For long positions, stop should be below entry
        # For short positions, stop should be above entry
        # We'll assume long if stop < entry, short if stop > entry

        return True, ""

    def calculate_risk_per_share(self, entry_price: float, stop_loss: float) -> float:
        """
        Calculate risk per share

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price

        Returns:
            Absolute risk per share
        """
        return abs(entry_price - stop_loss)
