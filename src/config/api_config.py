"""
API Configuration
Defines broker API and data source settings
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.config.base_config import BaseConfig, ValidationMixin
from src.config.constants import BrokerType, DataSource


@dataclass
class BrokerAPIConfig(ValidationMixin):
    """Broker API configuration"""

    # Broker selection
    broker_type: BrokerType = BrokerType.PAPER  # Start with paper trading
    enabled: bool = True

    # Authentication (stored securely, not in code)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    access_token: Optional[str] = None
    redirect_url: Optional[str] = None

    # API endpoints (broker-specific)
    base_url: str = ""
    websocket_url: str = ""

    # Rate limiting
    max_requests_per_second: int = 10
    max_orders_per_day: int = 100
    burst_limit: int = 20  # Max burst requests

    # Timeouts
    api_timeout_seconds: int = 30
    websocket_timeout_seconds: int = 60

    # Retry logic
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 2
    exponential_backoff: bool = True
    max_backoff_seconds: int = 16

    # Failover
    enable_failover: bool = False
    failover_broker: Optional[BrokerType] = None

    def validate(self) -> tuple[bool, List[str]]:
        """Validate broker API config"""
        errors = []

        # In live mode, credentials should be set (can be loaded from env vars/vault at runtime)
        # We don't enforce this as hard validation to allow loading credentials dynamically
        # Production systems should load credentials from environment variables or secure vault

        # Validate rate limits
        if self.max_requests_per_second < 1:
            errors.append("Max requests per second must be at least 1")

        if self.max_orders_per_day < 1:
            errors.append("Max orders per day must be at least 1")

        # Validate timeouts
        if error := self.validate_positive(self.api_timeout_seconds, "api_timeout_seconds"):
            errors.append(error)

        if self.api_timeout_seconds < 5:
            errors.append("API timeout must be at least 5 seconds")

        # Validate retry config
        if self.max_retry_attempts < 0:
            errors.append("Max retry attempts cannot be negative")

        if self.retry_delay_seconds < 1:
            errors.append("Retry delay must be at least 1 second")

        return (len(errors) == 0, errors)

    def get_headers(self) -> Dict[str, str]:
        """Generate API request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if self.api_key:
            headers["X-API-Key"] = self.api_key

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers


@dataclass
class DataSourceConfig(ValidationMixin):
    """Data source configuration for market data"""

    # Primary data source
    primary_source: DataSource = DataSource.YFINANCE

    # Historical data sources (in priority order)
    historical_sources: List[str] = field(default_factory=lambda: [
        DataSource.YFINANCE.value,
        DataSource.NSEPY.value,
    ])

    # Real-time data source
    realtime_source: DataSource = DataSource.BROKER_API

    # Fallback sources
    enable_fallback: bool = True
    fallback_sources: List[str] = field(default_factory=lambda: [
        DataSource.ALPHA_VANTAGE.value,
    ])

    # Alpha Vantage (free tier)
    alpha_vantage_api_key: Optional[str] = None
    alpha_vantage_calls_per_minute: int = 5  # Free tier limit

    # Data fetch settings
    max_retries_per_source: int = 2
    source_timeout_seconds: int = 30
    cache_data: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes

    # Data quality
    validate_data_quality: bool = True
    reject_outliers: bool = True
    outlier_threshold_std: float = 3.0  # 3 standard deviations

    def validate(self) -> tuple[bool, List[str]]:
        """Validate data source config"""
        errors = []

        # Validate historical sources not empty
        if not self.historical_sources:
            errors.append("Must have at least one historical data source")

        # Validate timeout
        if error := self.validate_positive(self.source_timeout_seconds, "source_timeout_seconds"):
            errors.append(error)

        # Validate cache TTL
        if self.cache_ttl_seconds < 10:
            errors.append("Cache TTL must be at least 10 seconds")

        # Validate outlier threshold
        if self.outlier_threshold_std < 1.0:
            errors.append("Outlier threshold must be at least 1.0 std dev")

        return (len(errors) == 0, errors)


