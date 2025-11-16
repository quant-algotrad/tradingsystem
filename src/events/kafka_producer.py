"""
Kafka Event Producer
Publishes events to Kafka topics with low latency
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

from src.utils import get_logger

logger = get_logger(__name__)

# Conditional Kafka import
try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception


class KafkaEventProducer:
    """
    Kafka event producer with batching and compression

    Pattern: Singleton Pattern
    - Single producer instance per application
    - Thread-safe message publishing
    - Automatic batching for performance
    """

    _instance: Optional['KafkaEventProducer'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._producer = None
        self._enabled = False

        # Kafka configuration
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

        # Topics
        self.topics = {
            'market_data': 'trading.market_data',
            'signals': 'trading.signals',
            'trades': 'trading.trades',
            'risk': 'trading.risk',
            'system': 'trading.system'
        }

        self._initialize_producer()

    def _initialize_producer(self):
        """Initialize Kafka producer"""
        if not KAFKA_AVAILABLE:
            logger.warning("kafka-python not available. Install with: pip install kafka-python")
            return

        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                # Serialization
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,

                # Performance tuning for low latency
                acks='1',  # Leader acknowledgment only (faster)
                compression_type='lz4',  # Fast compression
                linger_ms=5,  # Small batching window (5ms)
                batch_size=16384,  # 16KB batches

                # Retry configuration
                retries=3,
                max_in_flight_requests_per_connection=5,

                # Timeout
                request_timeout_ms=10000,
                api_version=(2, 8, 0)
            )

            self._enabled = True
            logger.info(f"Kafka producer connected to {self.bootstrap_servers}")

        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self._enabled = False

    def is_enabled(self) -> bool:
        """Check if producer is enabled"""
        return self._enabled

    def send_event(
        self,
        topic_name: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send event to Kafka topic

        Args:
            topic_name: Topic name ('market_data', 'signals', 'trades', 'risk', 'system')
            event: Event data as dictionary
            key: Optional partition key (e.g., symbol)
            headers: Optional headers

        Returns:
            bool: True if sent successfully
        """
        if not self._enabled:
            logger.debug(f"Kafka disabled, skipping event to {topic_name}")
            return False

        try:
            # Get topic
            topic = self.topics.get(topic_name, topic_name)

            # Prepare headers
            kafka_headers = []
            if headers:
                kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]

            # Add timestamp header
            kafka_headers.append(('timestamp', datetime.now().isoformat().encode('utf-8')))

            # Send message
            future = self._producer.send(
                topic=topic,
                value=event,
                key=key,
                headers=kafka_headers
            )

            # Wait for send to complete (with timeout)
            record_metadata = future.get(timeout=2)

            logger.debug(
                f"Event sent to {topic} "
                f"(partition: {record_metadata.partition}, offset: {record_metadata.offset})"
            )

            return True

        except KafkaError as e:
            logger.error(f"Kafka error sending event to {topic_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending event to {topic_name}: {e}")
            return False

    def send_market_data_event(self, event: Dict[str, Any], symbol: str) -> bool:
        """Send market data event"""
        return self.send_event('market_data', event, key=symbol)

    def send_signal_event(self, event: Dict[str, Any], symbol: str) -> bool:
        """Send signal event"""
        return self.send_event('signals', event, key=symbol)

    def send_trade_event(self, event: Dict[str, Any], symbol: str) -> bool:
        """Send trade event"""
        return self.send_event('trades', event, key=symbol)

    def send_risk_event(self, event: Dict[str, Any]) -> bool:
        """Send risk event"""
        return self.send_event('risk', event)

    def send_system_event(self, event: Dict[str, Any]) -> bool:
        """Send system event"""
        return self.send_event('system', event)

    def flush(self, timeout: int = 5):
        """Flush all pending messages"""
        if self._enabled and self._producer:
            self._producer.flush(timeout=timeout)

    def close(self):
        """Close producer"""
        if self._enabled and self._producer:
            self._producer.flush()
            self._producer.close()
            logger.info("Kafka producer closed")


# ========================================
# Convenience Functions
# ========================================

_global_producer: Optional[KafkaEventProducer] = None


def get_event_producer() -> KafkaEventProducer:
    """Get global event producer instance"""
    global _global_producer

    if _global_producer is None:
        _global_producer = KafkaEventProducer()

    return _global_producer
