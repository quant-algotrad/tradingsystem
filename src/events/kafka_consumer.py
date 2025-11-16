"""
Kafka Event Consumer
Subscribes to Kafka topics and processes events
"""

import os
import json
from typing import Callable, List, Optional, Dict, Any
from datetime import datetime

from src.utils import get_logger

logger = get_logger(__name__)

# Conditional Kafka import
try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaConsumer = None
    KafkaError = Exception


class KafkaEventConsumer:
    """
    Kafka event consumer with automatic offset management

    Pattern: Observer Pattern
    - Subscribes to topics and notifies handlers
    - Automatic offset commit
    - Error handling and retry
    """

    def __init__(
        self,
        consumer_group: str,
        topics: List[str],
        handler: Callable[[Dict[str, Any]], None],
        bootstrap_servers: Optional[str] = None
    ):
        """
        Initialize Kafka consumer

        Args:
            consumer_group: Consumer group ID
            topics: List of topics to subscribe
            handler: Callback function to handle messages
            bootstrap_servers: Kafka servers (default from env)
        """
        self.consumer_group = consumer_group
        self.topics = topics
        self.handler = handler
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            'KAFKA_BOOTSTRAP_SERVERS',
            'localhost:9092'
        )

        self._consumer = None
        self._enabled = False
        self._running = False

        self._initialize_consumer()

    def _initialize_consumer(self):
        """Initialize Kafka consumer"""
        if not KAFKA_AVAILABLE:
            logger.warning("kafka-python not available")
            return

        try:
            self._consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,

                # Deserialization
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,

                # Offset management
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                auto_offset_reset='latest',  # Start from latest for real-time

                # Performance
                fetch_min_bytes=1,
                fetch_max_wait_ms=500,
                max_poll_records=100,

                # Timeout
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000,
                request_timeout_ms=40000,

                api_version=(2, 8, 0)
            )

            self._enabled = True
            logger.info(f"Kafka consumer '{self.consumer_group}' subscribed to {self.topics}")

        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if consumer is enabled"""
        return self._enabled

    def start(self):
        """Start consuming messages"""
        if not self._enabled:
            logger.warning("Kafka consumer not enabled")
            return

        self._running = True
        logger.info(f"Starting consumer '{self.consumer_group}'...")

        try:
            for message in self._consumer:
                if not self._running:
                    break

                try:
                    # Log received message
                    logger.debug(
                        f"Received: topic={message.topic}, "
                        f"partition={message.partition}, offset={message.offset}"
                    )

                    # Extract event data
                    event = message.value

                    # Add metadata
                    event['_kafka_metadata'] = {
                        'topic': message.topic,
                        'partition': message.partition,
                        'offset': message.offset,
                        'timestamp': message.timestamp,
                        'key': message.key
                    }

                    # Call handler
                    self.handler(event)

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing next message

        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop consumer"""
        self._running = False
        if self._consumer:
            self._consumer.close()
            logger.info(f"Consumer '{self.consumer_group}' stopped")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# ========================================
# Convenience Functions
# ========================================

def create_consumer(
    consumer_group: str,
    topics: List[str],
    handler: Callable[[Dict[str, Any]], None]
) -> KafkaEventConsumer:
    """
    Create and return Kafka consumer

    Args:
        consumer_group: Consumer group ID
        topics: List of topics
        handler: Message handler function

    Returns:
        KafkaEventConsumer instance
    """
    return KafkaEventConsumer(consumer_group, topics, handler)


# ========================================
# Topic Helper Functions
# ========================================

TOPIC_MAP = {
    'market_data': 'trading.market_data',
    'signals': 'trading.signals',
    'trades': 'trading.trades',
    'risk': 'trading.risk',
    'system': 'trading.system'
}


def get_topic_name(short_name: str) -> str:
    """Get full topic name from short name"""
    return TOPIC_MAP.get(short_name, short_name)