@dataclass
class WebSocketConfig(ValidationMixin):
    """WebSocket configuration for real-time data"""

    enabled: bool = False  # Disable for paper trading
    auto_reconnect: bool = True
    reconnect_delay_seconds: int = 5
    max_reconnect_attempts: int = 10

    # Heartbeat/ping settings
    ping_interval_seconds: int = 30
    pong_timeout_seconds: int = 10

    # Message handling
    max_message_size_kb: int = 1024  # 1 MB
    message_queue_size: int = 1000

    # Subscriptions
    subscribe_to_quotes: bool = True
    subscribe_to_orders: bool = True
    subscribe_to_positions: bool = True

    def validate(self) -> tuple[bool, List[str]]:
        """Validate WebSocket config"""
        errors = []

        if self.reconnect_delay_seconds < 1:
            errors.append("Reconnect delay must be at least 1 second")

        if self.max_reconnect_attempts < 1:
            errors.append("Max reconnect attempts must be at least 1")

        if self.ping_interval_seconds < 10:
            errors.append("Ping interval must be at least 10 seconds")

        if self.message_queue_size < 100:
            errors.append("Message queue size must be at least 100")

        return (len(errors) == 0, errors)


@dataclass
class APIConfig(BaseConfig, ValidationMixin):
    """
    Main API Configuration

    Manages broker APIs and data sources
    """

    # Sub-configurations
    broker: BrokerAPIConfig = field(default_factory=BrokerAPIConfig)
    data_source: DataSourceConfig = field(default_factory=DataSourceConfig)
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)

    # Global API settings
    enable_api_caching: bool = True
    global_timeout_seconds: int = 30

    # Error handling
    log_api_errors: bool = True
    alert_on_api_failure: bool = True
    circuit_breaker_on_failures: bool = True
    max_consecutive_failures: int = 3

    # Development/Testing
    mock_api_responses: bool = False  # For testing without real API
    record_api_calls: bool = False    # For debugging

    def validate(self) -> tuple[bool, List[str]]:
        """Validate API configuration"""
        errors = []

        # Validate all sub-configurations
        for sub_config in [self.broker, self.data_source, self.websocket]:
            is_valid, sub_errors = sub_config.validate()
            errors.extend(sub_errors)

        # Validate global timeout
        if error := self.validate_positive(self.global_timeout_seconds, "global_timeout_seconds"):
            errors.append(error)

        # Validate circuit breaker
        if self.max_consecutive_failures < 1:
            errors.append("Max consecutive failures must be at least 1")

        # Logical validations
        if self.websocket.enabled and self.broker.broker_type == BrokerType.PAPER:
            errors.append("WebSocket not available in paper trading mode")

        return (len(errors) == 0, errors)

    def from_dict(self, data: Dict[str, Any]) -> 'APIConfig':
        """Create from dictionary"""
        if 'broker' in data:
            if 'broker_type' in data['broker']:
                data['broker']['broker_type'] = BrokerType(data['broker']['broker_type'])
            data['broker'] = BrokerAPIConfig(**data['broker'])

        if 'data_source' in data:
            if 'primary_source' in data['data_source']:
                data['data_source']['primary_source'] = DataSource(data['data_source']['primary_source'])
            if 'realtime_source' in data['data_source']:
                data['data_source']['realtime_source'] = DataSource(data['data_source']['realtime_source'])
            data['data_source'] = DataSourceConfig(**data['data_source'])

        if 'websocket' in data:
            data['websocket'] = WebSocketConfig(**data['websocket'])

        return APIConfig(**data)

    def get_summary(self) -> str:
        """Human-readable summary"""
        return f"""
API Configuration Summary:
- Broker: {self.broker.broker_type.value.upper()}
- Broker API: {'Enabled' if self.broker.enabled else 'Disabled'}
- Primary Data Source: {self.data_source.primary_source.value}
- Real-time Source: {self.data_source.realtime_source.value}
- WebSocket: {'Enabled' if self.websocket.enabled else 'Disabled'}
- API Caching: {'Enabled' if self.enable_api_caching else 'Disabled'}
- Circuit Breaker: {'Enabled' if self.circuit_breaker_on_failures else 'Disabled'}
- Mock Mode: {'ON' if self.mock_api_responses else 'OFF'}
        """.strip()

    def is_live_trading(self) -> bool:
        """Check if configured for live trading"""
        return (self.broker.broker_type != BrokerType.PAPER and
                self.broker.enabled and
                not self.mock_api_responses)

    def is_paper_trading(self) -> bool:
        """Check if configured for paper trading"""
        return self.broker.broker_type == BrokerType.PAPER or not self.broker.enabled
