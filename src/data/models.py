"""
Data Models and DTOs
Domain objects for market data representation
Follows Data Transfer Object (DTO) pattern for clean data encapsulation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import pandas as pd


# ============================================
# ENUMS
# ============================================

class DataQuality(Enum):
    """Data quality assessment"""
    EXCELLENT = "excellent"  # No issues
    GOOD = "good"            # Minor issues, usable
    FAIR = "fair"            # Some issues, needs cleaning
    POOR = "poor"            # Major issues, questionable
    INVALID = "invalid"      # Unusable data


class DataSourceStatus(Enum):
    """Data source health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


# ============================================
# CORE DATA MODELS
# ============================================

@dataclass
class OHLCV:
    """
    Single OHLCV bar (candlestick)
    Immutable data transfer object
    """
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    # Derived fields
    adjusted_close: Optional[float] = None

    # Metadata
    symbol: Optional[str] = None
    timeframe: Optional[str] = None

    def __post_init__(self):
        """Validate OHLCV data"""
        # Basic sanity checks
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) cannot be less than Low ({self.low})")

        if not (self.low <= self.open <= self.high):
            raise ValueError(f"Open ({self.open}) must be between Low and High")

        if not (self.low <= self.close <= self.high):
            raise ValueError(f"Close ({self.close}) must be between Low and High")

        if self.volume < 0:
            raise ValueError(f"Volume cannot be negative: {self.volume}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'adjusted_close': self.adjusted_close,
            'symbol': self.symbol,
            'timeframe': self.timeframe
        }

    @property
    def typical_price(self) -> float:
        """Calculate typical price (HLC/3)"""
        return (self.high + self.low + self.close) / 3.0

    @property
    def range(self) -> float:
        """Price range (High - Low)"""
        return self.high - self.low

    @property
    def body(self) -> float:
        """Candle body size (abs(Close - Open))"""
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        """Is bullish candle (Close > Open)"""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Is bearish candle (Close < Open)"""
        return self.close < self.open


@dataclass
class OHLCVSeries:
    """
    Time series of OHLCV data
    Container for multiple bars with metadata
    """
    symbol: str
    timeframe: str
    bars: List[OHLCV] = field(default_factory=list)

    # Metadata
    data_source: Optional[str] = None
    fetched_at: datetime = field(default_factory=datetime.now)
    quality: DataQuality = DataQuality.GOOD

    # Data range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def __post_init__(self):
        """Initialize date range"""
        if self.bars:
            self.start_date = min(bar.timestamp for bar in self.bars)
            self.end_date = max(bar.timestamp for bar in self.bars)

    def __len__(self) -> int:
        """Number of bars"""
        return len(self.bars)

    def __getitem__(self, index: int) -> OHLCV:
        """Get bar by index"""
        return self.bars[index]

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert to pandas DataFrame

        Returns:
            DataFrame with OHLCV columns
        """
        if not self.bars:
            return pd.DataFrame()

        data = {
            'timestamp': [bar.timestamp for bar in self.bars],
            'open': [bar.open for bar in self.bars],
            'high': [bar.high for bar in self.bars],
            'low': [bar.low for bar in self.bars],
            'close': [bar.close for bar in self.bars],
            'volume': [bar.volume for bar in self.bars],
        }

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        return df

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, symbol: str,
                      timeframe: str) -> 'OHLCVSeries':
        """
        Create from pandas DataFrame

        Args:
            df: DataFrame with OHLC columns (timestamp as index)
            symbol: Stock symbol
            timeframe: Timeframe string

        Returns:
            OHLCVSeries instance
        """
        bars = []

        for timestamp, row in df.iterrows():
            bar = OHLCV(
                timestamp=timestamp if isinstance(timestamp, datetime) else pd.to_datetime(timestamp),
                open=float(row['open']) if 'open' in row else float(row['Open']),
                high=float(row['high']) if 'high' in row else float(row['High']),
                low=float(row['low']) if 'low' in row else float(row['Low']),
                close=float(row['close']) if 'close' in row else float(row['Close']),
                volume=int(row['volume']) if 'volume' in row else int(row['Volume']),
                symbol=symbol,
                timeframe=timeframe
            )
            bars.append(bar)

        return cls(
            symbol=symbol,
            timeframe=timeframe,
            bars=bars
        )

    def get_latest(self, n: int = 1) -> List[OHLCV]:
        """Get latest n bars"""
        return self.bars[-n:] if self.bars else []

    def get_closes(self) -> List[float]:
        """Get all close prices"""
        return [bar.close for bar in self.bars]

    def get_volumes(self) -> List[int]:
        """Get all volumes"""
        return [bar.volume for bar in self.bars]


