"""
Logging System
Centralized logging with file rotation, structured logging, and performance tracking

Patterns:
- Singleton Pattern: Single logger instance
- Factory Pattern: Logger creation
- Decorator Pattern: Performance tracking
- Strategy Pattern: Different log formatters
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
import threading
import time


# ============================================
# CUSTOM LOG LEVELS
# ============================================

# Add custom log levels
PERFORMANCE = 25  # Between INFO and WARNING
logging.addLevelName(PERFORMANCE, "PERFORMANCE")

TRADE = 35  # Between WARNING and ERROR
logging.addLevelName(TRADE, "TRADE")


# ============================================
# STRUCTURED LOG FORMATTER
# ============================================

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging

    Pattern: Strategy Pattern for formatting
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter

    Pattern: Strategy Pattern for formatting
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'PERFORMANCE': '\033[35m', # Magenta
        'WARNING': '\033[33m',    # Yellow
        'TRADE': '\033[1;34m',    # Bold Blue
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[1;31m', # Bold Red
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ============================================
# TRADING LOGGER (Main Logger Class)
# ============================================

class TradingLogger:
    """
    Main logging class for trading system

    Pattern: Singleton Pattern
    - Single logger instance across application
    - Thread-safe initialization
    - Centralized configuration
    """

    _instance: Optional['TradingLogger'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls):
        """Thread-safe singleton implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize logger (only once)"""
        if self._initialized:
            return

        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._log_dir = Path("logs")
        self._log_dir.mkdir(exist_ok=True)

        # Performance tracking
        self._performance_metrics: Dict[str, list] = {}
        self._metrics_lock = threading.Lock()

        # Initialize root logger
        self._setup_root_logger()

    def _setup_root_logger(self):
        """Setup root logger with handlers"""
        root_logger = logging.getLogger('trading')
        root_logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Console handler (colored)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # Main file handler (rotating)
        main_file_handler = logging.handlers.RotatingFileHandler(
            filename=self._log_dir / 'trading.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        main_file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-11s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        main_file_handler.setFormatter(file_formatter)
        root_logger.addHandler(main_file_handler)

        # Error file handler (errors only)
        error_file_handler = logging.handlers.RotatingFileHandler(
            filename=self._log_dir / 'errors.log',
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_file_handler)

        # Trade file handler (trade logs only)
        trade_file_handler = logging.handlers.RotatingFileHandler(
            filename=self._log_dir / 'trades.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10,
            encoding='utf-8'
        )
        trade_file_handler.setLevel(TRADE)
        trade_file_handler.addFilter(lambda record: record.levelno == TRADE)
        trade_file_handler.setFormatter(file_formatter)
        root_logger.addHandler(trade_file_handler)

        # Structured JSON handler (for log analysis)
        json_handler = logging.handlers.RotatingFileHandler(
            filename=self._log_dir / 'trading.json',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=3,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(json_handler)

        # Prevent propagation to root
        root_logger.propagate = False

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create logger for specific module

        Args:
            name: Logger name (usually module name)

        Returns:
            Logger instance
        """
        if name not in self._loggers:
            logger = logging.getLogger(f'trading.{name}')
            self._loggers[name] = logger

        return self._loggers[name]

    def performance(self, logger_name: str, message: str, **kwargs):
        """Log performance metrics"""
        logger = self.get_logger(logger_name)
        logger.log(PERFORMANCE, message, **kwargs)

    def trade(self, logger_name: str, message: str, **kwargs):
        """Log trade events"""
        logger = self.get_logger(logger_name)
        logger.log(TRADE, message, **kwargs)

    def track_performance(self, name: str, duration_ms: float, **metadata):
        """
        Track performance metrics

        Args:
            name: Metric name
            duration_ms: Duration in milliseconds
            metadata: Additional metadata
        """
        with self._metrics_lock:
            if name not in self._performance_metrics:
                self._performance_metrics[name] = []

            metric = {
                'timestamp': datetime.now(),
                'duration_ms': duration_ms,
                **metadata
            }
            self._performance_metrics[name].append(metric)

            # Keep only last 1000 entries per metric
            if len(self._performance_metrics[name]) > 1000:
                self._performance_metrics[name] = self._performance_metrics[name][-1000:]

    def get_performance_stats(self, name: str) -> Dict[str, Any]:
        """
        Get performance statistics for a metric

        Args:
            name: Metric name

        Returns:
            Statistics dictionary
        """
        with self._metrics_lock:
            if name not in self._performance_metrics or not self._performance_metrics[name]:
                return {}

            durations = [m['duration_ms'] for m in self._performance_metrics[name]]

            return {
                'count': len(durations),
                'avg_ms': sum(durations) / len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'total_ms': sum(durations)
            }

    def set_level(self, level: str):
        """
        Set logging level

        Args:
            level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger('trading').setLevel(numeric_level)

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)"""
        with cls._lock:
            cls._instance = None


