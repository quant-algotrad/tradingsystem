"""
Discord Notifier
Send notifications to Discord channel via webhook

Pattern: Observer Pattern
- Free and easy to set up
- Great for mobile notifications
- Supports rich embeds with colors
"""

import requests
from typing import Optional, Dict, Any
from datetime import datetime
import os

from src.notifications.base_notifier import INotifier, NotificationPriority
from src.events.event_types import BaseEvent, TradeEvent, SignalEvent, RiskEvent
from src.utils import get_logger

logger = get_logger(__name__)


class DiscordNotifier(INotifier):
    """
    Discord notification channel

    Sends notifications to Discord via webhooks
    Free and easy - just create a webhook in your Discord server

    Setup:
    1. Go to your Discord server settings
    2. Integrations > Webhooks > New Webhook
    3. Copy webhook URL
    4. Set DISCORD_WEBHOOK_URL environment variable
    """

    def __init__(
        self,
        enabled: bool = True,
        webhook_url: str = None,
        username: str = "Trading Bot",
        avatar_url: str = None
    ):
        """
        Initialize Discord notifier

        Args:
            enabled: Whether to enable Discord notifications
            webhook_url: Discord webhook URL
            username: Bot username to display
            avatar_url: Bot avatar URL (optional)
        """
        super().__init__(enabled)

        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL', '')
        self.username = username
        self.avatar_url = avatar_url

        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured. Set DISCORD_WEBHOOK_URL")
            self.enabled = False

    def get_name(self) -> str:
        return "Discord"

    def send(self, event: BaseEvent, priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """
        Send Discord notification

        Args:
            event: Event to notify
            priority: Priority level

        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.webhook_url:
            return False

        try:
            # Create Discord embed
            embed = self._create_embed(event, priority)

            # Create payload
            payload = {
                'username': self.username,
                'embeds': [embed]
            }

            if self.avatar_url:
                payload['avatar_url'] = self.avatar_url

            # Send to Discord
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 204:
                logger.debug(f"Discord notification sent: {event.event_type}")
                return True
            else:
                logger.error(f"Discord notification failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    def _create_embed(self, event: BaseEvent, priority: NotificationPriority) -> Dict[str, Any]:
        """
        Create Discord embed from event

        Args:
            event: Event to format
            priority: Priority level

        Returns:
            Discord embed dict
        """
        # Priority colors (Discord uses decimal color codes)
        priority_colors = {
            NotificationPriority.LOW: 0x17a2b8,      # Cyan
            NotificationPriority.MEDIUM: 0xffc107,   # Yellow
            NotificationPriority.HIGH: 0xff9800,     # Orange
            NotificationPriority.CRITICAL: 0xf44336  # Red
        }

        color = priority_colors.get(priority, 0x6c757d)

        # Event type specific embeds
        if isinstance(event, TradeEvent):
            return self._create_trade_embed(event, color)
        elif isinstance(event, SignalEvent):
            return self._create_signal_embed(event, color)
        elif isinstance(event, RiskEvent):
            return self._create_risk_embed(event, color)
        else:
            return self._create_generic_embed(event, color, priority)

    def _create_trade_embed(self, event: TradeEvent, color: int) -> Dict[str, Any]:
        """Create embed for trade event"""
        emoji = "🟢" if event.action == "BUY" else "🔴"

        fields = [
            {
                'name': 'Symbol',
                'value': event.symbol,
                'inline': True
            },
            {
                'name': 'Action',
                'value': f"{emoji} {event.action}",
                'inline': True
            },
            {
                'name': 'Quantity',
                'value': str(event.quantity),
                'inline': True
            },
            {
                'name': 'Price',
                'value': f"₹{event.price:.2f}",
                'inline': True
            },
            {
                'name': 'Stop Loss',
                'value': f"₹{event.stop_loss:.2f}" if event.stop_loss else 'N/A',
                'inline': True
            },
            {
                'name': 'Target',
                'value': f"₹{event.target_price:.2f}" if event.target_price else 'N/A',
                'inline': True
            },
            {
                'name': 'Strategy',
                'value': event.strategy,
                'inline': False
            }
        ]

        if event.pnl is not None:
            pnl_emoji = "📈" if event.pnl > 0 else "📉"
            fields.append({
                'name': 'P&L',
                'value': f"{pnl_emoji} ₹{event.pnl:.2f} ({event.pnl_percent:.2f}%)",
                'inline': False
            })

        return {
            'title': f"{emoji} Trade Executed: {event.action}",
            'description': f"**{event.symbol}** - {event.position_type}",
            'color': color,
            'fields': fields,
            'timestamp': event.timestamp,
            'footer': {
                'text': f'Trading System | {event.source_service}'
            }
        }

    def _create_signal_embed(self, event: SignalEvent, color: int) -> Dict[str, Any]:
        """Create embed for signal event"""
        emoji = "📈" if event.signal_type in ["BUY", "STRONG_BUY"] else "📉"

        fields = [
            {
                'name': 'Signal',
                'value': f"{emoji} {event.signal_type}",
                'inline': True
            },
            {
                'name': 'Confidence',
                'value': f"{event.confidence:.0f}%",
                'inline': True
            },
            {
                'name': 'Strength',
                'value': f"{event.strength:.0f}%",
                'inline': True
            },
            {
                'name': 'Timeframe',
                'value': event.timeframe or 'N/A',
                'inline': True
            },
            {
                'name': 'Strategy',
                'value': event.strategy_name or 'N/A',
                'inline': True
            }
        ]

        if event.reasons:
            fields.append({
                'name': 'Reasons',
                'value': '\n'.join(event.reasons[:3]),  # First 3 reasons
                'inline': False
            })

        return {
            'title': f"{emoji} Trading Signal",
            'description': f"**{event.symbol}**",
            'color': color,
            'fields': fields,
            'timestamp': event.timestamp,
            'footer': {
                'text': f'Trading System | {event.source_service}'
            }
        }

    def _create_risk_embed(self, event: RiskEvent, color: int) -> Dict[str, Any]:
        """Create embed for risk event"""
        emoji = "⚠️" if event.severity == "WARNING" else "🚨"

        fields = [
            {
                'name': 'Risk Type',
                'value': event.risk_type,
                'inline': True
            },
            {
                'name': 'Severity',
                'value': f"{emoji} {event.severity}",
                'inline': True
            },
            {
                'name': 'Metric',
                'value': event.metric_name,
                'inline': False
            },
            {
                'name': 'Current Value',
                'value': f"{event.current_value:.2f}",
                'inline': True
            },
            {
                'name': 'Limit',
                'value': f"{event.limit_value:.2f}",
                'inline': True
            },
            {
                'name': 'Utilization',
                'value': f"{event.utilization_percent:.0f}%",
                'inline': True
            }
        ]

        if event.message:
            fields.append({
                'name': 'Message',
                'value': event.message,
                'inline': False
            })

        return {
            'title': f"{emoji} Risk Alert",
            'description': event.risk_type,
            'color': 0xf44336,  # Always red for risk events
            'fields': fields,
            'timestamp': event.timestamp,
            'footer': {
                'text': f'Trading System | {event.source_service}'
            }
        }

    def _create_generic_embed(self, event: BaseEvent, color: int, priority: NotificationPriority) -> Dict[str, Any]:
        """Create generic embed for any event"""
        formatted_message = self.format_event_message(event)

        return {
            'title': event.event_type.replace('.', ' ').title(),
            'description': formatted_message,
            'color': color,
            'timestamp': event.timestamp,
            'fields': [
                {
                    'name': 'Priority',
                    'value': priority.value,
                    'inline': True
                },
                {
                    'name': 'Source',
                    'value': event.source_service,
                    'inline': True
                }
            ],
            'footer': {
                'text': 'Trading System'
            }
        }

    def send_custom_message(self, message: str, title: str = "Trading System", color: int = 0x0099ff):
        """
        Send custom message to Discord

        Args:
            message: Message text
            title: Message title
            color: Embed color (decimal)
        """
        if not self.enabled or not self.webhook_url:
            return False

        try:
            payload = {
                'username': self.username,
                'embeds': [{
                    'title': title,
                    'description': message,
                    'color': color,
                    'timestamp': datetime.now().isoformat()
                }]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 204

        except Exception as e:
            logger.error(f"Failed to send custom Discord message: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Discord webhook"""
        return self.send_custom_message(
            "✅ Discord webhook connected successfully!",
            "Test Message",
            0x00ff00
        )
