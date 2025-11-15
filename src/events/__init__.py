"""
Event-Driven Architecture Module
Kafka-based event streaming for trading system

Events Flow:
1. Market Data Events → Ingestion Service → Kafka
2. Signal Events → Signal Processor → Kafka
3. Trade Events → Trade Executor → Kafka
4. Risk Events → Risk Monitor → Kafka

Patterns:
- Event Sourcing: All state changes are events
- CQRS: Separate read/write models
- Publisher-Subscriber: Decoupled services
"""

from .event_types import (
    EventType,
    MarketDataEvent,
    SignalEvent,
    TradeEvent,
    RiskEvent,
    SystemEvent
)

from .kafka_producer import (
    KafkaEventProducer,
    get_event_producer
)

from .kafka_consumer import (
    KafkaEventConsumer,
    create_consumer
)

__all__ = [
    # Event Types
    'EventType',
    'MarketDataEvent',
    'SignalEvent',
    'TradeEvent',
    'RiskEvent',
    'SystemEvent',

    # Producer
    'KafkaEventProducer',
    'get_event_producer',

    # Consumer
    'KafkaEventConsumer',
    'create_consumer'
]

__version__ = '1.0.0'