# ============================================
# PERFORMANCE TRACKING DECORATOR
# ============================================

def log_performance(func: Callable) -> Callable:
    """
    Decorator to track function performance

    Pattern: Decorator Pattern
    - Wraps function to track execution time
    - Logs performance metrics
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger_instance = get_logger(func.__module__)

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            logger_instance.debug(
                f"{func.__name__} completed in {duration_ms:.2f}ms"
            )

            # Track in global metrics
            trading_logger = TradingLogger()
            trading_logger.track_performance(
                f"{func.__module__}.{func.__name__}",
                duration_ms
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger_instance.error(
                f"{func.__name__} failed after {duration_ms:.2f}ms: {e}"
            )
            raise

    return wrapper


def log_method(level: str = 'DEBUG'):
    """
    Decorator to log method calls

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Pattern: Decorator Pattern with parameters
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)

            # Log entry
            logger.log(
                getattr(logging, level.upper()),
                f"Calling {func.__name__} with args={args[1:] if args else ()}, kwargs={kwargs}"
            )

            result = func(*args, **kwargs)

            # Log exit
            logger.log(
                getattr(logging, level.upper()),
                f"{func.__name__} returned: {type(result).__name__}"
            )

            return result

        return wrapper
    return decorator


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

# Global logger instance
_global_logger: Optional[TradingLogger] = None


def get_trading_logger() -> TradingLogger:
    """Get global trading logger instance"""
    global _global_logger

    if _global_logger is None:
        _global_logger = TradingLogger()

    return _global_logger


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get logger

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    trading_logger = get_trading_logger()
    return trading_logger.get_logger(name)


def log_trade(symbol: str, action: str, quantity: int, price: float, **kwargs):
    """
    Convenience function to log trades

    Args:
        symbol: Stock symbol
        action: BUY/SELL/SHORT/COVER
        quantity: Number of shares
        price: Execution price
        kwargs: Additional metadata
    """
    logger = get_logger('trades')

    message = f"TRADE | {action} {quantity} {symbol} @ ₹{price:.2f}"

    if kwargs:
        metadata_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        message += f" | {metadata_str}"

    logger.log(TRADE, message)


def log_signal(symbol: str, signal_type: str, strength: float, **kwargs):
    """
    Convenience function to log trading signals

    Args:
        symbol: Stock symbol
        signal_type: BUY/SELL/HOLD
        strength: Signal strength (0-100)
        kwargs: Additional metadata
    """
    logger = get_logger('signals')

    message = f"SIGNAL | {symbol} | {signal_type} | Strength: {strength:.1f}"

    if kwargs:
        metadata_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        message += f" | {metadata_str}"

    logger.info(message)


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == '__main__':
    # Get logger for this module
    logger = get_logger(__name__)

    # Different log levels
    logger.debug("This is a debug message")
    logger.info("System initialized successfully")
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Performance log
    trading_logger = get_trading_logger()
    trading_logger.performance(__name__, "Data fetch completed in 150ms")

    # Trade log
    log_trade("RELIANCE.NS", "BUY", 10, 2450.50, strategy="TREND_RSI", reason="RSI oversold")

    # Signal log
    log_signal("TCS.NS", "SELL", 75.0, indicator="RSI", value=72.5)

    # Performance tracking
    @log_performance
    def expensive_function():
        time.sleep(0.1)
        return "done"

    expensive_function()

    # Get performance stats
    stats = trading_logger.get_performance_stats(f"{__name__}.expensive_function")
    print(f"Performance stats: {stats}")
