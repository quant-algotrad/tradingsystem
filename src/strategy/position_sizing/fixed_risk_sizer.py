"""
Fixed Risk Position Sizer
Risk a fixed percentage of capital per trade

Pattern: Strategy Pattern
- Most common position sizing method
- Simple and effective
- Default choice for most traders
"""

from typing import Dict, Any
from src.strategy.position_sizing.base_sizer import IPositionSizer, PositionSizeResult


class FixedRiskSizer(IPositionSizer):
    """
    Fixed Risk Position Sizing

    Logic:
    - Risk fixed % of capital per trade (default 1%)
    - Position size = (Capital × Risk%) ÷ Risk per share
    - Most common and recommended method

    Example:
        Capital: ₹50,000
        Risk per trade: 1% = ₹500
        Entry: ₹100, Stop: ₹98 (₹2 risk per share)
        Position size: ₹500 ÷ ₹2 = 250 shares
    """

    def __init__(self, risk_percent: float = 1.0, max_position_percent: float = 20.0):
        """
        Initialize fixed risk sizer

        Args:
            risk_percent: % of capital to risk per trade (default: 1%)
            max_position_percent: Max % of capital per position (default: 20%)
        """
        self.risk_percent = risk_percent
        self.max_position_percent = max_position_percent

    def get_name(self) -> str:
        return "FIXED_RISK"

    def get_description(self) -> str:
        return f"Risk {self.risk_percent}% of capital per trade (max {self.max_position_percent}% position size)"

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        **kwargs
    ) -> PositionSizeResult:
        """
        Calculate position size using fixed risk method

        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            **kwargs: Unused

        Returns:
            PositionSizeResult
        """
        # Validate inputs
        valid, error = self.validate_inputs(capital, entry_price, stop_loss)
        if not valid:
            return PositionSizeResult(
                quantity=0,
                position_value=0,
                risk_amount=0,
                risk_percent=0,
                method=self.get_name(),
                confidence=0,
                details={'error': error}
            )

        # Calculate risk amount
        risk_amount = capital * (self.risk_percent / 100.0)

        # Calculate risk per share
        risk_per_share = self.calculate_risk_per_share(entry_price, stop_loss)

        if risk_per_share == 0:
            return PositionSizeResult(
                quantity=0,
                position_value=0,
                risk_amount=0,
                risk_percent=0,
                method=self.get_name(),
                confidence=0,
                details={'error': 'Stop loss equals entry price'}
            )

        # Calculate quantity based on risk
        quantity = int(risk_amount / risk_per_share)

        # Calculate position value
        position_value = quantity * entry_price

        # Check max position size limit
        max_position_value = capital * (self.max_position_percent / 100.0)

        if position_value > max_position_value:
            # Reduce quantity to fit max position size
            quantity = int(max_position_value / entry_price)
            position_value = quantity * entry_price

        # Check if we can afford it
        if position_value > capital:
            quantity = int(capital / entry_price)
            position_value = quantity * entry_price

        # Recalculate actual risk
        actual_risk_amount = quantity * risk_per_share
        actual_risk_percent = (actual_risk_amount / capital * 100) if capital > 0 else 0

        return PositionSizeResult(
            quantity=quantity,
            position_value=position_value,
            risk_amount=actual_risk_amount,
            risk_percent=actual_risk_percent,
            method=self.get_name(),
            confidence=100.0,
            details={
                'target_risk_percent': self.risk_percent,
                'actual_risk_percent': actual_risk_percent,
                'risk_per_share': risk_per_share,
                'max_position_percent': self.max_position_percent
            }
        )

    def set_risk_percent(self, risk_percent: float):
        """Update risk percentage"""
        self.risk_percent = risk_percent

    def set_max_position_percent(self, max_position_percent: float):
        """Update max position percentage"""
        self.max_position_percent = max_position_percent