@dataclass
class SymbolInfo:
    """
    Stock/Symbol information
    Company metadata and trading details
    """
    symbol: str
    name: str
    exchange: str

    # Company details
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None

    # Trading details
    isin: Optional[str] = None
    lot_size: int = 1
    tick_size: float = 0.05

    # Price info
    last_price: Optional[float] = None
    previous_close: Optional[float] = None

    # Limits
    upper_circuit: Optional[float] = None
    lower_circuit: Optional[float] = None

    # Status
    is_tradable: bool = True
    is_active: bool = True

    # Metadata
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'exchange': self.exchange,
            'sector': self.sector,
            'industry': self.industry,
            'market_cap': self.market_cap,
            'isin': self.isin,
            'lot_size': self.lot_size,
            'tick_size': self.tick_size,
            'last_price': self.last_price,
            'previous_close': self.previous_close,
            'upper_circuit': self.upper_circuit,
            'lower_circuit': self.lower_circuit,
            'is_tradable': self.is_tradable,
            'is_active': self.is_active,
            'updated_at': self.updated_at
        }


@dataclass
class Quote:
    """
    Real-time quote data
    Latest market data for a symbol
    """
    symbol: str
    timestamp: datetime

    # Price data
    last_price: float
    open: float
    high: float
    low: float
    close: float
    previous_close: float

    # Volume
    volume: int

    # Bid/Ask
    bid_price: Optional[float] = None
    bid_quantity: Optional[int] = None
    ask_price: Optional[float] = None
    ask_quantity: Optional[int] = None

    # Derived
    change: Optional[float] = None
    change_percent: Optional[float] = None

    def __post_init__(self):
        """Calculate derived fields"""
        if self.change is None and self.previous_close:
            self.change = self.last_price - self.previous_close

        if self.change_percent is None and self.previous_close and self.previous_close != 0:
            self.change_percent = (self.change / self.previous_close) * 100.0


@dataclass
class DataFetchRequest:
    """
    Request object for data fetching
    Encapsulates all parameters for a data fetch operation
    """
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime

    # Options
    adjust_splits: bool = True
    adjust_dividends: bool = True
    include_prepost: bool = False

    # Metadata
    request_id: Optional[str] = None
    requested_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate request parameters"""
        errors = []

        if not self.symbol:
            errors.append("Symbol is required")

        if not self.timeframe:
            errors.append("Timeframe is required")

        if self.start_date >= self.end_date:
            errors.append("Start date must be before end date")

        if self.end_date > datetime.now():
            errors.append("End date cannot be in the future")

        return (len(errors) == 0, errors)


@dataclass
class DataFetchResponse:
    """
    Response object for data fetching
    Contains fetched data and metadata
    """
    request: DataFetchRequest
    success: bool

    # Data
    data: Optional[OHLCVSeries] = None

    # Metadata
    data_source: Optional[str] = None
    fetch_duration_ms: Optional[float] = None
    bars_fetched: int = 0
    quality: DataQuality = DataQuality.GOOD

    # Error info
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Timestamps
    fetched_at: datetime = field(default_factory=datetime.now)

    def is_success(self) -> bool:
        """Check if fetch was successful"""
        return self.success and self.data is not None and len(self.data) > 0

    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """Get data as DataFrame"""
        return self.data.to_dataframe() if self.data else None


@dataclass
class DataSourceHealth:
    """
    Health status of a data source
    For monitoring and circuit breaker logic
    """
    source_name: str
    status: DataSourceStatus

    # Metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0

    # Rate limiting
    requests_per_minute: int = 0
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_at: Optional[datetime] = None

    # Errors
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    consecutive_failures: int = 0

    # Timestamps
    last_success_at: Optional[datetime] = None
    checked_at: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0

    @property
    def is_healthy(self) -> bool:
        """Check if source is healthy"""
        return self.status == DataSourceStatus.HEALTHY

    @property
    def is_available(self) -> bool:
        """Check if source is available for use"""
        return self.status in [DataSourceStatus.HEALTHY, DataSourceStatus.DEGRADED]
