"""
Notification System
Observer Pattern implementation for multi-channel notifications

Components:
- Base Notifier: Observer interface
- WebSocket: Real-time dashboard updates
- Email: Critical alerts (disabled by default)
- Discord: Mobile-friendly notifications
- Notification Manager: Subject that manages all observers

Pattern: Observer Pattern
- Loose coupling between event sources and notification channels
- Easy to add new notification channels
- Priority-based routing

Usage:
    from src.notifications import notify_trade, get_notification_manager

    # Simple notification
    notify_trade(trade_event)

    # Advanced control
    manager = get_notification_manager()
    manager.notify(event, priority=NotificationPriority.HIGH)

    # Configure channels
    manager.disable_channel('Email')
    manager.enable_channel('Discord')
"""

from .base_notifier import INotifier, NotificationPriority
from .websocket_notifier import WebSocketNotifier
from .email_notifier import EmailNotifier
from .discord_notifier import DiscordNotifier
from .notification_manager import (
    NotificationManager,
    get_notification_manager,
    notify,
    notify_trade,
    notify_signal,
    notify_risk
)

__all__ = [
    # Base
    'INotifier',
    'NotificationPriority',

    # Notifiers
    'WebSocketNotifier',
    'EmailNotifier',
    'DiscordNotifier',

    # Manager
    'NotificationManager',
    'get_notification_manager',

    # Convenience functions
    'notify',
    'notify_trade',
    'notify_signal',
    'notify_risk',
]

__version__ = '1.0.0'
