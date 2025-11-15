"""
WebSocket Notifier
Real-time notifications to dashboard via WebSocket

Pattern: Observer Pattern
- Sends events to connected WebSocket clients
- Used for real-time dashboard updates
"""

from typing import Set, Dict, Any
import json
from datetime import datetime

from src.notifications.base_notifier import INotifier, NotificationPriority
from src.events.event_types import BaseEvent
from src.utils import get_logger

logger = get_logger(__name__)


class WebSocketNotifier(INotifier):
    """
    WebSocket notification channel

    Sends real-time updates to connected dashboard clients
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize WebSocket notifier

        Args:
            enabled: Whether to enable WebSocket notifications
        """
        super().__init__(enabled)
        self._clients: Set[Any] = set()  # Connected WebSocket clients
        self._message_queue = []  # Queue for offline messages
        self.max_queue_size = 100

    def get_name(self) -> str:
        return "WebSocket"

    def register_client(self, client):
        """
        Register a new WebSocket client

        Args:
            client: WebSocket client connection
        """
        self._clients.add(client)
        logger.info(f"WebSocket client connected. Total clients: {len(self._clients)}")

        # Send queued messages to new client
        self._send_queued_messages(client)

    def unregister_client(self, client):
        """
        Unregister a WebSocket client

        Args:
            client: WebSocket client connection
        """
        if client in self._clients:
            self._clients.remove(client)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self._clients)}")

    def send(self, event: BaseEvent, priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """
        Send event to all connected WebSocket clients

        Args:
            event: Event to send
            priority: Priority level

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        message = self._create_message(event, priority)

        # If no clients connected, queue the message
        if not self._clients:
            self._queue_message(message)
            return True

        # Send to all connected clients
        success = True
        disconnected_clients = []

        for client in self._clients:
            try:
                # Actual WebSocket send would happen here
                # For now, we just simulate it
                logger.debug(f"Sending to WebSocket client: {message['event_type']}")
                # In production: await client.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to WebSocket client: {e}")
                disconnected_clients.append(client)
                success = False

        # Remove disconnected clients
        for client in disconnected_clients:
            self.unregister_client(client)

        return success

    def _create_message(self, event: BaseEvent, priority: NotificationPriority) -> Dict[str, Any]:
        """
        Create WebSocket message from event

        Args:
            event: Event to convert
            priority: Priority level

        Returns:
            Message dict ready for JSON serialization
        """
        return {
            'event_type': event.event_type,
            'priority': priority.value,
            'timestamp': event.timestamp,
            'source': event.source_service,
            'data': event.to_dict(),
            'formatted_message': self.format_event_message(event)
        }

    def _queue_message(self, message: Dict[str, Any]):
        """
        Queue message for later delivery

        Args:
            message: Message to queue
        """
        self._message_queue.append(message)

        # Limit queue size
        if len(self._message_queue) > self.max_queue_size:
            self._message_queue.pop(0)

    def _send_queued_messages(self, client):
        """
        Send queued messages to newly connected client

        Args:
            client: WebSocket client
        """
        for message in self._message_queue:
            try:
                # In production: await client.send_json(message)
                logger.debug(f"Sending queued message to new client: {message['event_type']}")
            except Exception as e:
                logger.error(f"Failed to send queued message: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket notifier statistics"""
        return {
            'connected_clients': len(self._clients),
            'queued_messages': len(self._message_queue),
            'enabled': self.enabled
        }

    def broadcast_custom(self, message: Dict[str, Any]):
        """
        Broadcast custom message to all clients

        Args:
            message: Custom message dict
        """
        for client in self._clients:
            try:
                # In production: await client.send_json(message)
                logger.debug(f"Broadcasting custom message")
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
