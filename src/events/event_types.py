"""
Event Type Definitions
Defines all events in the trading system
"""

from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional
import json


class EventType(Enum):
    """Event types in the system"""
    # Market data events
    MARKET_DATA_TICK = "market_data.tick"
    MARKET_DATA_BAR = "market_data.bar"
    MARKET_DATA_QUOTE = "market_data.quote"

    # Signal events
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_AGGREGATED = "signal.aggregated"
    SIGNAL_MULTI_TIMEFRAME = "signal.multi_timeframe"

    # Trade events
    TRADE_DECISION = "trade.decision"
    TRADE_ORDER_CREATED = "trade.order_created"
    TRADE_ORDER_FILLED = "trade.order_filled"
    TRADE_ORDER_CANCELLED = "trade.order_cancelled"
    TRADE_POSITION_OPENED = "trade.position_opened"
    TRADE_POSITION_CLOSED = "trade.position_closed"

    # Risk events
    RISK_LIMIT_APPROACH = "risk.limit_approach"
    RISK_LIMIT_BREACH = "risk.limit_breach"
    RISK_CIRCUIT_BREAKER = "risk.circuit_breaker"
    RISK_POSITION_UPDATE = "risk.position_update"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEARTBEAT = "system.heartbeat"


@dataclass
class BaseEvent:
    """Base class for all events"""
    event_type: str
    timestamp: str  # ISO format
    source_service: str
    event_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str):
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class MarketDataEvent(BaseEvent):
    """Market data event (OHLCV, quotes, ticks)"""
    symbol: str
    data_type: str  # 'bar', 'quote', 'tick'
    timeframe: Optional[str] = None

    # OHLCV data (for bars)
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None

    # Quote data
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    last_price: Optional[float] = None


@dataclass
class SignalEvent(BaseEvent):
    """Trading signal event"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'NEUTRAL'
    confidence: float  # 0-100
    strength: float  # 0-100

    # Signal source
    indicator_name: Optional[str] = None
    strategy_name: Optional[str] = None
    timeframe: Optional[str] = None

    # Supporting data
    bullish_signals: int = 0
    bearish_signals: int = 0
    neutral_signals: int = 0

    # Metadata
    reasons: Optional[list] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class TradeEvent(BaseEvent):
    """Trade execution event"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'SHORT', 'COVER'

    # Order details
    order_id: Optional[str] = None
    quantity: int = 0
    price: float = 0.0
    order_type: str = "MARKET"  # 'MARKET', 'LIMIT', 'STOP'

    # Position details
    position_type: str = "SWING"  # 'SWING', 'INTRADAY'
    strategy: str = "MULTI_INDICATOR"

    # Risk management
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    risk_amount: Optional[float] = None

    # Execution status
    status: str = "PENDING"  # 'PENDING', 'FILLED', 'CANCELLED', 'REJECTED'
    filled_quantity: int = 0
    filled_price: Optional[float] = None

    # P&L (for position close)
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None

    # Metadata
    decision_score: Optional[float] = None
    execution_time: Optional[str] = None


@dataclass
class RiskEvent(BaseEvent):
    """Risk management event"""
    risk_type: str  # 'LIMIT_APPROACH', 'LIMIT_BREACH', 'CIRCUIT_BREAKER'
    severity: str  # 'INFO', 'WARNING', 'CRITICAL'

    # Risk metrics
    metric_name: str  # 'daily_loss', 'position_count', 'drawdown'
    current_value: float
    limit_value: float
    utilization_percent: float

    # Context
    symbol: Optional[str] = None
    position_type: Optional[str] = None

    # Action taken
    action_taken: Optional[str] = None  # 'HALT_TRADING', 'CLOSE_POSITIONS', 'REDUCE_SIZE'
    message: str = ""


@dataclass
class SystemEvent(BaseEvent):
    """System lifecycle and health events"""
    service_name: str
    event_subtype: str  # 'STARTUP', 'SHUTDOWN', 'ERROR', 'HEARTBEAT'

    # Health metrics
    status: str = "OK"  # 'OK', 'DEGRADED', 'ERROR'

    # Metadata
    message: Optional[str] = None
    error_details: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


# ========================================
# Event Factory Functions
# ========================================

def create_market_data_event(
    symbol: str,
    data_type: str,
    source_service: str,
    **kwargs
) -> MarketDataEvent:
    """Create market data event"""
    import uuid

    event_type_map = {
        'bar': EventType.MARKET_DATA_BAR,
        'quote': EventType.MARKET_DATA_QUOTE,
        'tick': EventType.MARKET_DATA_TICK
    }

    return MarketDataEvent(
        event_type=event_type_map[data_type].value,
        timestamp=datetime.now().isoformat(),
        source_service=source_service,
        event_id=str(uuid.uuid4()),
        symbol=symbol,
        data_type=data_type,
        **kwargs
    )


def create_signal_event(
    symbol: str,
    signal_type: str,
    confidence: float,
    strength: float,
    source_service: str,
    **kwargs
) -> SignalEvent:
    """Create signal event"""
    import uuid

    return SignalEvent(
        event_type=EventType.SIGNAL_AGGREGATED.value,
        timestamp=datetime.now().isoformat(),
        source_service=source_service,
        event_id=str(uuid.uuid4()),
        symbol=symbol,
        signal_type=signal_type,
        confidence=confidence,
        strength=strength,
        **kwargs
    )


def create_trade_event(
    symbol: str,
    action: str,
    source_service: str,
    **kwargs
) -> TradeEvent:
    """Create trade event"""
    import uuid

    return TradeEvent(
        event_type=EventType.TRADE_DECISION.value,
        timestamp=datetime.now().isoformat(),
        source_service=source_service,
        event_id=str(uuid.uuid4()),
        symbol=symbol,
        action=action,
        **kwargs
    )


def create_risk_event(
    risk_type: str,
    severity: str,
    metric_name: str,
    current_value: float,
    limit_value: float,
    source_service: str,
    **kwargs
) -> RiskEvent:
    """Create risk event"""
    import uuid

    utilization = (current_value / limit_value * 100) if limit_value > 0 else 0

    return RiskEvent(
        event_type=EventType.RISK_LIMIT_APPROACH.value,
        timestamp=datetime.now().isoformat(),
        source_service=source_service,
        event_id=str(uuid.uuid4()),
        risk_type=risk_type,
        severity=severity,
        metric_name=metric_name,
        current_value=current_value,
        limit_value=limit_value,
        utilization_percent=utilization,
        **kwargs
    )
