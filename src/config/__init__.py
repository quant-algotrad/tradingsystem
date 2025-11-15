"""
Configuration Module
Provides centralized configuration management for the trading system

Design Patterns Used:
- Singleton: ConfigurationManager (single instance)
- Factory: Config creation methods
- Builder: Complex config construction
- Composition: Config hierarchies

Usage:
    from src.config import get_trading_config, get_risk_config

    trading_config = get_trading_config()
    risk_config = get_risk_config()

    capital = trading_config.position_limits.initial_capital
    max_loss = risk_config.loss_limits.max_daily_loss_percent
"""

# Core configuration classes
from .base_config import (
    IConfiguration,
    BaseConfig,
    ValidationMixin,
    ConfigType
)

# Specific configurations
from .trading_config import TradingConfig, PositionLimits, TradingHours
from .risk_config import RiskConfig, LossLimits, StopLossConfig, CircuitBreaker
from .database_config import DatabaseConfig, DatabaseConnectionConfig
from .api_config import APIConfig, BrokerAPIConfig, DataSourceConfig

# Configuration manager
from .config_manager import (
    ConfigurationManager,
    get_config_manager,
    get_trading_config,
    get_risk_config,
    get_database_config,
    get_api_config
)

# Constants
from .constants import (
    # Enums
    PositionType,
    OrderSide,
    OrderType,
    OrderStatus,
    SignalType,
    Timeframe,
    StopLossType,
    StrategyName,
    Exchange,
    BrokerType,
    DataSource,
    Environment,
    OptionType,

    # Constants classes
    MarketHours,
    RiskDefaults,
    IndicatorDefaults,
    TransactionCosts,
    SystemDefaults,
)

__all__ = [
    # Base classes
    'IConfiguration',
    'BaseConfig',
    'ValidationMixin',
    'ConfigType',

    # Specific configs
    'TradingConfig',
    'RiskConfig',
    'DatabaseConfig',
    'APIConfig',
    'PositionLimits',
    'LossLimits',
    'StopLossConfig',
    'CircuitBreaker',
    'TradingHours',
    'BrokerAPIConfig',
    'DataSourceConfig',
    'DatabaseConnectionConfig',

    # Manager
    'ConfigurationManager',
    'get_config_manager',
    'get_trading_config',
    'get_risk_config',
    'get_database_config',
    'get_api_config',

    # Enums
    'PositionType',
    'OrderSide',
    'OrderType',
    'OrderStatus',
    'SignalType',
    'Timeframe',
    'StopLossType',
    'StrategyName',
    'Exchange',
    'BrokerType',
    'DataSource',
    'Environment',
    'OptionType',

    # Constants
    'MarketHours',
    'RiskDefaults',
    'IndicatorDefaults',
    'TransactionCosts',
    'SystemDefaults',
]

__version__ = '1.0.0'
