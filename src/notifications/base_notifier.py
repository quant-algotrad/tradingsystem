"""
Base Notifier Interface
Defines the Observer interface for notification system

Pattern: Observer Pattern
- Subjects publish events
- Observers (notifiers) receive and handle events
- Loose coupling between event sources and notification channels
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum

from src.events.event_types import (
    BaseEvent,
    MarketDataEvent,
    SignalEvent,
    TradeEvent,
    RiskEvent,
    SystemEvent
)


class NotificationPriority(Enum):
    """Priority levels for notifications"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class INotifier(ABC):
    """
    Abstract base class for all notification channels

    Pattern: Observer Pattern
    - Each notifier is an observer
    - Receives events and sends notifications
    - Can filter events based on type/priority
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize notifier

        Args:
            enabled: Whether this notifier is active
        """
        self.enabled = enabled
        self._filters = []  # Event type filters

    @abstractmethod
    def get_name(self) -> str:
        """Return notifier channel name"""
        pass

    @abstractmethod
    def send(self, event: BaseEvent, priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """
        Send notification for an event

        Args:
            event: Event to notify about
            priority: Notification priority

        Returns:
            True if sent successfully, False otherwise
        """
        pass

    def notify(self, event: BaseEvent, priority: NotificationPriority = NotificationPriority.MEDIUM):
        """
        Main notification entry point

        Args:
            event: Event to notify
            priority: Priority level
        """
        if not self.enabled:
            return

        # Apply filters
        if self._filters and type(event).__name__ not in self._filters:
            return

        try:
            self.send(event, priority)
        except Exception as e:
            print(f"[ERROR] {self.get_name()} notification failed: {e}")

    def enable(self):
        """Enable this notifier"""
        self.enabled = True

    def disable(self):
        """Disable this notifier"""
        self.enabled = False

    def is_enabled(self) -> bool:
        """Check if notifier is enabled"""
        return self.enabled

    def add_filter(self, event_type: str):
        """
        Add event type filter

        Args:
            event_type: Event class name to filter (e.g., 'TradeEvent')
        """
        if event_type not in self._filters:
            self._filters.append(event_type)

    def clear_filters(self):
        """Remove all filters (receive all events)"""
        self._filters = []

    def format_event_message(self, event: BaseEvent) -> str:
        """
        Format event into human-readable message

        Args:
            event: Event to format

        Returns:
            Formatted message string
        """
        if isinstance(event, TradeEvent):
            return self._format_trade_event(event)
        elif isinstance(event, SignalEvent):
            return self._format_signal_event(event)
        elif isinstance(event, RiskEvent):
            return self._format_risk_event(event)
        elif isinstance(event, SystemEvent):
            return self._format_system_event(event)
        elif isinstance(event, MarketDataEvent):
            return self._format_market_event(event)
        else:
            return f"{event.event_type}: {event.to_dict()}"

    def _format_trade_event(self, event: TradeEvent) -> str:
        """Format trade event"""
        emoji = "🟢" if event.action == "BUY" else "🔴"
        return (
            f"{emoji} **TRADE**: {event.action} {event.quantity} {event.symbol}\n"
            f"Price: ₹{event.price:.2f} | Strategy: {event.strategy}\n"
            f"SL: ₹{event.stop_loss:.2f} | Target: ₹{event.target_price:.2f}"
        )

    def _format_signal_event(self, event: SignalEvent) -> str:
        """Format signal event"""
        emoji = "📈" if event.signal_type in ["BUY", "STRONG_BUY"] else "📉"
        return (
            f"{emoji} **SIGNAL**: {event.signal_type} {event.symbol}\n"
            f"Confidence: {event.confidence:.0f}% | Strength: {event.strength:.0f}%\n"
            f"Strategy: {event.strategy_name or 'N/A'} | TF: {event.timeframe or 'N/A'}"
        )

    def _format_risk_event(self, event: RiskEvent) -> str:
        """Format risk event"""
        emoji = "⚠️" if event.severity == "WARNING" else "🚨"
        return (
            f"{emoji} **RISK ALERT**: {event.risk_type}\n"
            f"Metric: {event.metric_name}\n"
            f"Current: {event.current_value:.2f} / Limit: {event.limit_value:.2f}\n"
            f"Utilization: {event.utilization_percent:.0f}%"
        )

    def _format_system_event(self, event: SystemEvent) -> str:
        """Format system event"""
        emoji = "✅" if event.status == "OK" else "❌"
        return (
            f"{emoji} **SYSTEM**: {event.service_name}\n"
            f"Event: {event.event_subtype} | Status: {event.status}\n"
            f"Message: {event.message or 'N/A'}"
        )

    def _format_market_event(self, event: MarketDataEvent) -> str:
        """Format market data event"""
        if event.data_type == 'quote':
            return (
                f"💹 **QUOTE**: {event.symbol}\n"
                f"Bid: ₹{event.bid:.2f} x {event.bid_size} | "
                f"Ask: ₹{event.ask:.2f} x {event.ask_size}"
            )
        elif event.data_type == 'bar':
            return (
                f"📊 **BAR**: {event.symbol} ({event.timeframe})\n"
                f"O: ₹{event.open:.2f} H: ₹{event.high:.2f} "
                f"L: ₹{event.low:.2f} C: ₹{event.close:.2f}\n"
                f"Volume: {event.volume:,}"
            )
        else:
            return f"📈 **MARKET DATA**: {event.symbol} - {event.data_type}"
