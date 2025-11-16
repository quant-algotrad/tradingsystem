"""
Trade Decision Engine
Converts signals into actionable trade decisions with risk management

Patterns:
- Strategy Pattern: Different decision strategies
- Chain of Responsibility: Filter chain for trade validation
- Builder Pattern: Trade recommendation building
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.indicators.models import SignalValue
from src.strategy.signal_aggregator import AggregatedSignal
from src.config import get_risk_config, get_trading_config
from src.database.db_connector import DatabaseConnector
from src.utils import get_logger

logger = get_logger(__name__)


class TradeAction(Enum):
    """Trade actions"""
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"
    HOLD = "HOLD"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"


class RejectionReason(Enum):
    """Reasons for trade rejection"""
    LOW_CONFIDENCE = "Confidence below threshold"
    POSITION_LIMIT = "Position limit reached"
    CAPITAL_INSUFFICIENT = "Insufficient capital"
    RISK_LIMIT = "Risk limit exceeded"
    MARKET_HOURS = "Outside trading hours"
    DUPLICATE_POSITION = "Already have position in symbol"
    INVALID_SIGNAL = "Invalid signal"
    CONFLICTING_TIMEFRAMES = "Timeframe conflict"


@dataclass
class TradeRecommendation:
    """
    Trade recommendation with complete trade details

    Contains entry, stop loss, targets, position sizing, and scoring
    """
    symbol: str
    timestamp: datetime
    action: TradeAction

    # Signal information
    signal_confidence: float  # 0-100
    signal_strength: float  # Weighted signal strength

    # Pricing
    entry_price: float
    stop_loss: float
    target_price: float

    # Position sizing
    quantity: int
    position_value: float
    risk_amount: float
    risk_percent: float

    # Scoring
    score: float  # Overall opportunity score (0-100)
    expected_return_percent: float
    risk_reward_ratio: float

    # Metadata
    strategy: str = "MULTI_INDICATOR"
    timeframe: str = "1d"
    position_type: str = "SWING"  # SWING or INTRADAY

    # Supporting data
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Risk metrics
    max_loss: float = 0.0
    potential_profit: float = 0.0

    def is_actionable(self) -> bool:
        """Check if recommendation is actionable"""
        return (
            self.action != TradeAction.HOLD and
            self.score >= 50 and
            self.quantity > 0 and
            len(self.warnings) == 0
        )

    def get_summary(self) -> str:
        """Get trade summary"""
        return (
            f"{self.action.value} {self.quantity} {self.symbol} @ ₹{self.entry_price:.2f} | "
            f"SL: ₹{self.stop_loss:.2f} | Target: ₹{self.target_price:.2f} | "
            f"Score: {self.score:.0f} | Confidence: {self.signal_confidence:.0f}%"
        )


@dataclass
class TradeDecision:
    """
    Trade decision with recommendation or rejection
    """
    symbol: str
    timestamp: datetime
    should_trade: bool

    recommendation: Optional[TradeRecommendation] = None
    rejection_reason: Optional[RejectionReason] = None
    details: Dict[str, Any] = field(default_factory=dict)


class TradeDecisionEngine:
    """
    Main trade decision engine

    Patterns:
    - Chain of Responsibility: Validation filters
    - Strategy Pattern: Position sizing strategies
    - Builder Pattern: Build trade recommendations

    Responsibilities:
    - Evaluate signals
    - Apply risk management
    - Calculate position sizing
    - Generate trade recommendations
    """

    def __init__(self, db_connector: Optional[DatabaseConnector] = None):
        """
        Initialize trade decision engine

        Args:
            db_connector: Database connector (creates new if None)
        """
        self.risk_config = get_risk_config()
        self.trading_config = get_trading_config()
        self.db = db_connector or DatabaseConnector()

        # Decision thresholds
        self.MIN_CONFIDENCE = 60.0  # Minimum signal confidence
        self.MIN_SCORE = 50.0  # Minimum opportunity score
        self.MIN_RISK_REWARD = 1.5  # Minimum risk:reward ratio

        # Get max position percent from trading config
        self.max_position_percent = self.trading_config.position_limits.max_position_size_percent

        logger.info("Trade Decision Engine initialized")

    def evaluate_signal(
        self,
        symbol: str,
        aggregated_signal: AggregatedSignal,
        current_price: float,
        timeframe: str = "1d",
        position_type: str = "SWING"
    ) -> TradeDecision:
        """
        Evaluate aggregated signal and decide on trade

        Args:
            symbol: Stock symbol
            aggregated_signal: Aggregated signal from multiple indicators
            current_price: Current market price
            timeframe: Timeframe for trade
            position_type: SWING or INTRADAY

        Returns:
            TradeDecision with recommendation or rejection
        """
        timestamp = datetime.now()

        # Step 1: Validate signal confidence
        if aggregated_signal.confidence < self.MIN_CONFIDENCE:
            return TradeDecision(
                symbol=symbol,
                timestamp=timestamp,
                should_trade=False,
                rejection_reason=RejectionReason.LOW_CONFIDENCE,
                details={'confidence': aggregated_signal.confidence}
            )

        # Step 2: Determine action from signal
        action = self._signal_to_action(aggregated_signal.signal, position_type)

        if action == TradeAction.HOLD:
            return TradeDecision(
                symbol=symbol,
                timestamp=timestamp,
                should_trade=False,
                rejection_reason=RejectionReason.INVALID_SIGNAL,
                details={'signal': aggregated_signal.signal.value}
            )

        # Step 3: Check position limits
        if not self._check_position_limits(symbol, position_type):
            return TradeDecision(
                symbol=symbol,
                timestamp=timestamp,
                should_trade=False,
                rejection_reason=RejectionReason.POSITION_LIMIT
            )

        # Step 4: Calculate entry, stop loss, and target
        levels = self._calculate_trade_levels(
            current_price,
            aggregated_signal,
            action
        )

        # Step 5: Calculate position size
        capital = self._get_available_capital()
        position_size = self._calculate_position_size(
            capital=capital,
            entry_price=levels['entry'],
            stop_loss=levels['stop_loss'],
            position_type=position_type
        )

        if position_size['quantity'] == 0:
            return TradeDecision(
                symbol=symbol,
                timestamp=timestamp,
                should_trade=False,
                rejection_reason=RejectionReason.CAPITAL_INSUFFICIENT
            )

        # Step 6: Calculate risk metrics
        risk_reward = self._calculate_risk_reward(
            entry=levels['entry'],
            stop_loss=levels['stop_loss'],
            target=levels['target']
        )

        if risk_reward < self.MIN_RISK_REWARD:
            return TradeDecision(
                symbol=symbol,
                timestamp=timestamp,
                should_trade=False,
                rejection_reason=RejectionReason.RISK_LIMIT,
                details={'risk_reward': risk_reward}
            )

        # Step 7: Calculate opportunity score
        score = self._calculate_opportunity_score(
            signal_confidence=aggregated_signal.confidence,
            consensus_strength=aggregated_signal.get_consensus_strength(),
            risk_reward=risk_reward,
            bullish_score=aggregated_signal.bullish_score,
            bearish_score=aggregated_signal.bearish_score
        )

        # Step 8: Build recommendation
        recommendation = TradeRecommendation(
            symbol=symbol,
            timestamp=timestamp,
            action=action,
            signal_confidence=aggregated_signal.confidence,
            signal_strength=aggregated_signal.bullish_score if action in [TradeAction.BUY] else aggregated_signal.bearish_score,
            entry_price=levels['entry'],
            stop_loss=levels['stop_loss'],
            target_price=levels['target'],
            quantity=position_size['quantity'],
            position_value=position_size['position_value'],
            risk_amount=position_size['risk_amount'],
            risk_percent=position_size['risk_percent'],
            score=score,
            expected_return_percent=self._calculate_expected_return(levels['entry'], levels['target']),
            risk_reward_ratio=risk_reward,
            timeframe=timeframe,
            position_type=position_type,
            reasons=aggregated_signal.reasons,
            max_loss=position_size['risk_amount'],
            potential_profit=position_size['quantity'] * (levels['target'] - levels['entry'])
        )

        # Add warnings if any
        self._add_warnings(recommendation, aggregated_signal)

        # Decide if actionable
        should_trade = recommendation.is_actionable()

        return TradeDecision(
            symbol=symbol,
            timestamp=timestamp,
            should_trade=should_trade,
            recommendation=recommendation,
            details={
                'score': score,
                'risk_reward': risk_reward,
                'confidence': aggregated_signal.confidence
            }
        )

    def _signal_to_action(self, signal: SignalValue, position_type: str) -> TradeAction:
        """Convert signal value to trade action"""
        if signal in [SignalValue.BUY, SignalValue.STRONG_BUY]:
            return TradeAction.BUY
        elif signal in [SignalValue.SELL, SignalValue.STRONG_SELL]:
            # For SWING, SELL means close long or short
            # For INTRADAY, SELL can be short
            if position_type == "INTRADAY":
                return TradeAction.SHORT
            else:
                return TradeAction.SELL
        else:
            return TradeAction.HOLD

    def _check_position_limits(self, symbol: str, position_type: str) -> bool:
        """Check if we can open new position"""
        try:
            # Get current positions
            if not self.db.conn:
                self.db.connect()

            positions = self.db.get_open_positions(position_type)

            # Check if already have position in this symbol
            for pos in positions:
                if pos['symbol'] == symbol:
                    logger.warning(f"Already have position in {symbol}")
                    return False

            # Check position count limits
            max_positions = (
                self.trading_config.position_limits.max_swing_positions
                if position_type == "SWING"
                else self.trading_config.position_limits.max_intraday_positions
            )

            if len(positions) >= max_positions:
                logger.warning(f"Position limit reached: {len(positions)}/{max_positions}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking position limits: {e}")
            return False

    def _calculate_trade_levels(
        self,
        current_price: float,
        signal: AggregatedSignal,
        action: TradeAction
    ) -> Dict[str, float]:
        """
        Calculate entry, stop loss, and target levels for a trade

        Uses volatility-based stops (ATR) when available, otherwise fixed percentage.
        Maintains consistent 1:3 risk:reward ratio for all trades.

        ATR (Average True Range): Measures market volatility
        - Higher ATR = More volatile stock = Wider stops needed
        - Lower ATR = Less volatile stock = Tighter stops acceptable
        """

        # Extract ATR value from indicator signals for volatility-based stop loss
        # ATR provides market-adaptive stop loss levels
        atr_value = None
        for ind_name, ind_signal in signal.indicator_signals.items():
            if 'ATR' in ind_name:
                atr_value = ind_signal.current_value
                break

        if action == TradeAction.BUY:
            # Long position: Buy at current price
            entry = current_price

            # Calculate stop loss below entry price
            # Preferred: 1.5x ATR (adapts to volatility)
            # Fallback: 2% fixed (if ATR unavailable)
            # Example: Entry=100, ATR=3 -> StopLoss = 100 - (3*1.5) = 95.5
            # Example: Entry=100, No ATR -> StopLoss = 100 * 0.98 = 98
            if atr_value:
                stop_loss = entry - (atr_value * 1.5)
            else:
                stop_loss = entry * 0.98  # 2% fixed stop

            # Calculate target using 3:1 reward:risk ratio
            # If risking 100, aim to make 300
            # Example: Entry=100, StopLoss=98, Risk=2, Target = 100 + (2*3) = 106
            risk = entry - stop_loss
            target = entry + (risk * 3.0)

        elif action == TradeAction.SHORT:
            # Short position: Sell at current price
            entry = current_price

            # Calculate stop loss above entry price (opposite of long)
            # Example: Entry=100, ATR=3 -> StopLoss = 100 + (3*1.5) = 104.5
            if atr_value:
                stop_loss = entry + (atr_value * 1.5)
            else:
                stop_loss = entry * 1.02  # 2% fixed stop

            # Calculate target using 3:1 reward:risk ratio
            # For shorts, target is below entry price
            # Example: Entry=100, StopLoss=102, Risk=2, Target = 100 - (2*3) = 94
            risk = stop_loss - entry
            target = entry - (risk * 3.0)

        else:  # SELL (close existing long position)
            # Exit trade at current market price
            # No stop loss or target needed for exits
            entry = current_price
            stop_loss = current_price
            target = current_price

        return {
            'entry': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2)
        }

    def _get_available_capital(self) -> float:
        """Get available capital for trading"""
        try:
            if not self.db.conn:
                self.db.connect()
            return self.db.get_available_cash()
        except Exception as e:
            logger.error(f"Error getting capital: {e}")
            return 50000.0  # Default

    def _calculate_position_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        position_type: str
    ) -> Dict[str, Any]:
        """
        Calculate position size based on risk management

        Uses fixed percentage risk per trade (default 1%)

        Algorithm:
        1. Calculate maximum risk amount (e.g., 1% of capital)
        2. Calculate risk per share (distance from entry to stop loss)
        3. Determine quantity: risk_amount / risk_per_share
        4. Apply position size limits (max % of capital per position)
        5. Apply capital availability constraint
        """
        # Step 1: Calculate maximum risk amount per trade
        # Example: With 50,000 capital and 1% risk = 500 max risk
        risk_per_trade = capital * (self.risk_config.loss_limits.risk_per_trade_percent / 100)

        # Step 2: Calculate risk per share
        # This is the amount you lose per share if stop loss is hit
        # Example: Entry=100, StopLoss=98, risk_per_share=2
        risk_per_share = abs(entry_price - stop_loss)

        # Edge case: If stop loss equals entry price, we cannot calculate position size
        if risk_per_share == 0:
            return {
                'quantity': 0,
                'position_value': 0,
                'risk_amount': 0,
                'risk_percent': 0
            }

        # Step 3: Calculate initial quantity based on risk
        # Example: risk_per_trade=500, risk_per_share=2, quantity=250 shares
        # This ensures that if stop loss is hit, you only lose your risk_per_trade amount
        quantity = int(risk_per_trade / risk_per_share)

        # Step 4: Calculate total position value
        # Example: 250 shares @ 100 = 25,000 position value
        position_value = quantity * entry_price

        # Step 5: Apply maximum position size constraint
        # Prevents over-concentration in single stock (default: 20% of capital max)
        # Example: With 50,000 capital and 20% max = 10,000 max position
        max_position_value = capital * (self.max_position_percent / 100)

        if position_value > max_position_value:
            # Reduce quantity to fit within maximum position size limit
            # Example: max_position=10,000, entry=100, quantity=100 shares
            quantity = int(max_position_value / entry_price)
            position_value = quantity * entry_price

        # Step 6: Ensure we have sufficient capital
        # This is a safety check in case calculations exceed available cash
        if position_value > capital:
            quantity = int(capital / entry_price)
            position_value = quantity * entry_price

        # Step 7: Recalculate actual risk based on final quantity
        # This may differ from risk_per_trade if position size limits were applied
        risk_amount = quantity * risk_per_share
        risk_percent = (risk_amount / capital) * 100 if capital > 0 else 0

        return {
            'quantity': quantity,
            'position_value': position_value,
            'risk_amount': risk_amount,
            'risk_percent': risk_percent
        }

    def _calculate_risk_reward(self, entry: float, stop_loss: float, target: float) -> float:
        """Calculate risk:reward ratio"""
        risk = abs(entry - stop_loss)
        reward = abs(target - entry)

        if risk == 0:
            return 0.0

        return reward / risk

    def _calculate_expected_return(self, entry: float, target: float) -> float:
        """Calculate expected return percentage"""
        if entry == 0:
            return 0.0
        return ((target - entry) / entry) * 100

    def _calculate_opportunity_score(
        self,
        signal_confidence: float,
        consensus_strength: float,
        risk_reward: float,
        bullish_score: float,
        bearish_score: float
    ) -> float:
        """
        Calculate overall opportunity score (0-100)

        This score combines multiple factors to rate the trade quality.
        Higher score means better opportunity.

        Weighting:
        - Signal confidence (40%): How confident are the indicators about direction
        - Consensus strength (20%): How well do indicators agree
        - Risk:reward ratio (20%): How favorable is the risk/reward profile
        - Signal strength (20%): How strong is the directional bias

        Example:
        - Perfect trade: 100 score (high confidence, consensus, great R:R)
        - Marginal trade: 50-60 score (meets minimum criteria)
        - Poor trade: <50 score (should not be taken)
        """
        # Normalize risk:reward ratio to 0-100 scale
        # We cap at 5:1 risk:reward as exceptional (100 score)
        # Example: 3:1 R:R = (3/5)*100 = 60 score
        # Example: 5:1 R:R = (5/5)*100 = 100 score
        rr_score = min(100, (risk_reward / 5.0) * 100)

        # Get dominant signal score (bullish or bearish)
        # This is the strength of the directional bias
        # Score ranges from 0.0 to 1.0, convert to 0-100
        signal_score = max(bullish_score, bearish_score) * 100

        # Weighted combination of all factors
        # This creates a composite score representing overall opportunity quality
        score = (
            signal_confidence * 0.40 +     # 40% weight: Most important factor
            consensus_strength * 0.20 +     # 20% weight: Indicator agreement
            rr_score * 0.20 +               # 20% weight: Risk management quality
            signal_score * 0.20             # 20% weight: Signal strength
        )

        # Ensure score stays within 0-100 range
        return min(100, max(0, score))

    def _add_warnings(self, recommendation: TradeRecommendation, signal: AggregatedSignal):
        """Add warnings to recommendation"""
        # Check for conflicting signals
        if signal.bullish_signals > 0 and signal.bearish_signals > 0:
            if abs(signal.bullish_signals - signal.bearish_signals) <= 1:
                recommendation.warnings.append("Mixed signals - low consensus")

        # Check for high risk
        if recommendation.risk_percent > 2.0:
            recommendation.warnings.append(f"High risk: {recommendation.risk_percent:.1f}% of capital")

        # Check for low confidence
        if recommendation.signal_confidence < 70:
            recommendation.warnings.append(f"Moderate confidence: {recommendation.signal_confidence:.0f}%")


# ========================================
# Convenience Functions
# ========================================

_global_engine: Optional[TradeDecisionEngine] = None


def get_trade_decision_engine() -> TradeDecisionEngine:
    """Get global trade decision engine instance"""
    global _global_engine

    if _global_engine is None:
        _global_engine = TradeDecisionEngine()

    return _global_engine


def evaluate_trade_opportunity(
    symbol: str,
    aggregated_signal: AggregatedSignal,
    current_price: float,
    timeframe: str = "1d",
    position_type: str = "SWING"
) -> TradeDecision:
    """
    Convenience function to evaluate trade opportunity

    Args:
        symbol: Stock symbol
        aggregated_signal: Aggregated signal
        current_price: Current market price
        timeframe: Timeframe
        position_type: SWING or INTRADAY

    Returns:
        TradeDecision
    """
    engine = get_trade_decision_engine()
    return engine.evaluate_signal(
        symbol, aggregated_signal, current_price, timeframe, position_type
    )
