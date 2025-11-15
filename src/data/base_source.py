"""
Base Data Source Interface
Abstract base classes for data providers
Follows Strategy Pattern and Interface Segregation Principle
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from src.data.models import (
    DataFetchRequest,
    DataFetchResponse,
    OHLCVSeries,
    SymbolInfo,
    Quote,
    DataSourceHealth,
    DataSourceStatus,
    DataQuality
)


# ============================================
# INTERFACE: Data Source Contract
# ============================================

class IDataSource(ABC):
    """
    Interface for all data sources

    SOLID Principles:
    - Interface Segregation: Specific interface for data providers
    - Dependency Inversion: Depend on abstraction, not concrete classes

    Pattern: Strategy Pattern
    - Different data sources implement same interface
    - Can be swapped at runtime
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get data source name"""
        pass

    @abstractmethod
    def fetch_historical(self, request: DataFetchRequest) -> DataFetchResponse:
        """
        Fetch historical OHLCV data

        Args:
            request: Data fetch request

        Returns:
            Data fetch response with OHLCV series
        """
        pass

    @abstractmethod
    def fetch_quote(self, symbol: str) -> Optional[Quote]:
        """
        Fetch real-time quote

        Args:
            symbol: Stock symbol

        Returns:
            Quote object or None if failed
        """
        pass

    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get symbol/company information

        Args:
            symbol: Stock symbol

        Returns:
            SymbolInfo object or None if not found
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if data source is available"""
        pass

    @abstractmethod
    def get_health(self) -> DataSourceHealth:
        """Get health status of data source"""
        pass


# ============================================
# ABSTRACT BASE: Data Source Implementation
# ============================================

class BaseDataSource(IDataSource, ABC):
    """
    Abstract base class for data sources

    Provides common functionality:
    - Health tracking
    - Error handling
    - Response time tracking
    - Rate limiting awareness

    SOLID Principles:
    - Single Responsibility: Base functionality only
    - Open/Closed: Open for extension, closed for modification
    """

    def __init__(self, name: str):
        """
        Initialize base data source

        Args:
            name: Data source name
        """
        self.name = name
        self._health = DataSourceHealth(
            source_name=name,
            status=DataSourceStatus.HEALTHY
        )

    def get_name(self) -> str:
        """Get data source name"""
        return self.name

    def is_available(self) -> bool:
        """Check if data source is available"""
        return self._health.is_available

    def get_health(self) -> DataSourceHealth:
        """Get health status"""
        return self._health

    # ========================================
    # Protected Helper Methods
    # ========================================

    def _record_success(self, response_time_ms: float):
        """Record successful request"""
        self._health.total_requests += 1
        self._health.successful_requests += 1
        self._health.consecutive_failures = 0
        self._health.last_success_at = datetime.now()

        # Update average response time
        total = self._health.total_requests
        avg = self._health.avg_response_time_ms
        self._health.avg_response_time_ms = ((avg * (total - 1)) + response_time_ms) / total

        # Update status if was degraded
        if self._health.status == DataSourceStatus.DEGRADED:
            self._health.status = DataSourceStatus.HEALTHY

    def _record_failure(self, error_message: str, error_code: Optional[str] = None):
        """Record failed request"""
        self._health.total_requests += 1
        self._health.failed_requests += 1
        self._health.consecutive_failures += 1
        self._health.last_error = error_message
        self._health.last_error_at = datetime.now()

        # Update status based on consecutive failures
        if self._health.consecutive_failures >= 5:
            self._health.status = DataSourceStatus.UNAVAILABLE
        elif self._health.consecutive_failures >= 3:
            self._health.status = DataSourceStatus.DEGRADED
        elif self._health.consecutive_failures >= 1:
            if self._health.status == DataSourceStatus.HEALTHY:
                self._health.status = DataSourceStatus.DEGRADED

    def _record_rate_limit(self, reset_at: Optional[datetime] = None):
        """Record rate limit hit"""
        self._health.status = DataSourceStatus.RATE_LIMITED
        self._health.rate_limit_reset_at = reset_at
        self._health.last_error = "Rate limit exceeded"
        self._health.last_error_at = datetime.now()

    def _create_error_response(self, request: DataFetchRequest,
                              error_message: str,
                              error_code: Optional[str] = None) -> DataFetchResponse:
        """
        Create error response

        Args:
            request: Original request
            error_message: Error description
            error_code: Optional error code

        Returns:
            DataFetchResponse with error
        """
        return DataFetchResponse(
            request=request,
            success=False,
            data_source=self.name,
            error_message=error_message,
            error_code=error_code,
            quality=DataQuality.INVALID
        )

    def _create_success_response(self, request: DataFetchRequest,
                                data: OHLCVSeries,
                                fetch_duration_ms: float) -> DataFetchResponse:
        """
        Create success response

        Args:
            request: Original request
            data: Fetched OHLCV series
            fetch_duration_ms: Fetch duration in milliseconds

        Returns:
            DataFetchResponse with data
        """
        return DataFetchResponse(
            request=request,
            success=True,
            data=data,
            data_source=self.name,
            fetch_duration_ms=fetch_duration_ms,
            bars_fetched=len(data),
            quality=data.quality
        )

    def _validate_request(self, request: DataFetchRequest) -> tuple[bool, Optional[str]]:
        """
        Validate data fetch request

        Args:
            request: Request to validate

        Returns:
            (is_valid, error_message)
        """
        is_valid, errors = request.validate()
        if not is_valid:
            return (False, "; ".join(errors))
        return (True, None)

    # ========================================
    # Template Method Pattern
    # ========================================

    def fetch_historical(self, request: DataFetchRequest) -> DataFetchResponse:
        """
        Template method for fetching historical data

        Pattern: Template Method
        - Defines skeleton of algorithm
        - Subclasses implement specific steps
        """
        # Validate request
        is_valid, error_msg = self._validate_request(request)
        if not is_valid:
            return self._create_error_response(request, f"Invalid request: {error_msg}")

        # Check availability
        if not self.is_available():
            return self._create_error_response(
                request,
                f"Data source {self.name} is not available",
                "SOURCE_UNAVAILABLE"
            )

        # Delegate to concrete implementation
        try:
            start_time = datetime.now()
            response = self._fetch_historical_impl(request)
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            if response.success:
                self._record_success(duration_ms)
            else:
                self._record_failure(response.error_message or "Unknown error")

            return response

        except Exception as e:
            error_msg = f"Unexpected error in {self.name}: {str(e)}"
            self._record_failure(error_msg)
            return self._create_error_response(request, error_msg, "UNEXPECTED_ERROR")

    @abstractmethod
    def _fetch_historical_impl(self, request: DataFetchRequest) -> DataFetchResponse:
        """
        Concrete implementation of historical data fetch
        Must be implemented by subclasses
        """
        pass


