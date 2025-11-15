"""
Email Notifier
Send email notifications for important events

Pattern: Observer Pattern
- Disabled by default
- Useful for critical alerts when away from dashboard
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import os

from src.notifications.base_notifier import INotifier, NotificationPriority
from src.events.event_types import BaseEvent
from src.utils import get_logger

logger = get_logger(__name__)


class EmailNotifier(INotifier):
    """
    Email notification channel

    Sends email alerts for critical events
    Disabled by default - enable in config when needed
    """

    def __init__(
        self,
        enabled: bool = False,  # Disabled by default
        smtp_server: str = None,
        smtp_port: int = None,
        sender_email: str = None,
        sender_password: str = None,
        recipient_emails: List[str] = None,
        only_critical: bool = True
    ):
        """
        Initialize Email notifier

        Args:
            enabled: Whether to enable email notifications (default: False)
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (587 for TLS, 465 for SSL)
            sender_email: Sender email address
            sender_password: Sender email password/app password
            recipient_emails: List of recipient email addresses
            only_critical: Only send CRITICAL priority emails (default: True)
        """
        super().__init__(enabled)

        # SMTP configuration
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL', '')
        self.sender_password = sender_password or os.getenv('SENDER_PASSWORD', '')
        self.recipient_emails = recipient_emails or os.getenv('RECIPIENT_EMAILS', '').split(',')
        self.only_critical = only_critical

        # Validate configuration
        if not self.sender_email or not self.recipient_emails:
            logger.warning("Email notifier not fully configured. Set SENDER_EMAIL and RECIPIENT_EMAILS")
            self.enabled = False

    def get_name(self) -> str:
        return "Email"

    def send(self, event: BaseEvent, priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """
        Send email notification

        Args:
            event: Event to notify
            priority: Priority level

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        # Only send critical emails if configured
        if self.only_critical and priority != NotificationPriority.CRITICAL:
            return True

        # Check credentials
        if not self.sender_email or not self.sender_password:
            logger.error("Email credentials not configured")
            return False

        try:
            # Create message
            subject = self._create_subject(event, priority)
            body = self._create_body(event, priority)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)

            # Add plain text and HTML versions
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(self._create_html_body(event, priority), 'html')

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f"Email sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _create_subject(self, event: BaseEvent, priority: NotificationPriority) -> str:
        """Create email subject line"""
        priority_emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "📊",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.CRITICAL: "🚨"
        }

        emoji = priority_emoji.get(priority, "📧")
        event_type = event.event_type.replace('.', ' ').title()

        return f"{emoji} Trading System Alert: {event_type}"

    def _create_body(self, event: BaseEvent, priority: NotificationPriority) -> str:
        """Create plain text email body"""
        formatted_message = self.format_event_message(event)

        return f"""
Trading System Notification

Priority: {priority.value}
Timestamp: {event.timestamp}
Event Type: {event.event_type}
Source: {event.source_service}

--- Event Details ---
{formatted_message}

--- Raw Data ---
{event.to_dict()}

---
This is an automated message from your Trading System.
To disable email notifications, set EMAIL_NOTIFIER_ENABLED=false in your config.
"""

    def _create_html_body(self, event: BaseEvent, priority: NotificationPriority) -> str:
        """Create HTML email body"""
        priority_colors = {
            NotificationPriority.LOW: "#17a2b8",
            NotificationPriority.MEDIUM: "#ffc107",
            NotificationPriority.HIGH: "#ff9800",
            NotificationPriority.CRITICAL: "#f44336"
        }

        color = priority_colors.get(priority, "#6c757d")
        formatted_message = self.format_event_message(event).replace('\n', '<br>')

        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; }}
        .footer {{ background: #e9ecef; padding: 10px; font-size: 12px; color: #6c757d; text-align: center; border-radius: 0 0 5px 5px; }}
        .event-details {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid {color}; }}
        .badge {{ display: inline-block; padding: 5px 10px; border-radius: 3px; background: {color}; color: white; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Trading System Alert</h2>
            <p><span class="badge">{priority.value}</span></p>
        </div>
        <div class="content">
            <p><strong>Event Type:</strong> {event.event_type}</p>
            <p><strong>Timestamp:</strong> {event.timestamp}</p>
            <p><strong>Source:</strong> {event.source_service}</p>

            <div class="event-details">
                <h3>Event Details</h3>
                <p>{formatted_message}</p>
            </div>
        </div>
        <div class="footer">
            This is an automated message from your Trading System.<br>
            To disable email notifications, update your configuration.
        </div>
    </div>
</body>
</html>
"""

    def test_connection(self) -> bool:
        """
        Test SMTP connection and credentials

        Returns:
            True if connection successful
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            logger.info("Email SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"Email SMTP connection test failed: {e}")
            return False
