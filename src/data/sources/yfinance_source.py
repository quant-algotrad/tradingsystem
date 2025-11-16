"""
YFinance Data Source Adapter
Adapts Yahoo Finance API to our standard data source interface

Pattern: Adapter Pattern
- Adapts yfinance library to IDataSource interface
- Normalizes YFinance responses to our data models
"""

import time
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from src.data.base_source import BaseDataSource, DataNormalizer, IRateLimitedDataSource
from src.data.models import (
    DataFetchRequest,
    DataFetchResponse,
    OHLCV,
    OHLCVSeries,
    SymbolInfo,
    Quote,
    DataQuality
)
from src.utils import get_logger

logger = get_logger(__name__)

# Conditional import for yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None


class YFinanceSource(BaseDataSource, IRateLimitedDataSource):
    """
    Yahoo Finance data source adapter

    Features:
    - Historical OHLCV data
    - Real-time quotes
    - Symbol information
    - Automatic rate limiting
    - Error handling and retries

    Limitations:
    - Free tier: No strict rate limits but throttling exists
    - Intraday data limited to last 60 days
    - No official API (unofficial library)
    """

    def __init__(self):
        """Initialize YFinance data source"""
        super().__init__(name="YFinance")

        if not YFINANCE_AVAILABLE:
            raise ImportError(
                "yfinance library not available. Install with: pip install yfinance"
            )

        # Rate limiting (conservative estimates for free tier)
        self._requests_per_minute = 60
        self._request_times: list[datetime] = []

        # Timeframe mapping
        self._timeframe_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '1d': '1d',
            '1w': '1wk',
            '1M': '1mo'
        }

    # ========================================
    # IDataSource Implementation
    # ========================================

    def _fetch_historical_impl(self, request: DataFetchRequest) -> DataFetchResponse:
        """
        Fetch historical data from Yahoo Finance

        Args:
            request: Data fetch request

        Returns:
            DataFetchResponse with OHLCV series
        """
        start_time = datetime.now()

        try:
            # Normalize symbol
            symbol = DataNormalizer.normalize_symbol(request.symbol, "NSE")

            # Normalize timeframe
            timeframe = DataNormalizer.normalize_timeframe(request.timeframe)
            yf_interval = self._timeframe_map.get(timeframe, '1d')

            # Check rate limit
            if not self.can_make_request():
                wait_time = self.wait_for_rate_limit()
                if wait_time > 0:
                    time.sleep(wait_time)

            # Fetch data using yfinance
            ticker = yf.Ticker(symbol)

            df = ticker.history(
                start=request.start_date,
                end=request.end_date,
                interval=yf_interval,
                auto_adjust=False,  # We'll handle adjustments separately
                actions=False  # Don't include dividends/splits in OHLCV
            )

            # Record request time for rate limiting
            self._request_times.append(datetime.now())

            # Check if data received
            if df is None or df.empty:
                return self._create_error_response(
                    request,
                    f"No data available for {symbol}",
                    "NO_DATA"
                )

            # Normalize DataFrame
            df = DataNormalizer.normalize_dataframe(df)

            # Convert to OHLCVSeries
            ohlcv_series = self._dataframe_to_ohlcv_series(
                df, request.symbol, timeframe
            )

            # Assess data quality
            quality = self._assess_data_quality(ohlcv_series)
            ohlcv_series.quality = quality
            ohlcv_series.data_source = self.name

            # Calculate duration
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return self._create_success_response(request, ohlcv_series, duration_ms)

        except Exception as e:
            error_msg = f"YFinance fetch failed: {str(e)}"
            return self._create_error_response(request, error_msg, "FETCH_ERROR")

    def fetch_quote(self, symbol: str) -> Optional[Quote]:
        """
        Fetch real-time quote from Yahoo Finance

        Args:
            symbol: Stock symbol

        Returns:
            Quote object or None
        """
        try:
            # Normalize symbol
            symbol_yf = DataNormalizer.normalize_symbol(symbol, "NSE")

            # Check rate limit
            if not self.can_make_request():
                self.wait_for_rate_limit()

            # Fetch ticker
            ticker = yf.Ticker(symbol_yf)
            info = ticker.info

            # Record request
            self._request_times.append(datetime.now())

            # Extract quote data
            quote = Quote(
                symbol=symbol,
                timestamp=datetime.now(),
                last_price=info.get('currentPrice', info.get('regularMarketPrice', 0.0)),
                open=info.get('open', info.get('regularMarketOpen', 0.0)),
                high=info.get('dayHigh', info.get('regularMarketDayHigh', 0.0)),
                low=info.get('dayLow', info.get('regularMarketDayLow', 0.0)),
                close=info.get('previousClose', 0.0),
                previous_close=info.get('previousClose', 0.0),
                volume=info.get('volume', info.get('regularMarketVolume', 0))
            )

            return quote

        except Exception as e:
            logger.error(f"YFinance quote fetch failed for {symbol}: {e}")
            return None

    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """
        Get symbol/company information

        Args:
            symbol: Stock symbol

        Returns:
            SymbolInfo object or None
        """
        try:
            # Normalize symbol
            symbol_yf = DataNormalizer.normalize_symbol(symbol, "NSE")

            # Check rate limit
            if not self.can_make_request():
                self.wait_for_rate_limit()

            # Fetch ticker info
            ticker = yf.Ticker(symbol_yf)
            info = ticker.info

            # Record request
            self._request_times.append(datetime.now())

            # Create SymbolInfo
            symbol_info = SymbolInfo(
                symbol=symbol,
                name=info.get('longName', info.get('shortName', symbol)),
                exchange=info.get('exchange', 'NSE'),
                sector=info.get('sector'),
                industry=info.get('industry'),
                market_cap=info.get('marketCap'),
                last_price=info.get('currentPrice', info.get('regularMarketPrice')),
                previous_close=info.get('previousClose'),
                is_tradable=True,
                is_active=True
            )

            return symbol_info

        except Exception as e:
            logger.error(f"YFinance symbol info fetch failed for {symbol}: {e}")
            return None

    # ========================================
    # IRateLimitedDataSource Implementation
    # ========================================

    def get_rate_limit_info(self) -> dict:
        """Get rate limit information"""
        return {
            'requests_per_minute': self._requests_per_minute,
            'requests_in_last_minute': len(self._get_recent_requests()),
            'can_make_request': self.can_make_request()
        }

    def wait_for_rate_limit(self) -> float:
        """
        Wait if rate limited

        Returns:
            Seconds waited
        """
        recent_requests = self._get_recent_requests()

        if len(recent_requests) >= self._requests_per_minute:
            # Calculate wait time
            oldest_request = min(recent_requests)
            wait_until = oldest_request + timedelta(minutes=1)
            wait_seconds = (wait_until - datetime.now()).total_seconds()

            if wait_seconds > 0:
                logger.info(f"Rate limit reached, waiting {wait_seconds:.1f}s")
                time.sleep(wait_seconds)
                return wait_seconds

        return 0.0

    def can_make_request(self) -> bool:
        """Check if can make request without hitting rate limit"""
        recent_requests = self._get_recent_requests()
        return len(recent_requests) < self._requests_per_minute

    # ========================================
    # Helper Methods
    # ========================================

    def _get_recent_requests(self) -> list[datetime]:
        """Get requests in the last minute"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        self._request_times = [
            req_time for req_time in self._request_times
            if req_time > one_minute_ago
        ]

        return self._request_times

    def _dataframe_to_ohlcv_series(self, df: pd.DataFrame,
                                   symbol: str, timeframe: str) -> OHLCVSeries:
        """
        Convert DataFrame to OHLCVSeries

        Args:
            df: OHLCV DataFrame
            symbol: Stock symbol
            timeframe: Timeframe string

        Returns:
            OHLCVSeries object
        """
        bars = []

        for timestamp, row in df.iterrows():
            try:
                bar = OHLCV(
                    timestamp=pd.to_datetime(timestamp),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume']),
                    adjusted_close=float(row.get('adjusted_close', row['close'])),
                    symbol=symbol,
                    timeframe=timeframe
                )
                bars.append(bar)
            except (ValueError, KeyError) as e:
                # Skip invalid bars
                logger.warning(f"Skipping invalid bar at {timestamp}: {e}")
                continue

        return OHLCVSeries(
            symbol=symbol,
            timeframe=timeframe,
            bars=bars,
            data_source=self.name
        )

    def _assess_data_quality(self, series: OHLCVSeries) -> DataQuality:
        """
        Assess quality of fetched data

        Args:
            series: OHLCV series to assess

        Returns:
            DataQuality enum
        """
        if len(series) == 0:
            return DataQuality.INVALID

        # Check for gaps
        timestamps = [bar.timestamp for bar in series.bars]
        gaps = []

        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i-1]).total_seconds()
            gaps.append(gap)

        # Calculate expected interval based on timeframe
        if series.timeframe == '1d':
            expected_gap = 86400  # 1 day in seconds
        elif series.timeframe == '1h':
            expected_gap = 3600
        elif series.timeframe == '15m':
            expected_gap = 900
        elif series.timeframe == '5m':
            expected_gap = 300
        elif series.timeframe == '1m':
            expected_gap = 60
        else:
            expected_gap = 86400

        # Allow some tolerance for market hours and weekends
        tolerance = 2.5 if series.timeframe == '1d' else 1.5

        # Count large gaps
        large_gaps = sum(1 for gap in gaps if gap > expected_gap * tolerance)
        gap_ratio = large_gaps / len(gaps) if gaps else 0

        # Assess quality
        if gap_ratio == 0:
            return DataQuality.EXCELLENT
        elif gap_ratio < 0.05:
            return DataQuality.GOOD
        elif gap_ratio < 0.15:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR
