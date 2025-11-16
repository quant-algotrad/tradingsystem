"""
System-wide Constants
Immutable values used throughout the trading system
"""

from enum import Enum
from typing import Final


# ============================================
# MARKET CONSTANTS
# ============================================

class MarketHours:
    """Indian stock market trading hours (IST)"""
    MARKET_OPEN: Final[str] = "09:15"
    PRE_OPEN: Final[str] = "09:00"
    MARKET_CLOSE: Final[str] = "15:30"
    INTRADAY_CUTOFF: Final[str] = "14:30"  # Last entry time
    AUTO_SQUARE_TIME: Final[str] = "15:15"  # Square off intraday positions
    POST_MARKET_START: Final[str] = "15:35"  # Data processing starts


class TradingDays:
    """Market open days"""
    WEEKDAYS: Final[tuple] = (0, 1, 2, 3, 4)  # Monday to Friday
    WEEKEND: Final[tuple] = (5, 6)  # Saturday, Sunday


# ============================================
# POSITION TYPES
# ============================================

class PositionType(Enum):
    """Types of trading positions"""
    SWING = "SWING"  # Multi-day delivery positions
    INTRADAY = "INTRADAY"  # MIS - Auto-squared same day
    OPTIONS = "OPTIONS"  # Options contracts


class OrderSide(Enum):
    """Order direction"""
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"  # Sell first (intraday)
    COVER = "COVER"  # Buy back short position


class OrderType(Enum):
    """Order execution types"""
    MARKET = "MARKET"  # Immediate execution at best price
    LIMIT = "LIMIT"  # Execute at specified price or better
    STOP_LOSS = "STOP_LOSS"  # Trigger when price hits stop
    BRACKET = "BRACKET"  # Entry + SL + Target combined


class OrderStatus(Enum):
    """Order lifecycle states"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    EXECUTING = "EXECUTING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


# ============================================
# SIGNAL TYPES
# ============================================

class SignalType(Enum):
    """Trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"
    HOLD = "HOLD"
    NONE = "NONE"


class SignalStrength(Enum):
    """Signal confidence levels"""
    VERY_WEAK = (0, 20)
    WEAK = (20, 40)
    MODERATE = (40, 60)
    STRONG = (60, 80)
    VERY_STRONG = (80, 100)


# ============================================
# TIMEFRAMES
# ============================================

class Timeframe(Enum):
    """Supported timeframes for analysis"""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"


class TimeframeMinutes:
    """Timeframe to minutes conversion"""
    MAPPING: Final[dict] = {
        Timeframe.MINUTE_1: 1,
        Timeframe.MINUTE_5: 5,
        Timeframe.MINUTE_15: 15,
        Timeframe.HOUR_1: 60,
        Timeframe.DAILY: 1440,
        Timeframe.WEEKLY: 10080,
        Timeframe.MONTHLY: 43200,
    }


# ============================================
# STOP-LOSS TYPES
# ============================================

class StopLossType(Enum):
    """Stop-loss protection types"""
    FIXED = "FIXED"  # Static price level
    TRAILING = "TRAILING"  # Moves with profit
    PERCENTAGE = "PERCENTAGE"  # % from entry
    ATR = "ATR"  # Volatility-adjusted
    TIME_BASED = "TIME_BASED"  # Exit after time


# ============================================
# STRATEGIES
# ============================================

class StrategyName(Enum):
    """Available trading strategies"""
    TREND_RSI = "TREND_RSI"
    MEAN_REVERSION = "MEAN_REVERSION"
    BREAKOUT = "BREAKOUT"
    MOMENTUM = "MOMENTUM"
    INTRADAY_SHORT = "INTRADAY_SHORT"
    MULTI_TIMEFRAME = "MULTI_TIMEFRAME"
    OPTIONS_DIRECTIONAL = "OPTIONS_DIRECTIONAL"
    COVERED_CALL = "COVERED_CALL"


# ============================================
# MARKET SEGMENTS
# ============================================

class Exchange(Enum):
    """Indian stock exchanges"""
    NSE = "NSE"  # National Stock Exchange
    BSE = "BSE"  # Bombay Stock Exchange


class Segment(Enum):
    """Market segments"""
    EQUITY = "EQUITY"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"
    CURRENCY = "CURRENCY"


class OptionType(Enum):
    """Options contract types"""
    CALL = "CE"  # Call Option
    PUT = "PE"  # Put Option


# ============================================
# RISK LIMITS (Default Values)
# ============================================

class RiskDefaults:
    """Default risk management parameters"""
    # Capital limits
    INITIAL_CAPITAL: Final[float] = 50000.0  # ₹50,000
    MAX_POSITION_PERCENT: Final[float] = 20.0  # 20% per position
    MAX_DEPLOYED_PERCENT: Final[float] = 80.0  # 80% total deployed
    CASH_BUFFER_PERCENT: Final[float] = 20.0  # 20% cash reserve

    # Position limits
    MAX_SWING_POSITIONS: Final[int] = 4
    MAX_INTRADAY_POSITIONS: Final[int] = 2
    MAX_OPTIONS_POSITIONS: Final[int] = 2
    MAX_SECTOR_POSITIONS: Final[int] = 2
    MIN_SECTORS: Final[int] = 2

    # Loss limits
    RISK_PER_TRADE_PERCENT: Final[float] = 1.0  # 1% per trade
    MAX_DAILY_LOSS_PERCENT: Final[float] = 3.0  # 3% daily
    MAX_WEEKLY_LOSS_PERCENT: Final[float] = 6.0  # 6% weekly
    MAX_MONTHLY_DRAWDOWN_PERCENT: Final[float] = 10.0  # 10% monthly
    MAX_INTRADAY_LOSS_PERCENT: Final[float] = 2.0  # 2% intraday

    # Options limits
    MAX_OPTIONS_CAPITAL_PERCENT: Final[float] = 20.0  # 20% for options
    MAX_OPTION_PREMIUM: Final[float] = 5000.0  # ₹5,000 max premium
    MIN_DAYS_TO_EXPIRY: Final[int] = 7
    OPTIONS_STOP_LOSS_PERCENT: Final[float] = 45.0  # 45% of premium

    # Risk-reward
    MIN_RISK_REWARD_RATIO: Final[float] = 2.0  # Minimum 2:1

    # Leverage
    MAX_INTRADAY_LEVERAGE: Final[float] = 3.0  # 3x max


# ============================================
# TECHNICAL INDICATORS
# ============================================

class IndicatorDefaults:
    """Default parameters for technical indicators"""
    # Moving Averages
    SMA_SHORT: Final[int] = 20
    SMA_MEDIUM: Final[int] = 50
    SMA_LONG: Final[int] = 200
    EMA_SHORT: Final[int] = 12
    EMA_LONG: Final[int] = 26

    # RSI
    RSI_PERIOD: Final[int] = 14
    RSI_OVERBOUGHT: Final[float] = 70.0
    RSI_OVERSOLD: Final[float] = 30.0

    # MACD
    MACD_FAST: Final[int] = 12
    MACD_SLOW: Final[int] = 26
    MACD_SIGNAL: Final[int] = 9

    # Bollinger Bands
    BB_PERIOD: Final[int] = 20
    BB_STD: Final[float] = 2.0

    # ATR
    ATR_PERIOD: Final[int] = 14

    # Stochastic
    STOCH_K: Final[int] = 14
    STOCH_D: Final[int] = 3
    STOCH_SMOOTH: Final[int] = 3

    # ADX
    ADX_PERIOD: Final[int] = 14
    ADX_STRONG_TREND: Final[float] = 25.0


# ============================================
# DATA SOURCES
# ============================================

class DataSource(Enum):
    """Available data providers"""
    YFINANCE = "yfinance"  # Yahoo Finance (free)
    NSEPY = "nsetools"  # NSE Python (free)
    ALPHA_VANTAGE = "alpha_vantage"  # Alpha Vantage (free tier)
    BROKER_API = "broker_api"  # Live broker feed


class BrokerType(Enum):
    """Supported brokers"""
    ZERODHA = "zerodha"
    UPSTOX = "upstox"
    FYERS = "fyers"
    PAPER = "paper"  # Paper trading (simulation)


# ============================================
# FILE PATHS
# ============================================

class FilePaths:
    """Standard file paths"""
    DATA_DIR: Final[str] = "data"
    LOGS_DIR: Final[str] = "logs"
    CONFIG_DIR: Final[str] = "config"
    CACHE_DIR: Final[str] = "cache"
    REPORTS_DIR: Final[str] = "reports"
    BACKTEST_DIR: Final[str] = "backtest"


# ============================================
# LOGGING
# ============================================

class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================
# ENVIRONMENTS
# ============================================

class Environment(Enum):
    """System environments"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


# ============================================
# MARKET DATA
# ============================================

class MarketIndices:
    """Major Indian market indices"""
    NIFTY_50: Final[str] = "^NSEI"
    NIFTY_BANK: Final[str] = "^NSEBANK"
    NIFTY_IT: Final[str] = "NIFTY_IT.NS"
    SENSEX: Final[str] = "^BSESN"


class SectorCodes:
    """NSE sector classifications"""
    IT = "IT"
    BANKING = "BANKING"
    PHARMA = "PHARMA"
    AUTO = "AUTO"
    FMCG = "FMCG"
    METALS = "METALS"
    ENERGY = "ENERGY"
    REALTY = "REALTY"
    TELECOM = "TELECOM"
    INFRA = "INFRA"


# ============================================
# TRANSACTION COSTS
# ============================================

class TransactionCosts:
    """Brokerage and charges (Discount broker)"""
    BROKERAGE_FLAT: Final[float] = 20.0  # ₹20 per order
    BROKERAGE_PERCENT: Final[float] = 0.03  # 0.03% (whichever lower)
    STT_DELIVERY: Final[float] = 0.1  # 0.1% on sell side
    STT_INTRADAY: Final[float] = 0.025  # 0.025% on sell side
    EXCHANGE_CHARGES: Final[float] = 0.00325  # ~0.00325%
    GST: Final[float] = 18.0  # 18% on brokerage + transaction charges
    SEBI_CHARGES: Final[float] = 0.0001  # ₹10 per crore
    STAMP_DUTY: Final[float] = 0.015  # 0.015% on buy side

    # Options
    OPTIONS_BROKERAGE_FLAT: Final[float] = 20.0  # ₹20 per order
    OPTIONS_STT: Final[float] = 0.05  # 0.05% on sell side (premium)


# ============================================
# VALIDATION CONSTRAINTS
# ============================================

class ValidationLimits:
    """Validation boundaries"""
    MIN_STOCK_PRICE: Final[float] = 10.0
    MAX_STOCK_PRICE: Final[float] = 100000.0
    MIN_QUANTITY: Final[int] = 1
    MAX_QUANTITY: Final[int] = 100000
    MIN_SIGNAL_STRENGTH: Final[float] = 0.0
    MAX_SIGNAL_STRENGTH: Final[float] = 100.0
    MAX_SLIPPAGE_PERCENT: Final[float] = 1.0  # 1% max slippage


# ============================================
# SYSTEM SETTINGS
# ============================================

class SystemDefaults:
    """System-wide defaults"""
    PRICE_UPDATE_INTERVAL: Final[int] = 5  # seconds
    DATABASE_TIMEOUT: Final[int] = 30  # seconds
    API_RETRY_ATTEMPTS: Final[int] = 3
    API_RETRY_DELAY: Final[int] = 2  # seconds
    MAX_CACHE_AGE: Final[int] = 300  # 5 minutes
    BACKTEST_START_DATE: Final[str] = "2022-01-01"

    # Performance
    MAX_CONCURRENT_REQUESTS: Final[int] = 10
    REQUEST_TIMEOUT: Final[int] = 30

    # Monitoring
    HEALTH_CHECK_INTERVAL: Final[int] = 60  # seconds
    ALERT_COOLDOWN: Final[int] = 300  # 5 minutes between similar alerts


# ============================================
# NOTIFICATION TYPES
# ============================================

class NotificationType(Enum):
    """Alert notification types"""
    TRADE_EXECUTED = "trade_executed"
    STOP_LOSS_HIT = "stop_loss_hit"
    TARGET_REACHED = "target_reached"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    SYSTEM_ERROR = "system_error"
    DAILY_REPORT = "daily_report"
    SIGNAL_GENERATED = "signal_generated"
