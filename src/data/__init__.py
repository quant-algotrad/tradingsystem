"""
Data Module
Handles all data fetching, normalization, and management

Design Patterns Used:
- Strategy Pattern: Interchangeable data sources
- Factory Pattern: Data source creation
- Adapter Pattern: Normalize different APIs
- Facade Pattern: Simplified data fetching interface
- Chain of Responsibility: Fallback through sources

Usage:
    from src.data import get_data_fetcher, fetch_historical_data

    # Using facade
    df = fetch_historical_data('RELIANCE.NS', '1d', start_date)

    # Using fetcher directly
    fetcher = get_data_fetcher()
    response = fetcher.fetch_historical('TCS.NS', '1h', start_date)
"""

# Models
from .models import (
    OHLCV,
    OHLCVSeries,
    SymbolInfo,
    Quote,
    DataFetchRequest,
    DataFetchResponse,
    DataSourceHealth,
    DataQuality,
    DataSourceStatus
)

# Base classes
from .base_source import (
    IDataSource,
    BaseDataSource,
    DataNormalizer
)

# Factory
from .data_source_factory import (
    DataSourceFactory,
    create_data_source
)

# Main facade
from .data_fetcher import (
    DataFetcher,
    get_data_fetcher,
    fetch_historical_data
)

__all__ = [
    # Models
    'OHLCV',
    'OHLCVSeries',
    'SymbolInfo',
    'Quote',
    'DataFetchRequest',
    'DataFetchResponse',
    'DataSourceHealth',
    'DataQuality',
    'DataSourceStatus',

    # Base
    'IDataSource',
    'BaseDataSource',
    'DataNormalizer',

    # Factory
    'DataSourceFactory',
    'create_data_source',

    # Main API
    'DataFetcher',
    'get_data_fetcher',
    'fetch_historical_data',
]

__version__ = '1.0.0'
