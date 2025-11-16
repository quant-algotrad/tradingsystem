"""
Data Fetcher Manager
Main orchestrator for data fetching operations

Patterns:
- Facade Pattern: Simplifies complex data fetching logic
- Strategy Pattern: Switches between data sources
- Chain of Responsibility: Falls back through sources on failure
"""

import time
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pandas as pd

from src.data.base_source import IDataSource
from src.data.models import (
    DataFetchRequest,
    DataFetchResponse,
    OHLCVSeries,
    SymbolInfo,
    Quote,
    DataQuality
)
from src.data.data_source_factory import DataSourceFactory
from src.config import get_api_config, DataSource as DataSourceEnum
from src.utils import get_logger

logger = get_logger(__name__)


class DataFetcher:
    """
    Main data fetcher orchestrator

    Pattern: Facade Pattern
    - Provides simple interface for complex data fetching
    - Handles source selection, fallback, retry logic
    - Manages multiple data sources

    Pattern: Strategy Pattern
    - Dynamically selects best data source
    - Can switch strategies at runtime

    Pattern: Chain of Responsibility
    - Tries primary source first
    - Falls back to alternatives on failure
    """

    def __init__(self, config=None):
        """
        Initialize data fetcher

        Args:
            config: Optional APIConfig (uses global config if None)
        """
        self.config = config or get_api_config()

        # Initialize data sources
        self._primary_source: Optional[IDataSource] = None
        self._fallback_sources: List[IDataSource] = []

        self._initialize_sources()

        # Statistics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._cache_hits = 0

    def _initialize_sources(self):
        """Initialize data sources from configuration"""
        try:
            # Create primary source
            primary_name = self.config.data_source.primary_source
            self._primary_source = DataSourceFactory.create_from_config(primary_name)

            if not self._primary_source:
                logger.warning(f"Could not create primary source: {primary_name.value}")

            # Create fallback sources
            for fallback_name in self.config.data_source.fallback_sources:
                if fallback_name == primary_name.value:
                    continue  # Skip if same as primary

                try:
                    fallback_source = DataSourceFactory.create(fallback_name)
                    if fallback_source:
                        self._fallback_sources.append(fallback_source)
                except Exception as e:
                    logger.warning(f"Could not create fallback source {fallback_name}: {e}")

            logger.info(
                f"Data sources initialized - "
                f"Primary: {self._primary_source.get_name() if self._primary_source else 'None'}, "
                f"Fallbacks: {[s.get_name() for s in self._fallback_sources]}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize data sources: {e}")

    # ========================================
    # Public API
    # ========================================

    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        max_retries: int = 2
    ) -> DataFetchResponse:
        """
        Fetch historical OHLCV data with automatic fallback

        Args:
            symbol: Stock symbol
            timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)
            start_date: Start date
            end_date: End date (default: now)
            max_retries: Maximum retry attempts per source

        Returns:
            DataFetchResponse with OHLCV data

        Pattern: Chain of Responsibility
        - Tries primary source first
        - Falls back to alternatives on failure
        """
        self._total_requests += 1

        if end_date is None:
            end_date = datetime.now()

        # Create request
        request = DataFetchRequest(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            request_id=f"REQ_{self._total_requests}"
        )

        # Validate request
        is_valid, errors = request.validate()
        if not is_valid:
            return self._create_error_response(request, f"Invalid request: {errors}")

        # Try primary source first
        if self._primary_source and self._primary_source.is_available():
            response = self._fetch_with_retry(
                self._primary_source,
                request,
                max_retries
            )

            if response.is_success():
                self._successful_requests += 1
                return response

        # Fallback to other sources
        if self.config.data_source.enable_fallback:
            for fallback_source in self._fallback_sources:
                if not fallback_source.is_available():
                    continue

                logger.info(f"Falling back to: {fallback_source.get_name()}")

                response = self._fetch_with_retry(
                    fallback_source,
                    request,
                    max_retries=1  # Fewer retries for fallback
                )

                if response.is_success():
                    self._successful_requests += 1
                    return response

        # All sources failed
        self._failed_requests += 1
        return self._create_error_response(
            request,
            "All data sources failed",
            "ALL_SOURCES_FAILED"
        )

    def fetch_quote(self, symbol: str) -> Optional[Quote]:
        """
        Fetch real-time quote

        Args:
            symbol: Stock symbol

        Returns:
            Quote object or None
        """
        # Try primary source
        if self._primary_source and self._primary_source.is_available():
            quote = self._primary_source.fetch_quote(symbol)
            if quote:
                return quote

        # Try fallback sources
        for source in self._fallback_sources:
            if not source.is_available():
                continue

            quote = source.fetch_quote(symbol)
            if quote:
                return quote

        return None

    def fetch_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get symbol information

        Args:
            symbol: Stock symbol

        Returns:
            SymbolInfo object or None
        """
        # Try primary source
        if self._primary_source and self._primary_source.is_available():
            info = self._primary_source.get_symbol_info(symbol)
            if info:
                return info

        # Try fallback sources
        for source in self._fallback_sources:
            if not source.is_available():
                continue

            info = source.get_symbol_info(symbol)
            if info:
                return info

        return None

    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> Dict[str, DataFetchResponse]:
        """
        Fetch historical data for multiple symbols

        Args:
            symbols: List of symbols
            timeframe: Timeframe
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary mapping symbol to DataFetchResponse
        """
        results = {}

        for symbol in symbols:
            response = self.fetch_historical(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            results[symbol] = response

            # Small delay to avoid rate limiting
            time.sleep(0.1)

        return results

    # ========================================
    # Helper Methods
    # ========================================

    def _fetch_with_retry(
        self,
        source: IDataSource,
        request: DataFetchRequest,
        max_retries: int
    ) -> DataFetchResponse:
        """
        Fetch data with retry logic

        Args:
            source: Data source to use
            request: Fetch request
            max_retries: Maximum retry attempts

        Returns:
            DataFetchResponse
        """
        last_response = None
        retry_delay = self.config.data_source.source_timeout_seconds

        for attempt in range(max_retries + 1):
            try:
                response = source.fetch_historical(request)

                if response.is_success():
                    return response

                # Store last response for potential return
                last_response = response

                # If not last attempt, retry
                if attempt < max_retries:
                    wait_time = retry_delay * (attempt + 1)  # Linear backoff
                    logger.info(
                        f"Retry {attempt + 1}/{max_retries} for {source.get_name()} "
                        f"after {wait_time}s"
                    )
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {source.get_name()}: {e}")

                if attempt < max_retries:
                    time.sleep(retry_delay)

        # Return last response or create error response
        return last_response or self._create_error_response(
            request,
            f"Max retries exceeded for {source.get_name()}",
            "MAX_RETRIES_EXCEEDED"
        )

    def _create_error_response(
        self,
        request: DataFetchRequest,
        error_message: str,
        error_code: str = "ERROR"
    ) -> DataFetchResponse:
        """Create error response"""
        return DataFetchResponse(
            request=request,
            success=False,
            error_message=error_message,
            error_code=error_code,
            quality=DataQuality.INVALID
        )

    # ========================================
    # Statistics & Health
    # ========================================

    def get_statistics(self) -> dict:
        """Get fetcher statistics"""
        success_rate = 0.0
        if self._total_requests > 0:
            success_rate = (self._successful_requests / self._total_requests) * 100.0

        return {
            'total_requests': self._total_requests,
            'successful_requests': self._successful_requests,
            'failed_requests': self._failed_requests,
            'success_rate': success_rate,
            'cache_hits': self._cache_hits,
            'primary_source': self._primary_source.get_name() if self._primary_source else None,
            'fallback_sources': [s.get_name() for s in self._fallback_sources]
        }

    def get_source_health(self) -> dict:
        """Get health status of all sources"""
        health = {}

        if self._primary_source:
            health['primary'] = self._primary_source.get_health()

        health['fallbacks'] = [
            source.get_health() for source in self._fallback_sources
        ]

        return health

    def print_statistics(self):
        """Print statistics"""
        stats = self.get_statistics()

        print("\n" + "="*60)
        print("DATA FETCHER STATISTICS")
        print("="*60)
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful: {stats['successful_requests']}")
        print(f"Failed: {stats['failed_requests']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Cache Hits: {stats['cache_hits']}")
        print(f"Primary Source: {stats['primary_source']}")
        print(f"Fallback Sources: {stats['fallback_sources']}")
        print("="*60)


# ========================================
# Convenience Functions
# ========================================

# Global instance (lazy-loaded)
_global_fetcher: Optional[DataFetcher] = None


def get_data_fetcher() -> DataFetcher:
    """
    Get global data fetcher instance

    Returns:
        DataFetcher singleton
    """
    global _global_fetcher

    if _global_fetcher is None:
        _global_fetcher = DataFetcher()

    return _global_fetcher


def fetch_historical_data(
    symbol: str,
    timeframe: str,
    start_date: datetime,
    end_date: Optional[datetime] = None
) -> Optional[pd.DataFrame]:
    """
    Convenience function to fetch historical data as DataFrame

    Args:
        symbol: Stock symbol
        timeframe: Timeframe
        start_date: Start date
        end_date: End date

    Returns:
        DataFrame or None
    """
    fetcher = get_data_fetcher()
    response = fetcher.fetch_historical(symbol, timeframe, start_date, end_date)

    if response.is_success():
        return response.get_dataframe()

    return None
