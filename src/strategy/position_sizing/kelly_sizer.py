"""
Kelly Criterion Position Sizer
Optimal bet sizing based on edge and win rate

Pattern: Strategy Pattern
- Mathematically optimal position sizing
- Maximizes long-term growth
- Requires win rate and avg win/loss data
"""

from typing import Dict, Any
from src.strategy.position_sizing.base_sizer import IPositionSizer, PositionSizeResult


class KellyCriterionSizer(IPositionSizer):
    """
    Kelly Criterion Position Sizing

    Logic:
    - Kelly% = (Win% × Avg Win - Loss% × Avg Loss) ÷ Avg Win
    - Mathematically optimal for maximizing growth
    - Aggressive - often use fractional Kelly (e.g., 0.25× Kelly)

    Example:
        Win rate: 55%, Avg win: 6%, Avg loss: 3%
        Kelly% = (0.55 × 6 - 0.45 × 3) ÷ 6 = 32.5%
        Fractional Kelly (0.25×) = 8.1%

    Warning: Full Kelly can be very aggressive. Use fractional Kelly!
    """

    def __init__(
        self,
        win_rate: float = 0.55,
        avg_win: float = 6.0,
        avg_loss: float = 3.0,
        kelly_fraction: float = 0.25,
        max_position_percent: float = 20.0
    ):
        """
        Initialize Kelly Criterion sizer

        Args:
            win_rate: Historical win rate (0-1, default: 0.55 = 55%)
            avg_win: Average win % (default: 6%)
            avg_loss: Average loss % (default: 3%)
            kelly_fraction: Fraction of Kelly to use (default: 0.25 = Quarter Kelly)
            max_position_percent: Max % of capital per position (default: 20%)
        """
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
        self.kelly_fraction = kelly_fraction
        self.max_position_percent = max_position_percent

    def get_name(self) -> str:
        return "KELLY_CRITERION"

    def get_description(self) -> str:
        return f"Kelly Criterion ({self.kelly_fraction:.0%} Kelly) - Optimal growth sizing based on edge"

    def calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        win_rate: float = None,
        avg_win: float = None,
        avg_loss: float = None,
        **kwargs
    ) -> PositionSizeResult:
        """
        Calculate position size using Kelly Criterion

        Args:
            capital: Available capital
            entry_price: Entry price
            stop_loss: Stop loss price
            win_rate: Override default win rate
            avg_win: Override default avg win %
            avg_loss: Override default avg loss %
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

        # Use provided values or defaults
        w = win_rate if win_rate is not None else self.win_rate
        avg_w = avg_win if avg_win is not None else self.avg_win
        avg_l = avg_loss if avg_loss is not None else self.avg_loss

        # Calculate Kelly %
        # Kelly% = (p × b - q) / b
        # Where: p = win rate, q = loss rate, b = avg_win / avg_loss
        loss_rate = 1 - w
        b = avg_w / avg_l if avg_l > 0 else 1.0

        kelly_percent = (w * b - loss_rate) / b

        # Apply fractional Kelly
        kelly_percent = kelly_percent * self.kelly_fraction

        # Ensure non-negative
        if kelly_percent <= 0:
            return PositionSizeResult(
                quantity=0,
                position_value=0,
                risk_amount=0,
                risk_percent=0,
                method=self.get_name(),
                confidence=0,
                details={
                    'error': 'Negative Kelly - no edge detected',
                    'kelly_percent': kelly_percent,
                    'win_rate': w
                }
            )

        # Cap at max position size
        kelly_percent = min(kelly_percent * 100, self.max_position_percent)

        # Calculate position value based on Kelly %
        target_position_value = capital * (kelly_percent / 100.0)

        # Calculate quantity
        quantity = int(target_position_value / entry_price)

        # Actual position value
        position_value = quantity * entry_price

        # Ensure we can afford it
        if position_value > capital:
            quantity = int(capital / entry_price)
            position_value = quantity * entry_price

        # Calculate risk
        risk_per_share = self.calculate_risk_per_share(entry_price, stop_loss)
        risk_amount = quantity * risk_per_share
        risk_percent = (risk_amount / capital * 100) if capital > 0 else 0

        # Confidence based on data quality
        # More trades = more confidence
        confidence = min(100.0, w * 100 + 20)  # Simple heuristic

        return PositionSizeResult(
            quantity=quantity,
            position_value=position_value,
            risk_amount=risk_amount,
            risk_percent=risk_percent,
            method=self.get_name(),
            confidence=confidence,
            details={
                'kelly_percent': kelly_percent,
                'kelly_fraction': self.kelly_fraction,
                'win_rate': w,
                'avg_win': avg_w,
                'avg_loss': avg_l,
                'edge': w * avg_w - loss_rate * avg_l
            }
        )

    def update_stats(self, win_rate: float, avg_win: float, avg_loss: float):
        """
        Update Kelly parameters based on recent performance

        Args:
            win_rate: Recent win rate (0-1)
            avg_win: Recent average win %
            avg_loss: Recent average loss %
        """
        self.win_rate = win_rate
        self.avg_win = avg_win
        self.avg_loss = avg_loss
