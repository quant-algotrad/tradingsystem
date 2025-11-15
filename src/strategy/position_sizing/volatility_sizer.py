"""
Volatility-Adjusted Position Sizer
Size positions based on ATR/volatility

Pattern: Strategy Pattern
- Larger positions in low volatility
- Smaller positions in high volatility
- Risk-adjusted sizing
"""

from typing import Dict, Any
from src.strategy.position_sizing.base_sizer import IPositionSizer, PositionSizeResult


class VolatilityAdjustedSizer(IPositionSizer):
    """
    Volatility-Adjusted Position Sizing

    Logic:
    - Use ATR to determine volatility
    - Risk fixed ATR multiple per trade
    - Lower volatility → larger position
    - Higher volatility → smaller position

    Example:
        Capital: ₹50,000
        Target risk: 1% = ₹500
        ATR: ₹5
        ATR multiplier: 2×
        Risk per share: ₹10 (2 × ₹5)
        Position size: ₹500 ÷ ₹10 = 50 shares
    """

    def __init__(
        self,
        risk_percent: float = 1.0,
        atr_multiplier: float = 2.0,
        max_position_percent: float = 20.0,
        use_stop_if_no_atr: bool = True
    ):
        """
        Initialize volatility-adjusted sizer

        Args:
            risk_percent: % of capital to risk (default: 1%)
            atr_multiplier: ATR multiplier for stop distance (default: 2.0)
            max_position_percent: Max % of capital per position (default: 20%)
            use_stop_if_no_atr: Fall back to stop loss if ATR unavailable (default: True)
        """
        self.risk_percent = risk_percent
        self.atr_multiplier = atr_multiplier
        self.max_position_percent = max_position_percent
        self.use_stop_if_no_atr = use_stop_if_no_atr

    def get_name(self) -> str:
        return "VOLATILITY_ADJUSTED"

    def get_description(self) -> str:
        return f"ATR-based sizing: Risk {self.risk_percent}% using {self.atr_multiplier}× ATR"

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        atr: float = None,
        **kwargs
    ) -> PositionSizeResult:
        """
        Calculate position size using volatility adjustment

        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price (fallback if no ATR)
            atr: Average True Range value
            **kwargs: Additional parameters

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

        # Determine risk per share using ATR or stop loss
        if atr and atr > 0:
            # Use ATR-based risk
            risk_per_share = atr * self.atr_multiplier
            used_method = f"ATR ({self.atr_multiplier}×)"
            confidence = 100.0
        elif self.use_stop_if_no_atr:
            # Fall back to stop loss
            risk_per_share = self.calculate_risk_per_share(entry_price, stop_loss)
            used_method = "Stop Loss (no ATR)"
            confidence = 70.0  # Lower confidence without ATR
        else:
            return PositionSizeResult(
                quantity=0,
                position_value=0,
                risk_amount=0,
                risk_percent=0,
                method=self.get_name(),
                confidence=0,
                details={'error': 'ATR not provided and fallback disabled'}
            )

        if risk_per_share == 0:
            return PositionSizeResult(
                quantity=0,
                position_value=0,
                risk_amount=0,
                risk_percent=0,
                method=self.get_name(),
                confidence=0,
                details={'error': 'Risk per share is zero'}
            )

        # Calculate quantity
        quantity = int(risk_amount / risk_per_share)

        # Calculate position value
        position_value = quantity * entry_price

        # Check max position size
        max_position_value = capital * (self.max_position_percent / 100.0)

        if position_value > max_position_value:
            quantity = int(max_position_value / entry_price)
            position_value = quantity * entry_price

        # Check affordability
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
            confidence=confidence,
            details={
                'atr': atr,
                'atr_multiplier': self.atr_multiplier,
                'risk_per_share': risk_per_share,
                'sizing_method': used_method,
                'target_risk_percent': self.risk_percent
            }
        )