# ============================================
# INTERFACE: Cacheable Data Source
# ============================================

class ICacheableDataSource(IDataSource):
    """
    Interface for data sources that support caching

    Pattern: Decorator Pattern (for caching layer)
    """

    @abstractmethod
    def get_cache_key(self, symbol: str, timeframe: str,
                     start_date: datetime, end_date: datetime) -> str:
        """Generate cache key for request"""
        pass

    @abstractmethod
    def should_cache(self, timeframe: str) -> bool:
        """Determine if data should be cached"""
        pass


# ============================================
# INTERFACE: Rate Limited Data Source
# ============================================

class IRateLimitedDataSource(IDataSource):
    """
    Interface for data sources with rate limits
    """

    @abstractmethod
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information"""
        pass

    @abstractmethod
    def wait_for_rate_limit(self) -> float:
        """
        Wait if rate limited

        Returns:
            Seconds waited
        """
        pass

    @abstractmethod
    def can_make_request(self) -> bool:
        """Check if can make request without hitting rate limit"""
        pass


# ============================================
# HELPER: Data Normalizer
# ============================================

class DataNormalizer:
    """
    Normalizes data from different sources into standard format

    Pattern: Adapter Pattern
    - Adapts different API responses to common format
    """

    @staticmethod
    def normalize_symbol(symbol: str, exchange: str = "NSE") -> str:
        """
        Normalize symbol format

        Examples:
            RELIANCE -> RELIANCE.NS
            SBIN.NS -> SBIN.NS
            TCS -> TCS.NS
        """
        if exchange == "NSE":
            if not symbol.endswith(".NS"):
                return f"{symbol}.NS"
        elif exchange == "BSE":
            if not symbol.endswith(".BO"):
                return f"{symbol}.BO"

        return symbol

    @staticmethod
    def normalize_timeframe(timeframe: str) -> str:
        """
        Normalize timeframe to standard format

        Examples:
            1d, 1D, daily -> 1d
            1h, 1H, 60m -> 1h
            15m, 15min -> 15m
        """
        tf_lower = timeframe.lower()

        # Daily
        if tf_lower in ['1d', 'daily', 'd']:
            return '1d'

        # Hourly
        if tf_lower in ['1h', '60m', 'h', 'hourly']:
            return '1h'

        # Minutes
        if tf_lower.endswith('m') or tf_lower.endswith('min'):
            minutes = tf_lower.replace('m', '').replace('min', '')
            return f'{minutes}m'

        return timeframe

    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize DataFrame columns to standard format

        Handles different column naming conventions:
        - YFinance: Open, High, Low, Close, Volume
        - NSEpy: open, high, low, close, volume
        """
        df_copy = df.copy()

        # Column name mapping
        column_mapping = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adjusted_close'
        }

        # Rename columns if needed
        for old_name, new_name in column_mapping.items():
            if old_name in df_copy.columns:
                df_copy.rename(columns={old_name: new_name}, inplace=True)

        # Ensure timestamp index
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            if 'timestamp' in df_copy.columns:
                df_copy.set_index('timestamp', inplace=True)
            elif 'date' in df_copy.columns:
                df_copy.set_index('date', inplace=True)

        # Sort by timestamp
        df_copy.sort_index(inplace=True)

        return df_copy
