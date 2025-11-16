"""
Notification Manager
Centralized notification system using Observer Pattern

Pattern: Observer Pattern + Mediator Pattern
- Subject: NotificationManager
- Observers: Various notifiers (WebSocket, Email, Discord, etc.)
- Publishes events to all registered observers
"""

from typing import List, Dict, Any
from src.notifications.base_notifier import INotifier, NotificationPriority
from src.notifications.websocket_notifier import WebSocketNotifier
from src.notifications.email_notifier import EmailNotifier
from src.notifications.discord_notifier import DiscordNotifier
from src.events.event_types import BaseEvent, TradeEvent, RiskEvent, SignalEvent
from src.utils import get_logger

logger = get_logger(__name__)


class NotificationManager:
    """
    Central notification manager

    Pattern: Observer Pattern
    - Manages all notification channels (observers)
    - Routes events to appropriate channels
    - Handles priority-based filtering

    Pattern: Mediator Pattern
    - Decouples event sources from notification channels
    - Central point for notification logic

    Usage:
        manager = NotificationManager()
        manager.notify(trade_event, priority=NotificationPriority.HIGH)
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        """Singleton pattern - only one notification manager"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize notification manager"""
        if hasattr(self, '_initialized'):
            return

        self._notifiers: List[INotifier] = []
        self._priority_routing: Dict[str, List[NotificationPriority]] = {}

        # Initialize default notifiers
        self._init_default_notifiers()

        self._initialized = True
        logger.info("Notification Manager initialized")

    def _init_default_notifiers(self):
        """Initialize default notification channels"""
        # WebSocket - always enabled for dashboard
        websocket = WebSocketNotifier(enabled=True)
        self.register(websocket)

        # Email - disabled by default
        email = EmailNotifier(enabled=False, only_critical=True)
        self.register(email)

        # Discord - enabled if webhook configured
        discord = DiscordNotifier(enabled=True)
        self.register(discord)

        logger.info(f"Initialized {len(self._notifiers)} notification channels")

    def register(self, notifier: INotifier):
        """
        Register a new notification channel

        Args:
            notifier: Notifier instance to register
        """
        if notifier not in self._notifiers:
            self._notifiers.append(notifier)
            logger.info(f"Registered notifier: {notifier.get_name()}")

    def unregister(self, notifier: INotifier):
        """
        Unregister a notification channel

        Args:
            notifier: Notifier instance to remove
        """
        if notifier in self._notifiers:
            self._notifiers.remove(notifier)
            logger.info(f"Unregistered notifier: {notifier.get_name()}")

    def notify(
        self,
        event: BaseEvent,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channels: List[str] = None
    ):
        """
        Send notification to all registered channels

        Args:
            event: Event to notify
            priority: Notification priority
            channels: Specific channels to notify (None = all enabled)
        """
        # Auto-determine priority if not specified
        if priority == NotificationPriority.MEDIUM:
            priority = self._auto_determine_priority(event)

        logger.debug(
            f"Notifying: {event.event_type} | Priority: {priority.value} | "
            f"Channels: {channels or 'all'}"
        )

        # Send to each notifier
        for notifier in self._notifiers:
            # Skip if specific channels requested and this isn't one
            if channels and notifier.get_name() not in channels:
                continue

            # Skip if disabled
            if not notifier.is_enabled():
                continue

            # Check priority routing
            if not self._should_notify(notifier, priority):
                continue

            # Send notification
            try:
                notifier.notify(event, priority)
            except Exception as e:
                logger.error(f"Notifier {notifier.get_name()} failed: {e}")

    def notify_trade(self, trade_event: TradeEvent, priority: NotificationPriority = None):
        """
        Convenience method to notify trade events

        Args:
            trade_event: Trade event
            priority: Priority (auto-determined if None)
        """
        if priority is None:
            # Determine priority based on trade
            if trade_event.status == "FILLED":
                priority = NotificationPriority.HIGH
            elif trade_event.status == "REJECTED":
                priority = NotificationPriority.MEDIUM
            else:
                priority = NotificationPriority.LOW

        self.notify(trade_event, priority)

    def notify_signal(self, signal_event: SignalEvent, priority: NotificationPriority = None):
        """
        Convenience method to notify signal events

        Args:
            signal_event: Signal event
            priority: Priority (auto-determined if None)
        """
        if priority is None:
            # High confidence signals get higher priority
            if signal_event.confidence >= 80:
                priority = NotificationPriority.HIGH
            elif signal_event.confidence >= 60:
                priority = NotificationPriority.MEDIUM
            else:
                priority = NotificationPriority.LOW

        self.notify(signal_event, priority)

    def notify_risk(self, risk_event: RiskEvent, priority: NotificationPriority = None):
        """
        Convenience method to notify risk events

        Args:
            risk_event: Risk event
            priority: Priority (auto-determined if None)
        """
        if priority is None:
            # Risk events are always important
            if risk_event.severity == "CRITICAL":
                priority = NotificationPriority.CRITICAL
            elif risk_event.severity == "WARNING":
                priority = NotificationPriority.HIGH
            else:
                priority = NotificationPriority.MEDIUM

        self.notify(risk_event, priority)

    def _auto_determine_priority(self, event: BaseEvent) -> NotificationPriority:
        """
        Auto-determine priority based on event type

        Args:
            event: Event to analyze

        Returns:
            Suggested priority level
        """
        if isinstance(event, RiskEvent):
            return NotificationPriority.CRITICAL
        elif isinstance(event, TradeEvent):
            return NotificationPriority.HIGH
        elif isinstance(event, SignalEvent):
            return NotificationPriority.MEDIUM
        else:
            return NotificationPriority.LOW

    def _should_notify(self, notifier: INotifier, priority: NotificationPriority) -> bool:
        """
        Check if notifier should receive this priority

        Args:
            notifier: Notifier to check
            priority: Priority level

        Returns:
            True if should notify
        """
        notifier_name = notifier.get_name()

        # Check custom routing
        if notifier_name in self._priority_routing:
            allowed_priorities = self._priority_routing[notifier_name]
            return priority in allowed_priorities

        # Default: all notifiers get all priorities
        return True

    def set_priority_routing(self, notifier_name: str, priorities: List[NotificationPriority]):
        """
        Configure which priorities a notifier should receive

        Args:
            notifier_name: Notifier channel name
            priorities: List of allowed priorities

        Example:
            # Email only gets CRITICAL
            manager.set_priority_routing('Email', [NotificationPriority.CRITICAL])
        """
        self._priority_routing[notifier_name] = priorities
        logger.info(f"Priority routing set for {notifier_name}: {[p.value for p in priorities]}")

    def enable_channel(self, channel_name: str):
        """
        Enable a notification channel

        Args:
            channel_name: Name of channel to enable
        """
        for notifier in self._notifiers:
            if notifier.get_name() == channel_name:
                notifier.enable()
                logger.info(f"Enabled channel: {channel_name}")
                return

        logger.warning(f"Channel not found: {channel_name}")

    def disable_channel(self, channel_name: str):
        """
        Disable a notification channel

        Args:
            channel_name: Name of channel to disable
        """
        for notifier in self._notifiers:
            if notifier.get_name() == channel_name:
                notifier.disable()
                logger.info(f"Disabled channel: {channel_name}")
                return

        logger.warning(f"Channel not found: {channel_name}")

    def get_notifier(self, name: str) -> INotifier:
        """
        Get notifier by name

        Args:
            name: Notifier name

        Returns:
            Notifier instance or None
        """
        for notifier in self._notifiers:
            if notifier.get_name() == name:
                return notifier
        return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all notification channels

        Returns:
            Status dict with channel info
        """
        return {
            'total_channels': len(self._notifiers),
            'channels': [
                {
                    'name': n.get_name(),
                    'enabled': n.is_enabled(),
                    'filters': n._filters if hasattr(n, '_filters') else []
                }
                for n in self._notifiers
            ],
            'priority_routing': {
                name: [p.value for p in priorities]
                for name, priorities in self._priority_routing.items()
            }
        }

    def test_all_channels(self):
        """Test all notification channels"""
        from src.events.event_types import create_signal_event

        logger.info("Testing all notification channels...")

        test_event = create_signal_event(
            symbol="TEST",
            signal_type="BUY",
            confidence=75.0,
            strength=80.0,
            source_service="notification_test"
        )

        for notifier in self._notifiers:
            if notifier.is_enabled():
                try:
                    logger.info(f"Testing {notifier.get_name()}...")
                    notifier.notify(test_event, NotificationPriority.LOW)
                    logger.info(f"✅ {notifier.get_name()} test passed")
                except Exception as e:
                    logger.error(f"❌ {notifier.get_name()} test failed: {e}")


# ========================================
# Global Instance
# ========================================

_notification_manager: NotificationManager = None


def get_notification_manager() -> NotificationManager:
    """Get global notification manager instance"""
    global _notification_manager

    if _notification_manager is None:
        _notification_manager = NotificationManager()

    return _notification_manager


# ========================================
# Convenience Functions
# ========================================

def notify(event: BaseEvent, priority: NotificationPriority = NotificationPriority.MEDIUM):
    """
    Convenience function to send notification

    Args:
        event: Event to notify
        priority: Priority level
    """
    manager = get_notification_manager()
    manager.notify(event, priority)


def notify_trade(trade_event: TradeEvent):
    """Notify trade event with auto priority"""
    manager = get_notification_manager()
    manager.notify_trade(trade_event)


def notify_signal(signal_event: SignalEvent):
    """Notify signal event with auto priority"""
    manager = get_notification_manager()
    manager.notify_signal(signal_event)


def notify_risk(risk_event: RiskEvent):
    """Notify risk event with auto priority"""
    manager = get_notification_manager()
    manager.notify_risk(risk_event)
