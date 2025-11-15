"""
Data Source Factory
Creates data source instances using Factory Pattern

Pattern: Factory Pattern + Registry Pattern
- Centralized data source creation
- Registry of available sources
- Dynamic source selection based on config
"""

from typing import Optional, Dict, Type
from src.data.base_source import IDataSource
from src.data.sources.yfinance_source import YFinanceSource, YFINANCE_AVAILABLE
from src.config import DataSource as DataSourceEnum


class DataSourceFactory:
    """
    Factory for creating data source instances

    Pattern: Factory Pattern
    - Encapsulates object creation logic
    - Returns instances conforming to IDataSource interface

    Pattern: Registry Pattern
    - Maintains registry of available data sources
    - Allows registration of new sources at runtime
    """

    # Class-level registry of data sources
    _registry: Dict[str, Type[IDataSource]] = {}

    # Singleton-like initialization flag
    _initialized: bool = False

    @classmethod
    def _initialize_registry(cls):
        """Initialize the data source registry"""
        if cls._initialized:
            return

        # Register YFinance if available
        if YFINANCE_AVAILABLE:
            cls.register(DataSourceEnum.YFINANCE.value, YFinanceSource)

        # Future: Register other sources
        # if NSEPY_AVAILABLE:
        #     cls.register(DataSourceEnum.NSEPY.value, NSEpySource)
        # if ALPHA_VANTAGE_AVAILABLE:
        #     cls.register(DataSourceEnum.ALPHA_VANTAGE.value, AlphaVantageSource)

        cls._initialized = True

    @classmethod
    def register(cls, name: str, source_class: Type[IDataSource]):
        """
        Register a new data source

        Args:
            name: Data source name
            source_class: Data source class (must implement IDataSource)
        """
        if not issubclass(source_class, IDataSource):
            raise TypeError(f"{source_class} must implement IDataSource interface")

        cls._registry[name.lower()] = source_class
        print(f"[INFO] Registered data source: {name}")

    @classmethod
    def create(cls, source_name: str) -> Optional[IDataSource]:
        """
        Create a data source instance

        Args:
            source_name: Name of data source to create

        Returns:
            IDataSource instance or None if not available

        Raises:
            ValueError: If source_name is not registered
        """
        cls._initialize_registry()

        source_name_lower = source_name.lower()

        if source_name_lower not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Data source '{source_name}' not found. "
                f"Available sources: {available}"
            )

        try:
            source_class = cls._registry[source_name_lower]
            instance = source_class()
            print(f"[INFO] Created data source: {instance.get_name()}")
            return instance

        except Exception as e:
            print(f"[ERROR] Failed to create data source '{source_name}': {e}")
            return None

    @classmethod
    def create_from_config(cls, config_source: DataSourceEnum) -> Optional[IDataSource]:
        """
        Create data source from configuration enum

        Args:
            config_source: DataSource enum from config

        Returns:
            IDataSource instance or None
        """
        return cls.create(config_source.value)

    @classmethod
    def get_available_sources(cls) -> list[str]:
        """
        Get list of available data sources

        Returns:
            List of registered source names
        """
        cls._initialize_registry()
        return list(cls._registry.keys())

    @classmethod
    def is_available(cls, source_name: str) -> bool:
        """
        Check if a data source is available

        Args:
            source_name: Data source name

        Returns:
            True if available, False otherwise
        """
        cls._initialize_registry()
        return source_name.lower() in cls._registry


# Convenience function
def create_data_source(source_name: str) -> Optional[IDataSource]:
    """
    Convenience function to create a data source

    Args:
        source_name: Name of data source

    Returns:
        IDataSource instance
    """
    return DataSourceFactory.create(source_name)
